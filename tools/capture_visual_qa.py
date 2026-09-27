"""Render app pages and capture their native Windows surfaces for visual QA."""

from __future__ import annotations

import ctypes
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sim_controls_manager.gui import SimControlsApp
from sim_controls_manager import deck_layout, simhub, ui_dialogs
from sim_controls_manager.adapters import iracing
from sim_controls_manager.catalog import ACTIONS
from sim_controls_manager.file_change import apply_file_change, plan_file_change
from sim_controls_manager.recovery_history import discover_history


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

    def _backup_root(self):
        return self.qa_root / "backups"

    def preview_bindings(self, quiet=False):
        if self.discovery and self.simhub_inspection:
            profile = self._selected_profile()
            self._preview_complete((iracing.inspect_profile(profile), iracing.plan_bindings(profile, self._catalog()), "iracing"))


def capture_window(window: SimControlsApp, destination: Path) -> None:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    # HWND and GDI handles are pointer-sized on 64-bit Windows.
    for function, arguments, result in (
        (user32.GetParent, [ctypes.c_void_p], ctypes.c_void_p),
        (user32.GetWindowDC, [ctypes.c_void_p], ctypes.c_void_p),
        (user32.GetWindowRect, [ctypes.c_void_p, ctypes.POINTER(Rect)], ctypes.c_int),
        (user32.PrintWindow, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
        (user32.ReleaseDC, [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        (gdi32.CreateCompatibleDC, [ctypes.c_void_p], ctypes.c_void_p),
        (gdi32.CreateCompatibleBitmap, [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_void_p),
        (gdi32.SelectObject, [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_void_p),
        (gdi32.DeleteObject, [ctypes.c_void_p], ctypes.c_int),
        (gdi32.DeleteDC, [ctypes.c_void_p], ctypes.c_int),
        (gdi32.GetDIBits, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
        (gdi32.BitBlt, [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint], ctypes.c_int),
    ):
        function.argtypes, function.restype = arguments, result
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

        raw = pixels.raw
        rows = []
        for y in reversed(range(height)):
            source = raw[y*width*4:(y+1)*width*4]
            rgb = bytearray(width*3)
            rgb[0::3], rgb[1::3], rgb[2::3] = source[2::4], source[1::4], source[0::4]
            rows.append(b"\0" + rgb)
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data))
        destination.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)


def populate(app, root):
    """Synthetic files exercise the real parsers/planner and backup verification."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from test_iracing_adapter import synthetic_controls
    profile_dir = root / "iRacing" / "profiles" / "controls" / "Road"
    profile_dir.mkdir(parents=True)
    (profile_dir / "controls.cfg").write_bytes(synthetic_controls())
    (root / "iRacing" / "app.ini").write_text("[ControlProfiles]\nGlobal=Road\n")
    app.discovery = iracing.discover(root / "iRacing")
    app.iracing_root.set(str(root / "iRacing"))
    app.devices = (iracing.DeviceInfo("D94DE5E0-6276-11F1-8001-444553540000", "040DC24F-0076-0000-0000-504944564944", "SimHub virtual output"),)
    app.device_combo.configure(values=(app.devices[0].name,))
    app.device_name.set(app.devices[0].name)
    app.simhub_inspection = simhub.SimHubInspection(root / "SimHub" / "settings.json", 1, 1,
        tuple(simhub.SimHubBinding(action, role, number) for action, role, number in (
            ("pit_limiter", "PitLimiter", 20), ("tc_increase", "TractionControl+", 8), ("tc_decrease", "TractionControl-", 9))), ())
    app._update_profile_choices()
    app._refresh_binding_rows()
    app.preview_bindings()
    app.preview_summary.set("Profile and controller detected · 3 supported roles")
    app._set_status_card("iracing", "Connected", "1 profile · Road is active", True)
    app._set_status_card("simhub", "Connected", "3 of 3 roles mapped · vJoy output", True)
    app._set_status_card("device", "Connected", app.devices[0].name, True)
    for key, title in (("assetto_corsa", "Assetto Corsa"), ("acc", "ACC"), ("assetto_corsa_evo", "Assetto Corsa EVO"), ("lmu", "Le Mans Ultimate")):
        app._set_status_card(key, "Not found", "Choose the simulator folder in Source locations", False)
    app._set_status_card("automobilista_2", "Discovery only", "Encrypted profiles are read-only", False)
    app.last_refreshed.set("Updated just now · Visual QA fixture · No real simulator files used")
    for index, (directory, filename) in enumerate((("ACC/Config", "controls.json"), ("Assetto Corsa/cfg", "controls.ini"), ("iRacing/profiles/controls/Endurance", "controls.cfg"))):
        target = root / directory / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"original fixture")
        result = apply_file_change(plan_file_change(target, b"applied fixture"), root / "backups" / str(index), now=lambda i=index: datetime(2026, 9, 27-i, 15, 30, tzinfo=timezone.utc))
        if index == 1:
            target.write_bytes(b"changed after apply")
        if index == 2:
            Path(result.receipt.backupPath).write_bytes(b"damaged backup fixture")
    app._history_loaded(discover_history(root / "backups"), "")
    app.receipt_path.set(str(app._history_entries[0].path))
    app._inspect_receipt()
    app._refresh_workspace_status()


def main() -> None:
    output = Path("build/visual-qa-captures")
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="visual-qa-", dir="build") as temporary:
        root = Path(temporary).resolve()
        VisualQaApp.qa_root = root
        with patch.object(deck_layout, "default_layout_path", return_value=root / "deck.json"):
            app = VisualQaApp()
        app.auto_refresh.set(False)
        errors = []
        app.report_callback_exception = lambda kind, error, traceback: errors.append(f"{kind.__name__}: {error}")
        def render(page, name, geometry="1440x880"):
            app.geometry(geometry)
            app.show_page(page)
            app.update_idletasks()
            app.update()
            app._enable_dark_title_bar()
            capture_window(app, output / f"{name}.png")
        def exercise():
            try:
                render("recovery", "recovery-empty")
                populate(app, root)
                for geometry, suffix in (("1440x880", "wide"), ("1100x700", "compact")):
                    for page, name in (("dashboard", "overview"), ("controls", "deck"), ("control_map", "control-map"), ("bindings", "bindings"), ("recovery", "recovery")):
                        render(page, f"{name}-{suffix}", geometry)
                        if page == "bindings":
                            for button in (app.apply_button, app.apply_all_button, app.copy_iracing_button):
                                assert button.winfo_viewable(), f"Hidden action: {button.cget('text')}"
                                assert button.winfo_rooty()+button.winfo_height() <= app.winfo_rooty()+app.winfo_height()
                app.active_ack.set(True)
                app._update_apply_state()
                assert str(app.apply_button.cget("state")) == "normal"
                app._invalidate_preview()
                assert str(app.apply_button.cget("state")) == "disabled"
                app.preview_bindings()
                render("bindings", "bindings-ready")
                app.control_search.set("TractionControlInc")
                app._filter_control_names()
                assert "tc_increase" in app.control_tree.get_children()
                render("control_map", "control-map-filtered")
                app.control_search.set("no-matching-control-xyz")
                app._filter_control_names()
                assert not app.control_tree.get_children()
                render("control_map", "control-map-empty")
                app._clear_control_search()
                app.control_column_visibility["iracing"].set(False)
                app._update_control_columns()
                assert "iracing" not in app.control_mapping_tree.cget("displaycolumns")
                app.control_column_visibility["iracing"].set(True)
                app._update_control_columns()
                app.show_page("controls")
                original = app.deck_selected_index
                app._deck_keyboard(SimpleNamespace(keysym="Right"))
                assert app.deck_selected_index == original+1
                app.deck_label.set("QA ignition")
                app._apply_deck_tile()
                app._save_deck_layout()
                assert deck_layout.load_layout(root / "deck.json").active_page().tiles[1].label == "QA ignition"
                app.deck_inspector_tabs.select(1)
                render("controls", "deck-shortcuts")
                for entry in app._history_entries:
                    app.receipt_path.set(str(entry.path))
                    app._inspect_receipt()
                    assert str(app.restore_button.cget("state")) == ("normal" if entry.status == "ready" else "disabled")
                    render("recovery", f"recovery-{entry.status}")
                app.history_filter.set("ACC")
                app._populate_history()
                assert len(app.history_tree.get_children()) == 1
                app.receipt_path.set("not-a-receipt")
                assert str(app.restore_button.cget("state")) == "disabled"
                app.after(150, lambda: (capture_window(app._active_dialog, output / "confirmation-dialog.png"), app._active_dialog.event_generate("<Escape>")))
                accepted = ui_dialogs.askyesno("Apply previewed bindings?", "Apply 3 binding changes to Road?\n\nA verified backup and restore receipt will be created first. iRacing must be closed.", parent=app, icon="warning")
                assert accepted is False
                assert not errors, errors
                print("Native QA passed: all 5 pages at 1440x880 and 1100x700; filters, preview gating, deck edit/save, recovery integrity, and dialog cancellation.")
            except Exception as exc:
                errors.append(repr(exc))
            finally:
                app._close()
        app.after(250, exercise)
        app.mainloop()
        if errors:
            raise AssertionError(errors)


if __name__ == "__main__":
    main()
