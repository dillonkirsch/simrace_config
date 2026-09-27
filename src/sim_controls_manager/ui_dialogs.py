"""Consistent, keyboard-accessible dialogs over native Tk windows."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from sim_controls_manager.ui_theme import COLORS, TYPE, dark_caption, label


def _dialog(title, message, *, parent=None, confirm=False, prompt=False,
            initialvalue="", icon="info", **_options):
    parent = parent or tk._default_root
    window = tk.Toplevel(parent)
    window.withdraw()
    window.title(title)
    window.configure(bg=COLORS["surface"], padx=22, pady=20)
    window.transient(parent)
    window.minsize(460, 210)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)
    parent._active_dialog = window
    result = [None if prompt else False]
    old_focus = parent.focus_get()
    label(window, title, kind="section", tone="warning" if icon == "warning" else ("danger" if icon == "error" else "text"), wrap=580).grid(row=0, column=0, sticky="ew", pady=(0, 16))
    body = tk.Frame(window, bg=COLORS["surface"])
    body.grid(row=1, column=0, sticky="nsew")
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)
    lines = min(18, max(3, len(str(message))//78 + str(message).count("\n") + 2))
    text = tk.Text(body, width=72, height=lines, wrap="word", bg=COLORS["surface"],
                   fg=COLORS["muted"], bd=0, highlightthickness=0,
                   font=TYPE["body"], padx=0, pady=0, spacing3=5,
                   selectbackground=COLORS["selection_key"], cursor="arrow")
    text.insert("1.0", message)
    text.configure(state="disabled")
    text.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(body, command=text.yview, style="Slim.Vertical.TScrollbar")
    scroll.grid(row=0, column=1, sticky="ns")
    text.configure(yscrollcommand=scroll.set)
    value = tk.StringVar(value=initialvalue)
    entry = None
    if prompt:
        entry = ttk.Entry(window, textvariable=value)
        entry.grid(row=2, column=0, sticky="ew", pady=(10, 14))
        entry.selection_range(0, "end")

    def finish(accepted):
        result[0] = value.get() if prompt and accepted else (None if prompt else accepted)
        window.grab_release()
        window.destroy()
        parent._active_dialog = None
        if old_focus and old_focus.winfo_exists():
            old_focus.focus_set()

    actions = tk.Frame(window, bg=COLORS["surface"])
    actions.grid(row=3, column=0, sticky="ew", pady=(20, 0))
    accept = parent._button(actions, "Continue" if confirm else ("Save" if prompt else "Done"), lambda: finish(True), primary=icon != "warning", danger=icon == "warning")
    accept.pack(side="right")
    if confirm or prompt:
        cancel = parent._button(actions, "Cancel", lambda: finish(False))
        cancel.pack(side="right", padx=(0, 8))
        cancel.bind("<Return>", lambda e: finish(False))
    accept.bind("<Return>", lambda e: finish(True))
    if entry:
        entry.bind("<Return>", lambda e: finish(True))
    window.bind("<Escape>", lambda e: finish(False))
    window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    window.update_idletasks()
    width, height = max(560, window.winfo_reqwidth()), min(parent.winfo_screenheight()-100, window.winfo_reqheight())
    x = max(0, parent.winfo_rootx()+(parent.winfo_width()-width)//2)
    y = max(0, parent.winfo_rooty()+(parent.winfo_height()-height)//2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.deiconify()
    dark_caption(window)
    window.wait_visibility()
    window.grab_set()
    (entry if prompt else (cancel if confirm else accept)).focus_set()
    parent.wait_window(window)
    return result[0]


def showinfo(title, message, **options):
    return _dialog(title, message, **options)


def showwarning(title, message, **options):
    return _dialog(title, message, icon="warning", **options)


def showerror(title, message, **options):
    return _dialog(title, message, icon="error", **options)


def askyesno(title, message, **options):
    return _dialog(title, message, confirm=True, **options)


def askstring(title, prompt, **options):
    return _dialog(title, prompt, prompt=True, **options)
