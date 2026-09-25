"""Modern, dependency-free Windows interface for Sim Controls Manager."""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, TypeVar

from sim_controls_manager import simhub, updater
from sim_controls_manager.adapters import iracing
from sim_controls_manager.catalog import ACTIONS, Catalog, validate_catalog
from sim_controls_manager.control_names import (
    CONTROLS,
    GAMES,
    NATIVE_CONTROL_NAMES,
    NativeControlName,
)
from sim_controls_manager.file_change import (
    FileChangeError,
    apply_file_change,
    plan_file_change,
    preview_restore,
    restore_file,
)

T = TypeVar("T")


COLORS = {
    "canvas": "#0A0F17",
    "sidebar": "#070B11",
    "surface": "#111A26",
    "raised": "#192536",
    "border": "#25344A",
    "text": "#F6F8FC",
    "muted": "#9AAAC0",
    "subtle": "#66788F",
    "accent": "#42D7B6",
    "accent_soft": "#143A35",
    "primary": "#4C84FF",
    "primary_hover": "#6B9AFF",
    "warning": "#F5B84B",
    "danger": "#F06D76",
}

AUTO_REFRESH_MS = 2500

ACTION_LABELS = {
    "pit_limiter": "Pit limiter",
    "tc_increase": "Traction control +",
    "tc_decrease": "Traction control −",
}


def _native_control_text(mapping: NativeControlName) -> str:
    """Format one crosswalk cell for the driver-facing control reference."""

    if mapping.status == "not_exposed":
        return "Not exposed"
    if mapping.status == "not_observed":
        return "Not observed"
    name = " / ".join(mapping.names)
    if mapping.status == "compound":
        return f"{name} (combined)"
    if mapping.status == "related":
        return f"{name} (related)"
    return name


def _matching_control_ids(query: str) -> tuple[str, ...]:
    """Return controls whose central or native names contain ``query``."""

    needle = query.strip().casefold()
    if not needle:
        return tuple(CONTROLS)
    matches = []
    for control_id, control in CONTROLS.items():
        terms = [control_id, control.label, control.kind]
        for game_id, game_name in GAMES.items():
            mapping = NATIVE_CONTROL_NAMES[game_id][control_id]
            terms.extend((game_name, mapping.status, *mapping.names))
        if any(needle in term.casefold() for term in terms):
            matches.append(control_id)
    return tuple(matches)


def _binding_text(binding: iracing.NativeBinding | None) -> str:
    if binding is None:
        return "Unavailable"
    if binding.binding_type == "button" and binding.native_button_index is not None:
        return f"Button {binding.native_button_index + 1}"
    return binding.binding_type.replace("_", " ").title()


def _backup_directory(profile_name: str) -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    safe_profile = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in profile_name
    )
    return base / "sim-controls-manager" / "backups" / "iracing" / safe_profile


def _validate_iracing_bytes(data: bytes) -> bool:
    return iracing.build_gfcc(iracing.parse_gfcc(data)) == data


def _path_signature(path: Path) -> tuple[str, int | None, int | None]:
    """Return a cheap, stable fingerprint for a watched file or directory."""

    try:
        stat = path.stat()
    except OSError:
        return str(path), None, None
    return str(path), stat.st_mtime_ns, stat.st_size


def _source_signature(
    iracing_root: Path | None,
    simhub_settings: Path | None,
    devices: tuple[iracing.DeviceInfo, ...],
) -> tuple:
    """Fingerprint every external input shown by the GUI without reading its contents."""

    paths: list[Path] = []
    if iracing_root is not None:
        paths.extend((iracing_root, iracing_root / "app.ini", iracing_root / "controls.cfg"))
        profile_root = iracing_root / iracing.PROFILE_DIRECTORY
        paths.append(profile_root)
        if profile_root.is_dir():
            try:
                paths.extend(
                    directory / "controls.cfg"
                    for directory in sorted(profile_root.iterdir(), key=lambda item: item.name.lower())
                    if directory.is_dir()
                )
            except OSError:
                pass
    if simhub_settings is not None:
        paths.append(simhub_settings)
    device_signature = tuple(
        sorted((device.instance_guid, device.product_guid, device.name) for device in devices)
    )
    return tuple(_path_signature(path) for path in paths), device_signature


class SimControlsApp(tk.Tk):
    """Single-window, preview-first desktop workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Sim Controls Manager")
        self.geometry("1220x790")
        self.minsize(1060, 700)
        self.configure(bg=COLORS["canvas"])
        self._set_icon()

        self.discovery: iracing.DiscoveryResult | None = None
        self.simhub_inspection: simhub.SimHubInspection | None = None
        self.devices: tuple[iracing.DeviceInfo, ...] = ()
        self.binding_plan: iracing.BindingPlan | None = None
        self.last_receipt: Path | None = None
        self.busy = False
        self._closing = False
        self._watch_in_progress = False
        self._source_state: tuple | None = None
        self._watch_after_id: str | None = None

        self.iracing_root = tk.StringVar()
        self.simhub_settings = tk.StringVar()
        self.profile_name = tk.StringVar()
        self.device_name = tk.StringVar()
        self.active_ack = tk.BooleanVar(value=False)
        self.auto_refresh = tk.BooleanVar(value=True)
        self.footer_status = tk.StringVar(value="Ready to scan your setup")
        self.preview_summary = tk.StringVar(value="Scan your setup to begin")
        self.last_refreshed = tk.StringVar(value="Starting live sync…")
        self.receipt_path = tk.StringVar()
        self.control_search = tk.StringVar()
        self.control_result_summary = tk.StringVar()
        self.control_detail = tk.StringVar(value="Select a control to see mapping notes.")

        self._configure_styles()
        self._build_shell()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(200, self.scan_setup)
        self._schedule_watch()

    def _set_icon(self) -> None:
        candidates = []
        if getattr(sys, "_MEIPASS", None):
            candidates.append(Path(sys._MEIPASS) / "sim-controls-manager.ico")
        candidates.append(
            Path(__file__).resolve().parents[2]
            / "packaging"
            / "assets"
            / "sim-controls-manager.ico"
        )
        for candidate in candidates:
            if candidate.is_file():
                try:
                    self.iconbitmap(default=str(candidate))
                except tk.TclError:
                    pass
                break

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["canvas"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
        style.configure(
            "TLabel",
            background=COLORS["canvas"],
            foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Surface.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Muted.Surface.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["canvas"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 24),
        )
        style.configure(
            "CardTitle.Surface.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Metric.Surface.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 16),
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["raised"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=8,
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["raised"],
            background=COLORS["raised"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["muted"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=7,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["raised"])],
            foreground=[("readonly", COLORS["text"])],
            selectbackground=[("readonly", COLORS["raised"])],
            selectforeground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "TCheckbutton",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["surface"])],
            foreground=[("active", COLORS["text"])],
        )
        style.configure(
            "Live.TCheckbutton",
            background=COLORS["canvas"],
            foreground=COLORS["muted"],
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Live.TCheckbutton",
            background=[("active", COLORS["canvas"])],
            foreground=[("active", COLORS["text"])],
        )
        style.configure(
            "Control.Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            rowheight=34,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Control.Treeview.Heading",
            background=COLORS["raised"],
            foreground=COLORS["muted"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            font=("Segoe UI Semibold", 9),
            padding=(8, 9),
        )
        style.map(
            "Control.Treeview",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", COLORS["text"])],
        )
        style.map(
            "Control.Treeview.Heading",
            background=[("active", COLORS["raised"])],
            foreground=[("active", COLORS["text"])],
        )

    def _build_shell(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=238)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        brand = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(28, 38))
        tk.Label(
            brand,
            text="S",
            bg=COLORS["primary"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 12),
            width=3,
            height=2,
        ).pack(side="left", padx=(0, 12))
        tk.Label(
            brand,
            text="SIM CONTROLS\nMANAGER",
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 9),
            justify="left",
        ).pack(side="left")

        self.nav_buttons: dict[str, tk.Button] = {}
        for index, (page, label) in enumerate(
            (
                ("dashboard", "  Overview"),
                ("controls", "  Control names"),
                ("bindings", "  Bindings"),
                ("recovery", "  Recovery"),
            ),
            start=1,
        ):
            button = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                command=lambda name=page: self.show_page(name),
                bg=COLORS["sidebar"],
                fg=COLORS["muted"],
                activebackground=COLORS["raised"],
                activeforeground=COLORS["text"],
                relief="flat",
                bd=0,
                padx=18,
                pady=14,
                font=("Segoe UI Semibold", 10),
                cursor="hand2",
            )
            button.grid(row=index, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[page] = button

        version = updater.current_version()
        sidebar_footer = tk.Frame(sidebar, bg=COLORS["sidebar"])
        sidebar_footer.grid(row=6, column=0, sticky="sew", padx=22, pady=22)
        tk.Label(
            sidebar_footer,
            text="●  LIVE CONFIG SYNC",
            bg=COLORS["sidebar"],
            fg=COLORS["accent"],
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")
        tk.Label(
            sidebar_footer,
            text=f"Safe preview workflow  •  {version}",
            bg=COLORS["sidebar"],
            fg=COLORS["subtle"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(7, 0))
        sidebar.rowconfigure(5, weight=1)

        content = ttk.Frame(self)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, minsize=42)

        self.pages = {}
        for name in ("dashboard", "controls", "bindings", "recovery"):
            page = ttk.Frame(content, padding=(34, 28, 34, 14))
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self._build_dashboard(self.pages["dashboard"])
        self._build_control_names(self.pages["controls"])
        self._build_bindings(self.pages["bindings"])
        self._build_recovery(self.pages["recovery"])

        footer = tk.Frame(content, bg=COLORS["sidebar"], height=42)
        footer.grid(row=1, column=0, sticky="ew")
        footer.grid_propagate(False)
        self.footer_dot = tk.Label(
            footer, text="●", bg=COLORS["sidebar"], fg=COLORS["accent"], font=("Segoe UI", 8)
        )
        self.footer_dot.pack(side="left", padx=(24, 8))
        tk.Label(
            footer,
            textvariable=self.footer_status,
            bg=COLORS["sidebar"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="left")

        self.show_page("dashboard")

    def _page_heading(self, parent: ttk.Frame, title: str, description: str) -> None:
        ttk.Label(parent, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text=description,
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(5, 22))

    def _card(self, parent: tk.Misc, **pack_options) -> ttk.Frame:
        card = ttk.Frame(parent, style="Surface.TFrame", padding=20)
        card.pack(**pack_options)
        return card

    def _build_dashboard(self, page: ttk.Frame) -> None:
        self._page_heading(
            page,
            "Control center",
            "Your iRacing profiles and SimHub mappings stay in sync automatically.",
        )

        hero = self._card(page, fill="x")
        hero.columnconfigure(0, weight=1)
        hero.columnconfigure(1, weight=0)
        ttk.Label(hero, text="SYSTEM STATUS", style="Muted.Surface.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            textvariable=self.preview_summary,
            style="Metric.Surface.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(7, 4))
        ttk.Label(
            hero,
            textvariable=self.last_refreshed,
            style="Muted.Surface.TLabel",
        ).grid(row=2, column=0, sticky="w")
        live_controls = ttk.Frame(hero, style="Surface.TFrame")
        live_controls.grid(row=0, column=1, rowspan=3, padx=(24, 0), sticky="e")
        ttk.Checkbutton(
            live_controls,
            text="Live sync",
            variable=self.auto_refresh,
            command=self._auto_refresh_changed,
        ).pack(side="left", padx=(0, 12))
        self.scan_button = self._button(
            live_controls,
            "Refresh now",
            self.scan_setup,
            primary=True,
        )
        self.scan_button.pack(side="left")

        status_grid = ttk.Frame(page)
        status_grid.pack(fill="x", pady=14)
        for column in range(3):
            status_grid.columnconfigure(column, weight=1, uniform="status")
        self.status_cards: dict[str, tuple[tk.Label, tk.Label]] = {}
        for column, (key, title) in enumerate(
            (("iracing", "iRACING"), ("simhub", "SIMHUB"), ("device", "VIRTUAL DEVICE"))
        ):
            outer = ttk.Frame(status_grid, style="Surface.TFrame", padding=18)
            outer.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))
            tk.Label(
                outer,
                text=title,
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Segoe UI Semibold", 8),
            ).pack(anchor="w")
            value = tk.Label(
                outer,
                text="Not scanned",
                bg=COLORS["surface"],
                fg=COLORS["text"],
                font=("Segoe UI Semibold", 12),
                wraplength=220,
                justify="left",
            )
            value.pack(anchor="w", pady=(9, 4))
            detail = tk.Label(
                outer,
                text="Waiting",
                bg=COLORS["surface"],
                fg=COLORS["subtle"],
                font=("Segoe UI", 8),
                wraplength=220,
                justify="left",
            )
            detail.pack(anchor="w")
            self.status_cards[key] = (value, detail)

        paths = self._card(page, fill="x", pady=(0, 0))
        ttk.Label(paths, text="Source locations", style="CardTitle.Surface.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )
        paths.columnconfigure(1, weight=1)
        self._path_row(paths, 1, "iRacing folder", self.iracing_root, self._browse_iracing)
        self._path_row(paths, 2, "SimHub settings", self.simhub_settings, self._browse_simhub)

    def _path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: Callable[[], None],
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.Surface.TLabel").grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=5
        )
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
        button = self._button(parent, "Browse", command)
        button.grid(row=row, column=2, padx=(10, 0), pady=5)

    def _build_bindings(self, page: ttk.Frame) -> None:
        self._page_heading(
            page,
            "Live bindings",
            "External changes appear here automatically. Nothing is written until you approve it.",
        )

        selectors = self._card(page, fill="x")
        selectors.columnconfigure(0, weight=1)
        selectors.columnconfigure(1, weight=2)
        ttk.Label(selectors, text="iRacing profile", style="Muted.Surface.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(selectors, text="SimHub virtual controller", style="Muted.Surface.TLabel").grid(row=0, column=1, sticky="w", padx=(14, 0))
        self.profile_combo = ttk.Combobox(selectors, textvariable=self.profile_name, state="readonly")
        self.profile_combo.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.profile_combo.bind("<<ComboboxSelected>>", self._selection_changed)
        self.device_combo = ttk.Combobox(selectors, textvariable=self.device_name, state="readonly")
        self.device_combo.grid(row=1, column=1, sticky="ew", padx=(14, 0), pady=(6, 0))
        self.device_combo.bind("<<ComboboxSelected>>", self._selection_changed)

        table = self._card(page, fill="both", expand=True, pady=14)
        table.columnconfigure(0, weight=2)
        table.columnconfigure(1, weight=2)
        table.columnconfigure(2, weight=2)
        for column, title in enumerate(("ACTION", "CURRENT iRACING", "SIMHUB TARGET")):
            ttk.Label(table, text=title, style="Muted.Surface.TLabel").grid(
                row=0, column=column, sticky="w", pady=(0, 10)
            )
        self.binding_rows: dict[str, tuple[tk.Label, tk.Label]] = {}
        for row, action_id in enumerate(ACTIONS, start=1):
            tk.Frame(table, bg=COLORS["border"], height=1).grid(
                row=row * 2 - 1, column=0, columnspan=3, sticky="ew", pady=(0, 0)
            )
            tk.Label(
                table,
                text=ACTION_LABELS[action_id],
                bg=COLORS["surface"],
                fg=COLORS["text"],
                font=("Segoe UI Semibold", 10),
            ).grid(row=row * 2, column=0, sticky="w", pady=16)
            current = tk.Label(
                table,
                text="—",
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Segoe UI", 10),
            )
            current.grid(row=row * 2, column=1, sticky="w", pady=16)
            target = tk.Label(
                table,
                text="—",
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Segoe UI", 10),
            )
            target.grid(row=row * 2, column=2, sticky="w", pady=16)
            self.binding_rows[action_id] = (current, target)

        actions = ttk.Frame(page)
        actions.pack(fill="x")
        ttk.Checkbutton(
            actions,
            text="I understand this is the active iRacing profile",
            variable=self.active_ack,
            command=self._update_apply_state,
        ).pack(side="left")
        self.apply_button = self._button(actions, "Apply safely", self.apply_plan, danger=True)
        self.apply_button.pack(side="right", padx=(10, 0))
        self.preview_button = self._button(actions, "Refresh preview", self.preview_bindings, primary=True)
        self.preview_button.pack(side="right")
        self.apply_button.configure(state="disabled")

    def _build_control_names(self, page: ttk.Frame) -> None:
        self._page_heading(
            page,
            "Control names",
            "One control vocabulary, with the native name used by each supported simulator.",
        )

        search = self._card(page, fill="x")
        search.columnconfigure(0, weight=1)
        ttk.Label(search, text="Search controls or native game names", style="Muted.Surface.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(search, textvariable=self.control_result_summary, style="Muted.Surface.TLabel").grid(
            row=0, column=1, sticky="e", padx=(18, 0)
        )
        search_entry = ttk.Entry(search, textvariable=self.control_search)
        search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        search_entry.bind("<KeyRelease>", self._filter_control_names)

        table_card = self._card(page, fill="both", expand=True, pady=(14, 0))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)
        columns = ("control", *GAMES)
        self.control_tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="Control.Treeview",
            selectmode="browse",
        )
        self.control_tree.heading("control", text="CONTROL")
        self.control_tree.column("control", width=220, minwidth=180, stretch=False)
        for game_id, game_name in GAMES.items():
            self.control_tree.heading(game_id, text=game_name.upper())
            self.control_tree.column(game_id, width=210, minwidth=140, stretch=False)
        self.control_tree.grid(row=0, column=0, sticky="nsew")
        self.control_tree.bind("<<TreeviewSelect>>", self._control_name_selected)

        vertical = ttk.Scrollbar(table_card, orient="vertical", command=self.control_tree.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table_card, orient="horizontal", command=self.control_tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.control_tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        tk.Label(
            table_card,
            textvariable=self.control_detail,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
            wraplength=850,
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self._populate_control_names()

    def _filter_control_names(self, _event: tk.Event | None = None) -> None:
        self._populate_control_names()

    def _populate_control_names(self) -> None:
        control_ids = _matching_control_ids(self.control_search.get())
        self.control_tree.delete(*self.control_tree.get_children())
        for control_id in control_ids:
            values = [CONTROLS[control_id].label]
            values.extend(
                _native_control_text(NATIVE_CONTROL_NAMES[game_id][control_id])
                for game_id in GAMES
            )
            self.control_tree.insert("", "end", iid=control_id, values=values)
        total = len(CONTROLS)
        self.control_result_summary.set(f"{len(control_ids)} of {total} controls")
        self.control_detail.set(
            "Select a control to see mapping notes. “Not exposed” is verified absence; "
            "“Not observed” means the available game data was inconclusive."
        )

    def _control_name_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.control_tree.selection()
        if not selection:
            return
        control_id = selection[0]
        control = CONTROLS[control_id]
        details = [f"{control.label}  •  {control.kind.replace('_', ' ')}  •  {control_id}"]
        for game_id, game_name in GAMES.items():
            mapping = NATIVE_CONTROL_NAMES[game_id][control_id]
            if mapping.note:
                details.append(f"{game_name}: {mapping.note}")
        if len(details) == 1:
            details.append("All listed names are verified exact mappings.")
        self.control_detail.set("\n".join(details))

    def _build_recovery(self, page: ttk.Frame) -> None:
        self._page_heading(
            page,
            "Recovery",
            "Every applied change creates a hash-verified backup and a restore receipt.",
        )
        card = self._card(page, fill="x")
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text="Restore receipt", style="CardTitle.Surface.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            card,
            text="Select a receipt to inspect it before restoring the original controls file.",
            style="Muted.Surface.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 15))
        ttk.Entry(card, textvariable=self.receipt_path).grid(row=2, column=0, sticky="ew")
        self._button(card, "Choose receipt", self._browse_receipt).grid(row=2, column=1, padx=(10, 0))
        self.restore_info = tk.Label(
            card,
            text="No receipt selected",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
            wraplength=720,
        )
        self.restore_info.grid(row=3, column=0, columnspan=2, sticky="ew", pady=18)
        self.restore_button = self._button(card, "Restore original", self.restore_backup, danger=True)
        self.restore_button.grid(row=4, column=0, columnspan=2, sticky="e")
        self.restore_button.configure(state="disabled")

        safety = self._card(page, fill="x", pady=14)
        ttk.Label(safety, text="Built-in protection", style="CardTitle.Surface.TLabel").pack(anchor="w")
        ttk.Label(
            safety,
            text=(
                "✓ iRacing must be closed    ✓ Source hash must match the preview    "
                "✓ Backup is verified before writing    ✓ Failed writes roll back automatically"
            ),
            style="Muted.Surface.TLabel",
            wraplength=820,
        ).pack(anchor="w", pady=(10, 0))

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        primary: bool = False,
        danger: bool = False,
    ) -> tk.Button:
        background = COLORS["raised"]
        foreground = COLORS["text"]
        active = "#243247"
        if primary:
            background = COLORS["primary"]
            active = COLORS["primary_hover"]
        elif danger:
            background = "#3A2428"
            foreground = "#FFB2B2"
            active = "#503036"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=active,
            activeforeground=COLORS["text"],
            disabledforeground=COLORS["subtle"],
            relief="flat",
            bd=0,
            padx=17,
            pady=9,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

    def show_page(self, name: str) -> None:
        self.pages[name].tkraise()
        for page, button in self.nav_buttons.items():
            selected = page == name
            button.configure(
                bg=COLORS["raised"] if selected else COLORS["sidebar"],
                fg=COLORS["text"] if selected else COLORS["muted"],
            )

    def _set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.footer_status.set(message)
        self.footer_dot.configure(fg=COLORS["warning"] if busy else COLORS["accent"])
        state = "disabled" if busy else "normal"
        self.scan_button.configure(state=state)
        self.preview_button.configure(state=state)
        if not busy:
            self._update_apply_state()

    def _run_task(
        self,
        message: str,
        task: Callable[[], T],
        success: Callable[[T], None],
    ) -> None:
        if self.busy:
            return
        self._set_busy(True, message)

        def worker() -> None:
            try:
                result = task()
            except Exception as error:  # UI boundary reports domain errors uniformly.
                if not self._closing:
                    self.after(0, lambda error=error: self._task_failed(error))
            else:
                if not self._closing:
                    self.after(0, lambda: self._task_succeeded(result, success))

        threading.Thread(target=worker, daemon=True).start()

    def _task_failed(self, error: Exception) -> None:
        self._set_busy(False, "Action needs attention")
        messagebox.showerror("Sim Controls Manager", str(error), parent=self)

    def _task_succeeded(self, result: T, success: Callable[[T], None]) -> None:
        self._set_busy(False, "Ready")
        success(result)

    def _schedule_watch(self) -> None:
        if not self._closing and self._watch_after_id is None:
            self._watch_after_id = self.after(AUTO_REFRESH_MS, self._poll_sources)

    def _poll_sources(self) -> None:
        self._watch_after_id = None
        if (
            self._closing
            or not self.auto_refresh.get()
            or self.busy
            or self._watch_in_progress
        ):
            self._schedule_watch()
            return

        root_text = self.iracing_root.get().strip()
        settings_text = self.simhub_settings.get().strip()
        root = Path(root_text) if root_text else iracing.detect_iracing_directory()
        settings = Path(settings_text) if settings_text else simhub.default_settings_path()
        self._watch_in_progress = True

        def worker() -> None:
            devices, _error = iracing.enumerate_connected_devices()
            state = _source_signature(root, settings, devices)
            if not self._closing:
                self.after(0, lambda: self._watch_complete(state))

        threading.Thread(target=worker, daemon=True).start()

    def _watch_complete(self, state: tuple) -> None:
        self._watch_in_progress = False
        if not self.auto_refresh.get():
            self._source_state = state
            self._schedule_watch()
            return
        if self._source_state is None:
            self._source_state = state
        elif state != self._source_state:
            self._source_state = state
            self.footer_status.set("Configuration change detected • refreshing…")
            self.scan_setup(automatic=True)
        self._schedule_watch()

    def _auto_refresh_changed(self) -> None:
        if self.auto_refresh.get():
            self._source_state = None
            self.last_refreshed.set("Live sync enabled • checking every few seconds")
            if self._watch_after_id is None:
                self.after(0, self._poll_sources)
        else:
            self.last_refreshed.set("Live sync paused • use Refresh now to update")

    def _close(self) -> None:
        self._closing = True
        if self._watch_after_id is not None:
            try:
                self.after_cancel(self._watch_after_id)
            except tk.TclError:
                pass
        self.destroy()

    def scan_setup(self, automatic: bool = False) -> None:
        self._invalidate_preview()
        root_text = self.iracing_root.get().strip()
        settings_text = self.simhub_settings.get().strip()

        def task():
            root = Path(root_text) if root_text else None
            settings = Path(settings_text) if settings_text else None
            errors = {}
            try:
                discovery = iracing.discover(root)
            except Exception as error:
                discovery = None
                errors["iracing"] = str(error)
            try:
                inspection = simhub.inspect_control_mapper(settings)
            except Exception as error:
                inspection = None
                errors["simhub"] = str(error)
            devices, device_error = iracing.enumerate_connected_devices()
            if device_error:
                errors["device"] = device_error
            watched_root = discovery.iracing_directory if discovery else root
            watched_settings = inspection.settings_path if inspection else settings
            state = _source_signature(watched_root, watched_settings, devices)
            return discovery, inspection, devices, errors, state

        message = "Syncing changed configuration…" if automatic else "Scanning iRacing, SimHub, and connected controllers…"
        self._run_task(message, task, lambda result: self._scan_complete(result, automatic))

    def _scan_complete(self, result, automatic: bool = False) -> None:
        previous_profile = self.profile_name.get()
        previous_device = self.device_name.get()
        self.discovery, self.simhub_inspection, self.devices, errors, self._source_state = result
        if self.discovery:
            self.iracing_root.set(str(self.discovery.iracing_directory))
            names = [profile.name for profile in self.discovery.profiles]
            self.profile_combo["values"] = names
            selected = previous_profile if previous_profile in names else next(
                (profile.name for profile in self.discovery.profiles if profile.active),
                names[0] if names else "",
            )
            self.profile_name.set(selected)
            active_text = f"{len(names)} profile{'s' if len(names) != 1 else ''}"
            self._set_status_card("iracing", "Connected", active_text, True)
        else:
            self.profile_combo["values"] = ()
            self.profile_name.set("")
            self._set_status_card("iracing", "Not found", errors.get("iracing", "Choose the iRacing folder"), False)

        if self.simhub_inspection:
            self.simhub_settings.set(str(self.simhub_inspection.settings_path))
            count = len(self.simhub_inspection.bindings)
            self._set_status_card(
                "simhub",
                "Connected",
                f"{count}/{len(ACTIONS)} actions mapped",
                count > 0,
            )
        else:
            self._set_status_card("simhub", "Not found", errors.get("simhub", "Choose the settings file"), False)

        names = [device.name for device in self.devices]
        self.device_combo["values"] = names
        self.device_name.set(previous_device if previous_device in names else (names[0] if names else ""))
        if names:
            self._set_status_card("device", "Connected", f"{len(names)} controller{'s' if len(names) != 1 else ''} found", True)
        else:
            self._set_status_card("device", "Not found", errors.get("device", "Enable SimHub virtual output"), False)

        ready = bool(self.discovery and self.discovery.profiles and self.simhub_inspection and self.simhub_inspection.bindings and self.devices)
        self.preview_summary.set("Ready to preview safely" if ready else "Setup needs attention")
        now = datetime.now().strftime("%I:%M:%S %p").lstrip("0")
        live_text = "Live sync on" if self.auto_refresh.get() else "Live sync paused"
        self.last_refreshed.set(f"Updated {now}  •  {live_text}  •  read-only monitoring")
        self.footer_status.set("Configuration refreshed automatically" if automatic else "Setup scan complete")
        self._refresh_binding_rows()
        if ready:
            self.after(25, lambda: self.preview_bindings(quiet=True))

    def _set_status_card(self, key: str, value: str, detail: str, ready: bool) -> None:
        value_label, detail_label = self.status_cards[key]
        value_label.configure(text=value, fg=COLORS["accent"] if ready else COLORS["warning"])
        detail_label.configure(text=detail)

    def _selected_profile(self) -> iracing.ProfileCandidate:
        if not self.discovery:
            raise ValueError("Scan iRacing before creating a preview.")
        for profile in self.discovery.profiles:
            if profile.name == self.profile_name.get():
                return profile
        raise ValueError("Choose an iRacing profile.")

    def _selected_device(self) -> iracing.DeviceInfo:
        for device in self.devices:
            if device.name == self.device_name.get():
                return device
        raise ValueError("Choose the SimHub virtual controller.")

    def _catalog(self) -> Catalog:
        if not self.simhub_inspection or not self.simhub_inspection.bindings:
            raise ValueError("No supported SimHub actions were found. Scan the setup first.")
        device = self._selected_device()
        return validate_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": device.name,
                    "instanceGuid": device.instance_guid,
                    "productGuid": device.product_guid,
                },
                "bindings": [
                    {"actionId": binding.action_id, "virtualButton": binding.virtual_button}
                    for binding in self.simhub_inspection.bindings
                ],
            }
        )

    def _refresh_binding_rows(self) -> None:
        targets = {
            binding.action_id: binding.virtual_button
            for binding in self.simhub_inspection.bindings
        } if self.simhub_inspection else {}
        for action_id, (current, target) in self.binding_rows.items():
            current.configure(text="—", fg=COLORS["muted"])
            button = targets.get(action_id)
            target.configure(
                text=f"Button {button}" if button else "Not mapped",
                fg=COLORS["accent"] if button else COLORS["warning"],
            )

    def preview_bindings(self, quiet: bool = False) -> None:
        try:
            profile = self._selected_profile()
            catalog = self._catalog()
        except Exception as error:
            if quiet:
                self.footer_status.set(f"Preview unavailable • {error}")
            else:
                messagebox.showerror("Cannot create preview", str(error), parent=self)
            return

        def task():
            try:
                inspection = iracing.inspect_profile(profile)
                plan = iracing.plan_bindings(profile, catalog)
                return inspection, plan, None
            except Exception as error:
                return None, None, error

        message = "Refreshing binding preview…" if quiet else "Building a byte-exact preview…"
        self._run_task(message, task, lambda result: self._preview_result(result, quiet))

    def _preview_result(self, result, quiet: bool) -> None:
        inspection, plan, error = result
        if error is not None:
            self._invalidate_preview()
            self.footer_status.set(f"Preview needs attention • {error}")
            if not quiet:
                messagebox.showerror("Cannot create preview", str(error), parent=self)
            return
        self._preview_complete((inspection, plan))

    def _preview_complete(self, result) -> None:
        inspection, self.binding_plan = result
        by_action = {action.action_id: action for action in inspection.actions}
        changed = {change.action_id for change in self.binding_plan.changes}
        for action_id, (current, target) in self.binding_rows.items():
            action = by_action.get(action_id)
            current.configure(
                text=_binding_text(action.binding if action else None),
                fg=COLORS["text"],
            )
            if action_id in changed:
                target.configure(fg=COLORS["primary"])
        count = len(self.binding_plan.changes)
        if count:
            self.footer_status.set(f"Preview ready • {count} change{'s' if count != 1 else ''}")
        else:
            self.footer_status.set("Everything already matches")
        self._update_apply_state()

    def _selection_changed(self, _event=None) -> None:
        self._invalidate_preview()
        self.active_ack.set(False)
        self._refresh_binding_rows()
        self.after(25, lambda: self.preview_bindings(quiet=True))

    def _invalidate_preview(self) -> None:
        self.binding_plan = None
        if hasattr(self, "apply_button"):
            self.apply_button.configure(state="disabled")

    def _update_apply_state(self) -> None:
        if not hasattr(self, "apply_button"):
            return
        enabled = bool(self.binding_plan and self.binding_plan.changes and not self.busy)
        if enabled and self.binding_plan.profile.active and not self.active_ack.get():
            enabled = False
        self.apply_button.configure(state="normal" if enabled else "disabled")

    def apply_plan(self) -> None:
        plan = self.binding_plan
        if not plan:
            return
        if not messagebox.askyesno(
            "Apply previewed bindings?",
            f"Apply {len(plan.changes)} binding change(s) to {plan.profile.name}?\n\n"
            "A verified backup and restore receipt will be created first. iRacing must be closed.",
            icon="warning",
            parent=self,
        ):
            return

        def task():
            file_plan = plan_file_change(plan.profile.controls_path, plan.next_bytes)
            if file_plan.source_hash != plan.source_hash:
                raise FileChangeError("SOURCE_CHANGED", "The profile changed after preview. Create a new preview.")
            return apply_file_change(
                file_plan,
                _backup_directory(plan.profile.name),
                validate=_validate_iracing_bytes,
                is_target_in_use=iracing.is_iracing_running,
            )

        self._run_task("Creating backup and applying bindings…", task, self._apply_complete)

    def _apply_complete(self, result) -> None:
        self.last_receipt = result.receipt_path
        if result.receipt_path:
            self.receipt_path.set(str(result.receipt_path))
            self._inspect_receipt()
        self._invalidate_preview()
        self.footer_status.set("Bindings applied and backup verified")
        messagebox.showinfo(
            "Bindings applied",
            "Your iRacing bindings were applied successfully. A verified backup is available on the Recovery screen.",
            parent=self,
        )
        self.show_page("recovery")

    def _browse_iracing(self) -> None:
        path = filedialog.askdirectory(title="Choose your iRacing folder", parent=self)
        if path:
            self.iracing_root.set(path)
            self.scan_setup()

    def _browse_simhub(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose SimHub Control Mapper settings",
            filetypes=(("JSON settings", "*.json"), ("All files", "*.*")),
            parent=self,
        )
        if path:
            self.simhub_settings.set(path)
            self.scan_setup()

    def _browse_receipt(self) -> None:
        initial = _backup_directory(self.profile_name.get() or "Legacy")
        path = filedialog.askopenfilename(
            title="Choose a restore receipt",
            initialdir=str(initial) if initial.is_dir() else None,
            filetypes=(("Restore receipt", "*-receipt.json"), ("JSON files", "*.json")),
            parent=self,
        )
        if path:
            self.receipt_path.set(path)
            self._inspect_receipt()

    def _inspect_receipt(self) -> None:
        try:
            preview = preview_restore(self.receipt_path.get())
        except Exception as error:
            self.restore_info.configure(text=str(error), fg=COLORS["danger"])
            self.restore_button.configure(state="disabled")
            return
        status_labels = {
            "ready": "Ready to restore",
            "already-restored": "Already restored",
            "changed-since-apply": "Target changed since apply",
            "target-missing": "Target file is missing",
        }
        label = status_labels.get(preview.status, preview.status)
        self.restore_info.configure(
            text=f"{label}\nOriginal file: {preview.receipt.originalPath}\nBackup created: {preview.receipt.createdAt}",
            fg=COLORS["accent"] if preview.status == "ready" else COLORS["warning"],
        )
        self.restore_button.configure(state="normal" if preview.status == "ready" else "disabled")

    def restore_backup(self) -> None:
        receipt = self.receipt_path.get()
        if not receipt:
            return
        if not messagebox.askyesno(
            "Restore original controls?",
            "This will replace the applied controls file with its verified backup. iRacing must be closed.",
            icon="warning",
            parent=self,
        ):
            return

        self._run_task(
            "Restoring verified backup…",
            lambda: restore_file(
                receipt,
                is_target_in_use=iracing.is_iracing_running,
                validate=_validate_iracing_bytes,
            ),
            self._restore_complete,
        )

    def _restore_complete(self, _result) -> None:
        self._inspect_receipt()
        self.footer_status.set("Original controls restored")
        messagebox.showinfo("Restore complete", "The original iRacing controls were restored.", parent=self)


def main(*, smoke_test: bool = False) -> int:
    app = SimControlsApp()
    if smoke_test:
        app.withdraw()
        app.update_idletasks()
        app._close()
        return 0
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
