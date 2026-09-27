"""Native desktop workspace composition, separate from simulator operations."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from sim_controls_manager import deck_layout, updater
from sim_controls_manager.catalog import ACTIONS
from sim_controls_manager.control_names import CONTROLS, GAMES, NATIVE_CONTROL_NAMES
from sim_controls_manager.file_change import preview_restore
from sim_controls_manager.recovery_history import STATUS_LABELS, discover_history, target_identity
from sim_controls_manager.ui_theme import COLORS, TYPE, FONT_ICON, Tooltip, ScrollFrame, divider, label, panel

ACTION_LABELS = {"pit_limiter": "Pit limiter", "tc_increase": "Traction control +", "tc_decrease": "Traction control −"}
NAVIGATION = (("dashboard", "\ue80f", "Overview"), ("controls", "\ueca5", "Deck Studio"),
              ("control_map", "\ue8fd", "Control Map"), ("bindings", "\ue8ab", "Bindings"),
              ("recovery", "\ue81c", "Recovery"))
SIMULATORS = (("iracing", "iRacing", "IR"), ("assetto_corsa", "Assetto Corsa", "AC"),
              ("acc", "ACC", "CC"), ("assetto_corsa_evo", "Assetto Corsa EVO", "EV"),
              ("automobilista_2", "Automobilista 2", "A2"), ("lmu", "Le Mans Ultimate", "LM"))


class WorkspaceUI:
    def _build_shell(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.mapping_summary = tk.StringVar(value="No preview yet")
        self.review_detail = tk.StringVar(value="Choose a simulator profile and virtual controller, then refresh the preview.")
        self.profile_context = tk.StringVar(value="No profile selected")
        self.device_context = tk.StringVar(value="No controller selected")
        self.pending_detail = tk.StringVar(value="Scan your setup to compare the current bindings with your SimHub targets.")
        self.history_summary = tk.StringVar(value="Looking for saved receipts…")
        self.last_backup_summary = tk.StringVar(value="No backup selected")
        self.overview_health = tk.StringVar(value="Discover your racing setup")
        self.overview_health_detail = tk.StringVar(value="Profiles, SimHub roles, and connected controllers are checked together.")
        self.live_status = tk.StringVar(value="Live sync enabled")
        self._history_entries = ()
        self._external_receipts = set()
        self._history_loading = False
        self._activity = []

        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=190)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(8, weight=1)
        brand = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand.grid(row=0, column=0, sticky="ew", padx=16, pady=(22, 24))
        mark = tk.Canvas(brand, width=30, height=30, bg=COLORS["sidebar"], highlightthickness=0)
        mark.pack(side="left", padx=(0, 10))
        mark.create_rectangle(2, 2, 28, 28, fill=COLORS["selection_key"], outline=COLORS["primary"])
        for x, y in ((8, 8), (19, 8), (8, 19), (19, 19)):
            mark.create_rectangle(x, y, x+4, y+4, fill=COLORS["primary_hover"], outline="")
        text = tk.Frame(brand, bg=COLORS["sidebar"])
        text.pack(side="left")
        label(text, "Sim Controls", kind="section").pack(anchor="w")
        label(text, "Manager", kind="metadata", tone="subtle").pack(anchor="w")
        label(sidebar, "Workspace", kind="metadata", tone="subtle").grid(row=1, column=0, sticky="w", padx=19, pady=(0, 8))
        self.nav_buttons, self.nav_rows, self.nav_icons, self.nav_indicators = {}, {}, {}, {}
        for index, (name, icon, title) in enumerate(NAVIGATION):
            row = tk.Frame(sidebar, bg=COLORS["sidebar"], height=42)
            row.grid(row=index+2, column=0, sticky="ew", padx=8, pady=(8 if name == "recovery" else 2, 2))
            row.pack_propagate(False)
            indicator = tk.Frame(row, bg=COLORS["sidebar"], width=3)
            indicator.pack(side="left", fill="y", pady=10)
            glyph = tk.Label(row, text=icon, font=(FONT_ICON, -17), width=3,
                             bg=COLORS["sidebar"], fg=COLORS["muted"], cursor="hand2")
            glyph.pack(side="left", fill="y")
            button = tk.Button(row, text=title, command=lambda page=name: self.show_page(page),
                               bg=COLORS["sidebar"], fg=COLORS["muted"], bd=0, relief="flat",
                               activebackground=COLORS["hover"], activeforeground=COLORS["text"],
                               anchor="w", font=TYPE["body"], takefocus=True, cursor="hand2")
            button.pack(side="left", fill="both", expand=True)
            glyph.bind("<Button-1>", lambda e, page=name: self.show_page(page))
            button.bind("<Enter>", lambda e, page=name: self._nav_hover(page, True))
            button.bind("<Leave>", lambda e, page=name: self._nav_hover(page, False))
            self.nav_buttons[name], self.nav_rows[name] = button, row
            self.nav_icons[name], self.nav_indicators[name] = glyph, indicator
            self.bind(f"<Control-Key-{index+1}>", lambda e, page=name: self.show_page(page))
            Tooltip(button, f"{title} · Ctrl+{index+1}")

        bottom = tk.Frame(sidebar, bg=COLORS["sidebar"])
        bottom.grid(row=9, column=0, sticky="ew", padx=16, pady=16)
        divider(bottom)
        self.sidebar_connection = label(bottom, "○  Waiting for scan", tone="muted", kind="secondary")
        self.sidebar_connection.pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(bottom, text="Live sync", variable=self.auto_refresh,
                        command=self._auto_refresh_changed, style="Sidebar.TCheckbutton").pack(anchor="w")
        label(bottom, f"Local workspace  ·  {updater.current_version()}", kind="metadata", tone="subtle", wrap=155).pack(fill="x", pady=(14, 0))

        content = ttk.Frame(self, style="Workspace.TFrame")
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        chrome = tk.Frame(content, bg=COLORS["sidebar"], height=38, padx=20)
        chrome.grid(row=0, column=0, sticky="ew")
        chrome.pack_propagate(False)
        label(chrome, "Workspace", tone="subtle", kind="secondary").pack(side="left")
        label(chrome, " / ", tone="subtle").pack(side="left", padx=8)
        self.footer_context = tk.StringVar(value="Overview")
        label(chrome, variable=self.footer_context, kind="secondary").pack(side="left")
        label(chrome, "Preview before every write", tone="muted", kind="metadata").pack(side="right")
        self.pages = {}
        for name, _, _ in NAVIGATION:
            page = ttk.Frame(content, style="Workspace.TFrame", padding=(20, 18, 20, 14))
            page.grid(row=1, column=0, sticky="nsew")
            self.pages[name] = page
        self._build_dashboard(self.pages["dashboard"])
        self._build_control_names(self.pages["controls"])
        self._build_control_map(self.pages["control_map"])
        self._build_bindings(self.pages["bindings"])
        self._build_recovery(self.pages["recovery"])

        footer = tk.Frame(content, bg=COLORS["sidebar"], height=28)
        footer.grid(row=2, column=0, sticky="ew")
        footer.pack_propagate(False)
        self.footer_dot = label(footer, "●", kind="metadata", tone="subtle")
        self.footer_dot.pack(side="left", padx=(16, 8))
        label(footer, variable=self.footer_status, kind="metadata", tone="muted").pack(side="left")
        label(footer, variable=self.live_status, kind="metadata", tone="subtle").pack(side="right", padx=16)
        self.footer_status.trace_add("write", self._record_activity)
        self.show_page("dashboard")
        self.after_idle(self._refresh_receipts)

    def _nav_hover(self, name, active):
        if name == self.current_page:
            return
        color = COLORS["surface"] if active else COLORS["sidebar"]
        for widget in (self.nav_buttons[name], self.nav_rows[name], self.nav_icons[name]):
            widget.configure(bg=color)

    def _page_heading(self, parent, title, description):
        header = ttk.Frame(parent, style="Workspace.TFrame")
        header.pack(fill="x", pady=(0, 16))
        label(header, title, kind="title").pack(anchor="w")
        label(header, description, tone="muted", kind="secondary", wrap=800).pack(fill="x", pady=(4, 0))

    def _section_header(self, parent, title, meta=""):
        header = tk.Frame(parent, bg=parent.cget("bg"))
        header.pack(fill="x", pady=(0, 12))
        label(header, title, kind="section").pack(side="left")
        if meta:
            label(header, meta, kind="metadata", tone="subtle").pack(side="right")
        return header

    def _build_dashboard(self, page):
        viewport = ttk.Frame(page)
        viewport.pack(fill="both", expand=True)
        viewport.columnconfigure(0, weight=1)
        viewport.rowconfigure(0, weight=1)
        self.dashboard_canvas = tk.Canvas(viewport, bg=COLORS["workspace"], highlightthickness=0, bd=0)
        self.dashboard_canvas.grid(row=0, column=0, sticky="nsew")
        self.dashboard_scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.dashboard_canvas.yview, style="Slim.Vertical.TScrollbar")
        self.dashboard_canvas.configure(yscrollcommand=self.dashboard_scrollbar.set)
        body = ttk.Frame(self.dashboard_canvas)
        self.dashboard_body = body
        self.dashboard_window = self.dashboard_canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", self._dashboard_frame_configured)
        self.dashboard_canvas.bind("<Configure>", self._dashboard_canvas_configured)
        self.bind_all("<MouseWheel>", self._dashboard_mousewheel, add="+")
        self._page_heading(body, "Overview", "Your simulator profiles, connections, and the work ready for your next session.")

        health = panel(body, padding=14, tone="surface_alt")
        health.pack(fill="x", pady=(0, 12))
        health.columnconfigure(1, weight=1)
        self.health_icon = label(health, "◉", tone="primary_hover", kind="title")
        self.health_icon.grid(row=0, column=0, rowspan=2, padx=(0, 14))
        label(health, variable=self.overview_health, kind="section").grid(row=0, column=1, sticky="w")
        label(health, variable=self.overview_health_detail, kind="secondary", tone="muted", wrap=570).grid(row=1, column=1, sticky="ew", pady=(4, 0))
        self.scan_button = self._button(health, "Refresh setup", self.scan_setup)
        self.scan_button.grid(row=0, column=2, rowspan=2, padx=(16, 0))

        grid = ttk.Frame(body)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=3, uniform="overview")
        grid.columnconfigure(1, weight=2, uniform="overview")
        grid.rowconfigure(0, weight=1)
        sims = panel(grid, padding=14)
        sims.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._section_header(sims, "Simulator library", "6 adapters")
        self.status_cards = {}
        for index, (key, title, initials) in enumerate(SIMULATORS):
            row = tk.Frame(sims, bg=COLORS["surface"], pady=9)
            row.pack(fill="both", expand=True)
            row.columnconfigure(1, weight=1)
            glyph = label(row, initials, kind="label", tone="muted")
            glyph.configure(bg=COLORS["raised"], width=3, pady=7)
            glyph.grid(row=0, column=0, rowspan=2, padx=(0, 12))
            label(row, title, kind="label").grid(row=0, column=1, sticky="w")
            detail = label(row, "Waiting for discovery", kind="secondary", tone="subtle", wrap=310)
            detail.grid(row=1, column=1, sticky="ew", pady=(3, 0), padx=(0, 8))
            value = label(row, "Not scanned", kind="secondary", tone="muted")
            value.grid(row=0, column=2, sticky="e")
            dot = label(row, "●", kind="metadata", tone="subtle")
            dot.grid(row=0, column=3, padx=(8, 0))
            self.status_cards[key] = dot, value, detail
            if index < 5:
                tk.Frame(sims, bg=COLORS["line"], height=1).pack(fill="x")
        right = ttk.Frame(grid)
        right.grid(row=0, column=1, sticky="nsew")
        connections = panel(right, padding=14)
        connections.pack(fill="x")
        self._section_header(connections, "Input connections")
        for key, title in (("simhub", "SimHub Control Mapper"), ("device", "Virtual controller")):
            row = tk.Frame(connections, bg=COLORS["surface"])
            row.pack(fill="x", pady=(4, 12))
            row.columnconfigure(1, weight=1)
            dot = label(row, "●", tone="subtle", kind="metadata")
            dot.grid(row=0, column=0, padx=(0, 8))
            label(row, title, kind="label").grid(row=0, column=1, sticky="w")
            value = label(row, "Not scanned", kind="secondary", tone="muted")
            value.grid(row=0, column=2, sticky="e")
            detail = label(row, "Waiting for discovery", kind="secondary", tone="subtle", wrap=320)
            detail.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(4, 0))
            self.status_cards[key] = dot, value, detail
        pending = panel(right, padding=14)
        pending.pack(fill="both", expand=True, pady=(12, 0))
        self._section_header(pending, "Binding review")
        label(pending, variable=self.mapping_summary, kind="section", tone="primary_hover").pack(anchor="w")
        label(pending, variable=self.pending_detail, kind="secondary", tone="muted", wrap=320).pack(fill="x", pady=(7, 10))
        label(pending, variable=self.profile_context, kind="secondary", tone="subtle", wrap=320).pack(fill="x", pady=(0, 12))
        self._button(pending, "Open bindings  →", lambda: self.show_page("bindings")).pack(anchor="w", side="bottom")

        lower = ttk.Frame(body)
        lower.pack(fill="both", expand=True, pady=(12, 0))
        for column in range(3):
            lower.columnconfigure(column, weight=1, uniform="lower")
        lower.rowconfigure(0, weight=1)
        deck = panel(lower, padding=14)
        deck.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._section_header(deck, "Your deck")
        self.deck_overview = label(deck, "", tone="muted", kind="secondary", wrap=280)
        self.deck_overview.pack(fill="x", pady=(0, 12))
        self._button(deck, "Open Deck Studio  →", lambda: self.show_page("controls"), ghost=True).pack(anchor="w", side="bottom")
        backup = panel(lower, padding=14)
        backup.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        self._section_header(backup, "Recovery")
        label(backup, variable=self.last_backup_summary, kind="secondary", tone="muted", wrap=280).pack(fill="x", pady=(0, 12))
        self._button(backup, "View backup history  →", lambda: self.show_page("recovery"), ghost=True).pack(anchor="w", side="bottom")
        activity = panel(lower, padding=14)
        activity.grid(row=0, column=2, sticky="nsew")
        self._section_header(activity, "Session activity")
        self.activity_label = label(activity, "Activity will appear after the first scan.", tone="muted", kind="secondary", wrap=280)
        self.activity_label.pack(fill="x")

        source = ttk.Frame(body)
        source.pack(fill="x", pady=(10, 0))
        self.source_disclosure = self._button(source, "›  Source locations", self._toggle_source_locations, ghost=True)
        self.source_disclosure.pack(side="top", anchor="w")
        paths = ttk.Frame(source, style="Surface.TFrame", padding=14)
        self.source_locations_panel = paths
        paths.columnconfigure(1, weight=1)
        for index, (title, variable, command) in enumerate((
            ("iRacing", self.iracing_root, self._browse_iracing),
            ("Assetto Corsa", self.assetto_corsa_root, self._browse_assetto_corsa),
            ("ACC", self.acc_root, self._browse_acc),
            ("Assetto Corsa EVO", self.assetto_corsa_evo_root, self._browse_assetto_corsa_evo),
            ("Automobilista 2", self.automobilista_2_root, self._browse_automobilista_2),
            ("Le Mans Ultimate", self.lmu_root, self._browse_lmu),
            ("SimHub settings", self.simhub_settings, self._browse_simhub))):
            self._path_row(paths, index, title, variable, command)
        label(source, variable=self.last_refreshed, tone="subtle", kind="metadata").pack(anchor="w", pady=(5, 0))

    def _dashboard_canvas_configured(self, event):
        self.dashboard_canvas.itemconfigure(self.dashboard_window, width=event.width)
        self.dashboard_canvas.coords(self.dashboard_window, 0, 0)
        self.dashboard_canvas.itemconfigure(self.dashboard_window, height=max(event.height, self.dashboard_body.winfo_reqheight()))
        self.after_idle(self._update_dashboard_scrollbar)

    def _dashboard_frame_configured(self, _event):
        self.dashboard_canvas.itemconfigure(self.dashboard_window, height=max(self.dashboard_canvas.winfo_height(), self.dashboard_body.winfo_reqheight()))
        self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))
        self.after_idle(self._update_dashboard_scrollbar)

    def _build_bindings(self, page):
        self._page_heading(page, "Bindings", "Connect simulator actions to stable SimHub targets. Review every change before applying.")
        selectors = panel(page, padding=14, tone="surface_alt")
        selectors.pack(fill="x", pady=(0, 12))
        combos = []
        for column, (title, variable) in enumerate((("Simulator", self.game_name), ("Control profile", self.profile_name), ("Virtual controller", self.device_name))):
            selectors.columnconfigure(column, weight=1, uniform="selectors")
            label(selectors, title, kind="label", tone="muted").grid(row=0, column=column, sticky="w", padx=(0, 12))
            combo = ttk.Combobox(selectors, textvariable=variable, state="readonly", width=12)
            combo.grid(row=1, column=column, sticky="ew", padx=(0, 12 if column < 2 else 0), pady=(7, 0))
            combos.append(combo)
        self.game_combo, self.profile_combo, self.device_combo = combos
        self.game_combo.configure(values=("iRacing", "Assetto Corsa", "ACC", "Assetto Corsa EVO", "Le Mans Ultimate"))
        for combo, handler in ((self.game_combo, self._game_selection_changed), (self.profile_combo, self._selection_changed), (self.device_combo, self._selection_changed)):
            combo.bind("<<ComboboxSelected>>", handler)

        viewport = ScrollFrame(page)
        workspace = viewport.body
        workspace.columnconfigure(0, weight=1)
        workspace.columnconfigure(1, minsize=274)
        workspace.rowconfigure(0, weight=1)
        editor = panel(workspace, padding=16)
        editor.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._section_header(editor, "Action mappings", "3 supported actions")
        table = tk.Frame(editor, bg=COLORS["surface"])
        table.pack(fill="x")
        for col, weight in ((0, 3), (1, 3), (2, 0), (3, 2)):
            table.columnconfigure(col, weight=weight, uniform="binding" if weight else "")
        for col, title in ((0, "Simulator action"), (1, "Current binding"), (3, "SimHub target")):
            label(table, title, tone="muted", kind="metadata").grid(row=0, column=col, sticky="w", pady=(3, 10), padx=(4, 8))
        self.binding_rows, self.binding_states, self.binding_native = {}, {}, {}
        for index, action_id in enumerate(ACTIONS):
            row = index*3+1
            tk.Frame(table, bg=COLORS["line"], height=1).grid(row=row, column=0, columnspan=4, sticky="ew")
            label(table, ACTION_LABELS[action_id], kind="label", wrap=170).grid(row=row+1, column=0, sticky="ew", padx=(4, 10), pady=(12, 2))
            native = label(table, action_id, tone="subtle", kind="metadata", wrap=170)
            native.grid(row=row+2, column=0, sticky="new", padx=(4, 10), pady=(0, 12))
            current = label(table, "Awaiting preview", tone="muted", wrap=170)
            current.grid(row=row+1, column=1, sticky="ew", padx=(4, 10), pady=(12, 2))
            state = label(table, "Not compared", tone="subtle", kind="metadata")
            state.grid(row=row+2, column=1, sticky="nw", padx=4, pady=(0, 12))
            label(table, "→", tone="primary_hover", kind="section").grid(row=row+1, column=2, rowspan=2, padx=10)
            target = label(table, "Not mapped", tone="subtle", kind="label", wrap=150)
            target.grid(row=row+1, column=3, sticky="ew", pady=(12, 2))
            label(table, "Virtual button", kind="metadata", tone="subtle").grid(row=row+2, column=3, sticky="nw", pady=(0, 12))
            self.binding_rows[action_id] = current, target
            self.binding_states[action_id], self.binding_native[action_id] = state, native
        divider(editor)
        label(editor, variable=self.current_binding_heading, kind="label").pack(anchor="w")
        self.binding_profile_path = label(editor, "Select a profile to inspect its controls file.", tone="muted", kind="secondary", wrap=550)
        self.binding_profile_path.pack(fill="x", pady=(6, 8))
        note = tk.Frame(editor, bg=COLORS["surface_alt"], padx=12, pady=8)
        note.pack(fill="x", side="bottom")
        label(note, "Need more actions?", kind="label").pack(anchor="w")
        label(note, "Control Map contains the full simulator vocabulary. Deck Studio manages your per-game shortcut plan.", tone="muted", kind="secondary", wrap=530).pack(fill="x", pady=(5, 8))
        self._button(note, "Explore Control Map  →", lambda: self.show_page("control_map"), ghost=True).pack(anchor="w")

        review = panel(workspace, padding=16)
        review.grid(row=0, column=1, sticky="nsew")
        review.configure(width=274)
        review.pack_propagate(False)
        self._section_header(review, "Change review")
        label(review, variable=self.mapping_summary, kind="section", tone="primary_hover", wrap=235).pack(fill="x")
        label(review, variable=self.review_detail, tone="muted", kind="secondary", wrap=235).pack(fill="x", pady=(8, 14))
        divider(review)
        label(review, "Destination", kind="label").pack(anchor="w")
        label(review, variable=self.profile_context, tone="muted", kind="secondary", wrap=235).pack(fill="x", pady=(6, 12))
        label(review, "Input source", kind="label").pack(anchor="w")
        label(review, variable=self.device_context, tone="muted", kind="secondary", wrap=235).pack(fill="x", pady=(6, 12))
        self.preview_button = self._button(review, "Refresh preview", self.preview_bindings)
        self.preview_button.pack(fill="x", pady=(5, 12))
        label(review, "A verified backup is created for each changed controls file.", tone="subtle", kind="secondary", wrap=235).pack(fill="x", side="bottom")

        cross = panel(page, padding=12, tone="surface_alt")
        cross.pack(fill="x", pady=(12, 0))
        cross.columnconfigure(0, weight=1)
        label(cross, "Across your simulators", kind="label").grid(row=0, column=0, sticky="w")
        label(cross, "Preview compatible profiles before copying or applying.", kind="secondary", tone="muted", wrap=460).grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.copy_iracing_button = self._button(cross, "Copy iRacing → games", self.copy_iracing_to_games)
        self.copy_iracing_button.grid(row=0, column=1, rowspan=2, padx=(12, 8))
        self.apply_all_button = self._button(cross, "Apply to all games", self.apply_catalog_to_all_games)
        self.apply_all_button.grid(row=0, column=2, rowspan=2)
        actions = ttk.Frame(page)
        actions.pack(fill="x", pady=(12, 0))
        self.active_ack_check = ttk.Checkbutton(actions, textvariable=self.active_ack_label, variable=self.active_ack, command=self._update_apply_state)
        self.active_ack_check.pack(side="left")
        self.apply_button = self._button(actions, "Apply selected", self.apply_plan, primary=True)
        self.apply_button.pack(side="right")
        self._set_button_state(self.apply_button, "disabled")
        self._set_button_state(self.apply_all_button, "disabled")
        cross.pack_forget()
        actions.pack_forget()
        actions.pack(side="bottom", fill="x", pady=(12, 0))
        cross.pack(side="bottom", fill="x", pady=(12, 0))
        viewport.pack(fill="both", expand=True)

    def _build_recovery(self, page):
        self._page_heading(page, "Recovery", "Browse saved changes, verify backup integrity, and restore a previous controls file.")
        toolbar = panel(page, padding=12, tone="surface_alt")
        toolbar.pack(fill="x", pady=(0, 12))
        label(toolbar, variable=self.history_summary, kind="label").pack(side="left")
        self._button(toolbar, "Choose receipt…", self._browse_receipt).pack(side="right")
        self.history_refresh_button = self._button(toolbar, "Refresh history", self._refresh_receipts, ghost=True)
        self.history_refresh_button.pack(side="right", padx=(0, 8))
        self.history_filter = tk.StringVar(value="All simulators")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.history_filter, values=("All simulators", "iRacing", "Assetto Corsa", "ACC", "Assetto Corsa EVO", "Le Mans Ultimate"), state="readonly", width=17)
        filter_combo.pack(side="right", padx=12)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._populate_history())

        workspace = ttk.Frame(page)
        workspace.pack(fill="both", expand=True)
        workspace.columnconfigure(0, weight=3, uniform="recovery")
        workspace.columnconfigure(1, weight=2, uniform="recovery")
        workspace.rowconfigure(0, weight=1)
        history = panel(workspace, padding=0)
        history.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        history.columnconfigure(0, weight=1)
        history.rowconfigure(1, weight=1)
        heading = tk.Frame(history, bg=COLORS["surface"], padx=14, pady=14)
        heading.grid(row=0, column=0, columnspan=2, sticky="ew")
        label(heading, "Backup history", kind="section").pack(side="left")
        label(heading, "Newest first", kind="metadata", tone="subtle").pack(side="right")
        self.history_tree = ttk.Treeview(history, columns=("date", "profile", "status"), show="headings", style="ControlMap.Treeview", selectmode="browse")
        for key, title, width in (("date", "Created", 166), ("profile", "Simulator / profile", 180), ("status", "Status", 126)):
            self.history_tree.heading(key, text=title, anchor="w")
            self.history_tree.column(key, width=width, minwidth=85, stretch=True)
        self.history_tree.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(history, command=self.history_tree.yview, style="Slim.Vertical.TScrollbar")
        scroll.grid(row=1, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=scroll.set)
        self.history_tree.bind("<<TreeviewSelect>>", self._history_selected)
        self.history_tree.tag_configure("ready", foreground=COLORS["accent"])
        self.history_tree.tag_configure("invalid", foreground=COLORS["danger"])
        self.history_empty = tk.Frame(history, bg=COLORS["surface"], padx=28, pady=32)
        label(self.history_empty, "No backups yet", kind="section").pack(anchor="w")
        self.history_empty_copy = label(self.history_empty, "Your first applied change will appear here. Each backup includes the original file, a timestamp, and a verified restore receipt.", tone="muted", wrap=380)
        self.history_empty_copy.pack(fill="x", pady=(10, 16))
        self._button(self.history_empty, "Open an existing receipt", self._browse_receipt).pack(anchor="w")
        history_footer = tk.Frame(history, bg=COLORS["surface_alt"], padx=14, pady=12)
        history_footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        label(history_footer, "Backups stay on this PC. Refresh rechecks every receipt.", tone="subtle", kind="secondary", wrap=470).pack(fill="x")

        inspector = panel(workspace, padding=16)
        inspector.grid(row=0, column=1, sticky="nsew")
        self.restore_button = self._button(inspector, "Restore original", self.restore_backup, danger=True)
        self.restore_button.pack(side="bottom", fill="x", pady=(14, 0))
        self._set_button_state(self.restore_button, "disabled")
        detail_view = ScrollFrame(inspector, tone="surface")
        detail_view.pack(fill="both", expand=True)
        detail = detail_view.body
        self._section_header(detail, "Receipt inspector")
        self.restore_info = label(detail, "Select a backup", kind="section", wrap=350)
        self.restore_info.pack(fill="x", pady=(0, 12))
        self.receipt_metadata = tk.StringVar(value="Choose an entry from the history to see its simulator, profile, and creation time.")
        label(detail, variable=self.receipt_metadata, kind="secondary", tone="muted", wrap=350).pack(fill="x")
        divider(detail)
        label(detail, "What changed", kind="label").pack(anchor="w")
        self.receipt_changes = tk.StringVar(value="The receipt records the controls file before and after an apply operation.")
        label(detail, variable=self.receipt_changes, kind="secondary", tone="muted", wrap=350).pack(fill="x", pady=(7, 12))
        label(detail, "Integrity", kind="label").pack(anchor="w")
        self.receipt_integrity = tk.StringVar(value="Select a receipt to verify its backup and current target.")
        label(detail, variable=self.receipt_integrity, kind="secondary", tone="muted", wrap=350).pack(fill="x", pady=(7, 12))
        label(detail, "Receipt location", kind="label").pack(anchor="w")
        entry = ttk.Entry(detail, textvariable=self.receipt_path, width=12)
        entry.pack(fill="x", pady=(7, 8))
        entry.bind("<Return>", lambda e: self._inspect_receipt())
        self.receipt_path.trace_add("write", self._receipt_path_edited)
        self._button(detail, "Inspect receipt", self._inspect_receipt, ghost=True).pack(anchor="w")

        protection = panel(page, padding=12, tone="surface_alt")
        protection.pack(fill="x", pady=(12, 0))
        label(protection, "Protected restore", kind="label").pack(side="left", padx=(0, 20))
        label(protection, "Verified backup  ·  Current-file check  ·  Simulator must be closed", kind="secondary", tone="muted", wrap=650).pack(side="left", fill="x", expand=True)
        protection.pack_forget()
        workspace.pack_forget()
        protection.pack(side="bottom", fill="x", pady=(12, 0))
        workspace.pack(fill="both", expand=True)

    def _receipt_path_edited(self, *_args):
        self._receipt_ready_path = None
        if hasattr(self, "restore_button"):
            self._set_button_state(self.restore_button, "disabled")
            self.restore_info.configure(text="Receipt needs inspection", fg=COLORS["muted"])
            self.receipt_metadata.set("Inspect the selected receipt before restoring.")
            self.receipt_changes.set("Waiting for inspection.")
            self.receipt_integrity.set("Not checked")

    def _backup_root(self):
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "sim-controls-manager" / "backups"

    def _refresh_receipts(self):
        if self._history_loading or self._closing:
            return
        self._history_loading = True
        self._set_button_state(self.history_refresh_button, "disabled")
        self.history_summary.set("Checking backup history…")
        if self.receipt_path.get():
            self._external_receipts.add(self.receipt_path.get())
        root, extra = self._backup_root(), tuple(self._external_receipts)
        result_queue = queue.SimpleQueue()
        def worker():
            try:
                entries, error = discover_history(root, extra), ""
            except (OSError, ValueError) as exc:
                entries, error = (), str(exc)
            result_queue.put((entries, error))
        def poll():
            if self._closing:
                return
            try:
                entries, error = result_queue.get_nowait()
            except queue.Empty:
                self.after(60, poll)
            else:
                self._history_loaded(entries, error)
        threading.Thread(target=worker, daemon=True).start()
        self.after(60, poll)

    def _history_loaded(self, entries, error):
        self._history_loading = False
        self._history_entries = entries
        self._set_button_state(self.history_refresh_button, "normal")
        self._populate_history()
        if error:
            self.history_summary.set("History unavailable")
            self.history_empty_copy.configure(text=error)
        ready = sum(entry.status == "ready" for entry in entries)
        if entries:
            latest = entries[0]
            self.last_backup_summary.set(f"{len(entries)} saved receipts · {ready} ready to restore\nLatest: {latest.simulator}\n{latest.date_label}")
        else:
            self.last_backup_summary.set("No saved receipts found. A verified backup is created with your first applied change.")

    def _populate_history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        chosen = self.history_filter.get()
        filtered = [entry for entry in self._history_entries if chosen == "All simulators" or entry.simulator == chosen]
        self.history_summary.set(f"{len(filtered)} receipt{'s' if len(filtered) != 1 else ''}")
        self._history_by_id = {}
        selected = None
        for index, entry in enumerate(filtered):
            iid = str(index)
            self._history_by_id[iid] = entry
            self.history_tree.insert("", "end", iid=iid, values=(entry.date_label, f"{entry.simulator} / {entry.profile}", STATUS_LABELS[entry.status]), tags=(entry.status,))
            if str(entry.path) == self.receipt_path.get():
                selected = iid
        if filtered:
            self.history_empty.grid_remove()
        else:
            self.history_empty_copy.configure(text="Your first applied change will appear here. You can also open an existing receipt." if not self._history_entries else "No receipts match this simulator. Choose another filter or open a receipt.")
            self.history_empty.grid(row=1, column=0, sticky="new", pady=(44, 0))
        if selected is not None:
            self.history_tree.selection_set(selected)
            self.history_tree.see(selected)

    def _history_selected(self, _event=None):
        selection = self.history_tree.selection()
        if selection and selection[0] in self._history_by_id:
            entry = self._history_by_id[selection[0]]
            self.receipt_path.set(str(entry.path))
            self._inspect_receipt()

    def _inspect_receipt(self):
        self._receipt_ready_path = None
        try:
            preview = preview_restore(self.receipt_path.get())
        except Exception as error:
            self.restore_info.configure(text="Receipt needs attention", fg=COLORS["danger"])
            self.receipt_metadata.set("This receipt cannot be used to restore a controls file.")
            self.receipt_integrity.set(str(error))
            self.receipt_changes.set("Unavailable until the receipt and backup pass validation.")
            self._set_button_state(self.restore_button, "disabled")
            return
        receipt = preview.receipt
        game, profile = target_identity(receipt.originalPath)
        self.restore_info.configure(text=STATUS_LABELS.get(preview.status, preview.status), fg=COLORS["accent"] if preview.status == "ready" else COLORS["warning"])
        from datetime import datetime
        try:
            date = datetime.fromisoformat(receipt.createdAt.replace("Z", "+00:00")).astimezone().strftime("%B %d, %Y at %H:%M")
        except ValueError:
            date = receipt.createdAt
        self.receipt_metadata.set(f"{game} / {profile}\n{date}")
        self.receipt_changes.set(f"Controls file updated\n{receipt.originalPath}\n\nThis receipt stores file snapshots; action-level changes were not recorded.")
        self.receipt_integrity.set(f"✓ Backup matches its SHA-256 receipt\nOriginal: {receipt.originalHash[:16]}…\nApplied:  {receipt.appliedHash[:16]}…\n\n" + {
            "ready": "✓ Current file matches the applied version",
            "already-restored": "The original file is already in place.",
            "changed-since-apply": "The target has changed since apply. Restore is blocked to preserve those changes.",
            "target-missing": "The target file is missing. Restore is blocked.",
        }.get(preview.status, preview.status))
        self._set_button_state(self.restore_button, "normal" if preview.status == "ready" and not self.busy else "disabled")
        if preview.status == "ready":
            self._receipt_ready_path = self.receipt_path.get()

    def _refresh_workspace_status(self):
        if not hasattr(self, "mapping_summary"):
            return
        self.profile_context.set(f"{self.game_name.get()} / {self.profile_name.get() or 'Select a profile'}")
        self.device_context.set(self.device_name.get() or "Select the SimHub virtual controller")
        self.live_status.set("Live sync enabled" if self.auto_refresh.get() else "Live sync paused")
        mapped = len(self.simhub_inspection.bindings) if self.simhub_inspection else 0
        self.sidebar_connection.configure(text=f"●  SimHub · {mapped}/3 roles" if mapped else "○  SimHub not connected", fg=COLORS["accent"] if mapped else COLORS["muted"])
        selected_game = {"acc": "assetto_corsa_competizione", "lmu": "le_mans_ultimate"}.get(self._selected_game_id(), self._selected_game_id())
        for action, widget in self.binding_native.items():
            mapping = NATIVE_CONTROL_NAMES[selected_game][action]
            widget.configure(text=" / ".join(mapping.names) or "Not exposed")
        plan = self.binding_plan
        if plan:
            count = len(plan.changes)
            self.mapping_summary.set(f"{count} pending change{'s' if count != 1 else ''}" if count else "Bindings are in sync")
            self.pending_detail.set(f"{self.game_name.get()} has {count} binding change{'s' if count != 1 else ''} ready for review." if count else "The selected profile matches the supported SimHub targets.")
            self.review_detail.set("Review the highlighted targets. Close the simulator before applying." if count else "No changes are needed for this profile.")
            changed = {change.action_id for change in plan.changes}
            for action, widget in self.binding_states.items():
                unsupported = not NATIVE_CONTROL_NAMES[selected_game][action].names
                widget.configure(text="Unsupported" if unsupported else ("● Will change" if action in changed else "✓ Unchanged"), fg=COLORS["warning"] if unsupported else (COLORS["primary_hover"] if action in changed else COLORS["accent"]))
        else:
            self.mapping_summary.set("Preview required")
            self.pending_detail.set("Refresh the preview to compare this profile with your current SimHub targets.")
            self.review_detail.set("Select a detected profile and controller. Refresh the preview to check changes and conflicts.")
            for widget in self.binding_states.values():
                widget.configure(text="Not compared", fg=COLORS["subtle"])
        try:
            profile = self._selected_profile()
            self.binding_profile_path.configure(text=str(profile.controls_path))
            ready = bool(mapped and self.devices)
        except ValueError:
            ready = False
            self.binding_profile_path.configure(text="No controls file selected. Scan your setup on Overview to discover profiles.")
        self.overview_health.set("Ready to review bindings" if ready else "Setup needs attention")
        self.overview_health_detail.set(self.preview_summary.get() if ready else "Check simulator profiles, SimHub roles, and the virtual controller below.")
        self.health_icon.configure(fg=COLORS["accent"] if ready else COLORS["warning"])
        tiles = sum(not tile.empty for page in self.tablet_layout.pages for tile in page.tiles)
        self.deck_overview.configure(text=f"{len(self.tablet_layout.pages)} pages · {tiles} configured tiles\nActive page: {self._active_deck_page().name}")

    def _record_activity(self, *_args):
        from datetime import datetime
        message = self.footer_status.get()
        if self._activity and self._activity[-1][1] == message:
            return
        self._activity.append((datetime.now().strftime("%H:%M"), message))
        self._activity = self._activity[-100:]
        self.activity_label.configure(text="\n\n".join(f"{time}  {text}" for time, text in reversed(self._activity[-3:])))
