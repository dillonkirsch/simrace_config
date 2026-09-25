"""Modern, dependency-free Windows interface for Sim Controls Manager."""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, TypeVar

from sim_controls_manager import simhub, updater
from sim_controls_manager.adapters import iracing
from sim_controls_manager.catalog import ACTIONS, Catalog, validate_catalog
from sim_controls_manager.file_change import (
    FileChangeError,
    apply_file_change,
    plan_file_change,
    preview_restore,
    restore_file,
)

T = TypeVar("T")


COLORS = {
    "canvas": "#0B0F14",
    "sidebar": "#0E141C",
    "surface": "#121A24",
    "raised": "#192432",
    "border": "#263446",
    "text": "#F4F7FA",
    "muted": "#8FA1B5",
    "subtle": "#617489",
    "accent": "#55D6BE",
    "primary": "#4F8CFF",
    "primary_hover": "#70A3FF",
    "warning": "#F2B84B",
    "danger": "#F06A6A",
}

ACTION_LABELS = {
    "pit_limiter": "Pit limiter",
    "tc_increase": "Traction control +",
    "tc_decrease": "Traction control −",
}


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


class SimControlsApp(tk.Tk):
    """Single-window, preview-first desktop workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Sim Controls Manager")
        self.geometry("1180x760")
        self.minsize(1040, 680)
        self.configure(bg=COLORS["canvas"])
        self._set_icon()

        self.discovery: iracing.DiscoveryResult | None = None
        self.simhub_inspection: simhub.SimHubInspection | None = None
        self.devices: tuple[iracing.DeviceInfo, ...] = ()
        self.binding_plan: iracing.BindingPlan | None = None
        self.last_receipt: Path | None = None
        self.busy = False

        self.iracing_root = tk.StringVar()
        self.simhub_settings = tk.StringVar()
        self.profile_name = tk.StringVar()
        self.device_name = tk.StringVar()
        self.active_ack = tk.BooleanVar(value=False)
        self.footer_status = tk.StringVar(value="Ready to scan your setup")
        self.preview_summary = tk.StringVar(value="Scan your setup to begin")
        self.receipt_path = tk.StringVar()

        self._configure_styles()
        self._build_shell()
        self.after(200, self.scan_setup)

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

    def _build_shell(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        brand = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(26, 34))
        tk.Label(
            brand,
            text="SC",
            bg=COLORS["accent"],
            fg=COLORS["canvas"],
            font=("Segoe UI Semibold", 12),
            width=3,
            height=1,
        ).pack(side="left", padx=(0, 12))
        tk.Label(
            brand,
            text="SIM CONTROLS",
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).pack(side="left")

        self.nav_buttons: dict[str, tk.Button] = {}
        for index, (page, label) in enumerate(
            (("dashboard", "Overview"), ("bindings", "Bindings"), ("recovery", "Recovery")),
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
                padx=22,
                pady=13,
                font=("Segoe UI Semibold", 10),
                cursor="hand2",
            )
            button.grid(row=index, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[page] = button

        version = updater.current_version()
        tk.Label(
            sidebar,
            text=f"Preview-first • {version}",
            bg=COLORS["sidebar"],
            fg=COLORS["subtle"],
            font=("Segoe UI", 8),
        ).grid(row=5, column=0, sticky="sw", padx=22, pady=22)
        sidebar.rowconfigure(4, weight=1)

        content = ttk.Frame(self)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, minsize=42)

        self.pages = {}
        for name in ("dashboard", "bindings", "recovery"):
            page = ttk.Frame(content, padding=(34, 28, 34, 14))
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self._build_dashboard(self.pages["dashboard"])
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
            "Your racing controls, in one place",
            "Connect the pieces once. Preview every change before it reaches the sim.",
        )

        hero = self._card(page, fill="x")
        hero.columnconfigure(0, weight=1)
        hero.columnconfigure(1, weight=0)
        ttk.Label(hero, text="SYSTEM READINESS", style="Muted.Surface.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            textvariable=self.preview_summary,
            style="Metric.Surface.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(7, 4))
        ttk.Label(
            hero,
            text="Read-only scan • no files are changed",
            style="Muted.Surface.TLabel",
        ).grid(row=2, column=0, sticky="w")
        self.scan_button = self._button(hero, "Scan setup", self.scan_setup, primary=True)
        self.scan_button.grid(row=0, column=1, rowspan=3, padx=(24, 0))

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
            "Preview bindings",
            "Choose a profile and virtual device, then review the exact three-action change.",
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
        self.preview_button = self._button(actions, "Create preview", self.preview_bindings, primary=True)
        self.preview_button.pack(side="right")
        self.apply_button.configure(state="disabled")

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
                self.after(0, lambda: self._task_failed(error))
            else:
                self.after(0, lambda: self._task_succeeded(result, success))

        threading.Thread(target=worker, daemon=True).start()

    def _task_failed(self, error: Exception) -> None:
        self._set_busy(False, "Action needs attention")
        messagebox.showerror("Sim Controls Manager", str(error), parent=self)

    def _task_succeeded(self, result: T, success: Callable[[T], None]) -> None:
        self._set_busy(False, "Ready")
        success(result)

    def scan_setup(self) -> None:
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
            return discovery, inspection, devices, errors

        self._run_task("Scanning iRacing, SimHub, and connected controllers…", task, self._scan_complete)

    def _scan_complete(self, result) -> None:
        self.discovery, self.simhub_inspection, self.devices, errors = result
        if self.discovery:
            self.iracing_root.set(str(self.discovery.iracing_directory))
            names = [profile.name for profile in self.discovery.profiles]
            self.profile_combo["values"] = names
            selected = next((profile.name for profile in self.discovery.profiles if profile.active), names[0] if names else "")
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
            self._set_status_card("simhub", "Connected", f"{count}/3 actions mapped", count > 0)
        else:
            self._set_status_card("simhub", "Not found", errors.get("simhub", "Choose the settings file"), False)

        names = [device.name for device in self.devices]
        self.device_combo["values"] = names
        previous = self.device_name.get()
        self.device_name.set(previous if previous in names else (names[0] if names else ""))
        if names:
            self._set_status_card("device", "Connected", f"{len(names)} controller{'s' if len(names) != 1 else ''} found", True)
        else:
            self._set_status_card("device", "Not found", errors.get("device", "Enable SimHub virtual output"), False)

        ready = bool(self.discovery and self.discovery.profiles and self.simhub_inspection and self.simhub_inspection.bindings and self.devices)
        self.preview_summary.set("Ready to preview safely" if ready else "Setup needs attention")
        self.footer_status.set("Setup scan complete")
        self._refresh_binding_rows()

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

    def preview_bindings(self) -> None:
        try:
            profile = self._selected_profile()
            catalog = self._catalog()
        except Exception as error:
            messagebox.showerror("Cannot create preview", str(error), parent=self)
            return

        def task():
            inspection = iracing.inspect_profile(profile)
            plan = iracing.plan_bindings(profile, catalog)
            return inspection, plan

        self._run_task("Building a byte-exact preview…", task, self._preview_complete)

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
        self._refresh_binding_rows()

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


def main() -> int:
    app = SimControlsApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
