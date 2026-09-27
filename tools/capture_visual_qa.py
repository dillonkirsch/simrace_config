"""Render app pages and capture their native Windows surfaces for visual QA."""

from __future__ import annotations

import ctypes
import struct
from pathlib import Path

from sim_controls_manager.gui import SimControlsApp


SRCCOPY = 0x00CC0020
BI_RGB = 0
DIB_RGB_COLORS = 0


class Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class BitmapInfo(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BitmapInfoHeader),
        ("bmiColors", ctypes.c_uint32 * 3),
    ]


class VisualQaApp(SimControlsApp):
    """Keep capture fixtures deterministic and free of background discovery."""

    def scan_setup(self, automatic: bool = False) -> None:
        return None

    def _schedule_watch(self) -> None:
        return None


def capture_window(window: SimControlsApp, destination: Path) -> None:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
    rect = Rect()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise OSError("Could not read the application window bounds")
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    window_dc = user32.GetWindowDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    previous = gdi32.SelectObject(memory_dc, bitmap)
    try:
        printed = user32.PrintWindow(hwnd, memory_dc, 2)
        if not printed:
            gdi32.BitBlt(memory_dc, 0, 0, width, height, window_dc, 0, 0, SRCCOPY)

        info = BitmapInfo()
        info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = BI_RGB
        image_size = width * height * 4
        info.bmiHeader.biSizeImage = image_size
        pixels = ctypes.create_string_buffer(image_size)
        if not gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            height,
            pixels,
            ctypes.byref(info),
            DIB_RGB_COLORS,
        ):
            raise OSError("Could not read the rendered application pixels")

        pixel_offset = 14 + ctypes.sizeof(BitmapInfoHeader)
        file_size = pixel_offset + image_size
        file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)
        destination.write_bytes(
            file_header
            + bytes(info.bmiHeader)
            + pixels.raw
        )
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)


def main() -> None:
    output = Path("build/visual-qa-captures")
    output.mkdir(parents=True, exist_ok=True)
    app = VisualQaApp()
    app.auto_refresh.set(False)
    app.update_idletasks()
    app.update()

    captures = (
        ("dashboard", "overview-wide", "1440x880"),
        ("controls", "deck-wide", "1440x880"),
        ("control_map", "control-map-wide", "1600x900"),
        ("bindings", "bindings-wide", "1440x880"),
        ("recovery", "recovery-wide", "1440x880"),
        ("dashboard", "overview-compact", "1100x700"),
        ("controls", "deck-compact", "1100x700"),
        ("bindings", "bindings-compact", "1100x700"),
    )
    try:
        for page, name, geometry in captures:
            app.geometry(geometry)
            app.show_page(page)
            app.update_idletasks()
            app.update()
            capture_window(app, output / f"{name}.bmp")
    finally:
        app._close()


if __name__ == "__main__":
    main()
