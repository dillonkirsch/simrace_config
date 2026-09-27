"""Shared desktop design tokens and small, toolkit-native presentation helpers."""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from tkinter import ttk

COLORS = {
    "canvas": "#191B20", "sidebar": "#202229", "workspace": "#262930",
    "surface": "#2E323B", "surface_alt": "#292D35", "raised": "#393E49",
    "hover": "#424956", "header": "#343943", "selection": "#354865",
    "selection_key": "#344C70", "border": "#474E5B", "line": "#3A404B",
    "text": "#F1F3F7", "muted": "#B8C0CE", "subtle": "#929DAC",
    "accent": "#75D6AD", "accent_soft": "#2C443E", "primary": "#4779DC",
    "primary_hover": "#86AEFF", "primary_pressed": "#3965BA",
    "warning": "#EAC17D", "danger": "#F38F99", "danger_soft": "#50353E",
}
FONT_TEXT = "Segoe UI"
FONT_DISPLAY = "Segoe UI Variable Display"
FONT_ICON = "Segoe Fluent Icons"
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
TYPE = {
    "title": (FONT_DISPLAY, -25, "bold"),
    "section": (FONT_TEXT, -15, "bold"),
    "body": (FONT_TEXT, -13), "secondary": (FONT_TEXT, -12),
    "label": (FONT_TEXT, -12, "bold"), "metadata": (FONT_TEXT, -11),
    "mono": ("Cascadia Mono", -12),
}


def dark_caption(window: tk.Toplevel) -> None:
    """Color the real DWM caption; keep Windows sizing and system controls."""
    if sys.platform != "win32":
        return
    try:
        user = ctypes.windll.user32
        user.GetParent.argtypes = [ctypes.c_void_p]
        user.GetParent.restype = ctypes.c_void_p
        hwnd = user.GetParent(window.winfo_id()) or window.winfo_id()
        setter = ctypes.windll.dwmapi.DwmSetWindowAttribute
        setter.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        for attr, value in ((20, 1), (19, 1), (35, 0x292220), (36, 0xF7F3F1)):
            number = ctypes.c_int(value)
            setter(hwnd, attr, ctypes.byref(number), ctypes.sizeof(number))
    except (AttributeError, OSError, tk.TclError):
        pass


def label(parent, text="", *, variable=None, tone="text", kind="body", wrap=0):
    """A label that inherits its surface and can wrap with its container."""
    try:
        background = parent.cget("background")
    except tk.TclError:
        background = ttk.Style(parent).lookup(parent.cget("style") or "TFrame", "background")
    options = {"textvariable": variable} if variable is not None else {"text": text}
    widget = tk.Label(parent, **options, bg=background, fg=COLORS[tone],
                      font=TYPE[kind], anchor="w", justify="left", bd=0,
                      wraplength=wrap)
    if wrap:
        widget.bind("<Configure>", lambda e: widget.configure(wraplength=max(80, e.width)))
    return widget


def panel(parent, *, padding=16, tone="surface"):
    return tk.Frame(parent, bg=COLORS[tone], padx=padding, pady=padding,
                    highlightthickness=1, highlightbackground=COLORS["line"], bd=0)


def divider(parent):
    tk.Frame(parent, bg=COLORS["line"], height=1).pack(fill="x", pady=12)


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.job, self.window = widget, text, None, None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")
        widget.bind("<FocusIn>", self.schedule, add="+")
        widget.bind("<FocusOut>", self.hide, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    def schedule(self, _event=None):
        self.hide()
        self.job = self.widget.after(650, self.show)

    def show(self):
        self.job = None
        if not self.widget.winfo_viewable():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.configure(bg=COLORS["raised"])
        label(self.window, self.text).pack(padx=10, pady=7)
        self.window.geometry(f"+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty()+self.widget.winfo_height()+6}")

    def hide(self, _event=None):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.window:
            self.window.destroy()
            self.window = None


class ScrollFrame(tk.Frame):
    """A viewport for inspectors and forms at smaller desktop sizes."""
    def __init__(self, parent, *, tone="workspace"):
        super().__init__(parent, bg=COLORS[tone], bd=0)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=COLORS[tone], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll = ttk.Scrollbar(self, command=self.canvas.yview, style="Slim.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.body = tk.Frame(self.canvas, bg=COLORS[tone])
        self.item = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.canvas.bind("<Configure>", self.resize)
        self.body.bind("<Configure>", self.resize)
        self.bind_all("<MouseWheel>", self.wheel, add="+")

    def resize(self, _event=None):
        height = max(self.canvas.winfo_height(), self.body.winfo_reqheight())
        self.canvas.itemconfigure(self.item, width=self.canvas.winfo_width(), height=height)
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), height))
        if height > self.canvas.winfo_height()+1:
            self.scroll.grid(row=0, column=1, sticky="ns")
        else:
            self.scroll.grid_remove()
            self.canvas.yview_moveto(0)

    def wheel(self, event):
        if str(event.widget).startswith(str(self) + ".") and self.scroll.winfo_ismapped():
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
            return "break"
