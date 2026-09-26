"""Editable tablet-deck layouts and per-game shortcut suggestions.

The layout is app-owned data.  It deliberately does not claim that a suggested
keyboard shortcut has already been written to a simulator's native controls
file; native adapters remain responsible for verified writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from sim_controls_manager.control_names import CONTROLS, GAMES, NATIVE_CONTROL_NAMES


SCHEMA_VERSION = 1
GRID_PRESETS = ((5, 3), (6, 4), (8, 4), (10, 5))
ICON_NAMES = (
    "gauge",
    "power",
    "starter",
    "headlight",
    "flash",
    "wiper",
    "eye-left",
    "eye-right",
    "pause",
    "reset",
    "mirror",
    "road",
    "plus",
    "minus",
    "dashboard",
    "radio",
    "weather",
    "tools",
    "fuel",
    "tire",
    "chat",
    "replay",
    "camera",
    "chevron-left",
    "chevron-right",
    "target",
)
ACCENT_NAMES = ("blue", "teal", "green", "amber", "red", "purple", "slate")


@dataclass(slots=True)
class DeckTile:
    """One editable square in a tablet deck."""

    action_id: str | None = None
    label: str = ""
    icon: str = "dashboard"
    accent: str = "blue"
    shortcuts: dict[str, str] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return self.action_id is None and not self.label.strip()


@dataclass(slots=True)
class DeckPage:
    """A named, fixed-cell deck page."""

    page_id: str
    name: str
    columns: int = 8
    rows: int = 4
    tiles: list[DeckTile] = field(default_factory=list)

    def __post_init__(self) -> None:
        target = self.columns * self.rows
        if len(self.tiles) < target:
            self.tiles.extend(DeckTile() for _ in range(target - len(self.tiles)))
        elif len(self.tiles) > target:
            del self.tiles[target:]


@dataclass(slots=True)
class DeckLayout:
    """The complete persisted tablet layout."""

    pages: list[DeckPage]
    active_page_id: str
    schema_version: int = SCHEMA_VERSION

    def active_page(self) -> DeckPage:
        for page in self.pages:
            if page.page_id == self.active_page_id:
                return page
        self.active_page_id = self.pages[0].page_id
        return self.pages[0]


def default_layout_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "sim-controls-manager" / "tablet-layout.json"


def _tile(
    action_id: str,
    label: str,
    icon: str,
    accent: str = "blue",
) -> DeckTile:
    if action_id not in CONTROLS:
        raise KeyError(action_id)
    return DeckTile(action_id, label, icon, accent)


def _page(name: str, assignments: dict[int, DeckTile]) -> DeckPage:
    tiles = [DeckTile() for _ in range(32)]
    for index, tile in assignments.items():
        tiles[index] = tile
    return DeckPage(name.casefold().replace(" ", "-"), name, 8, 4, tiles)


def default_layout() -> DeckLayout:
    """Return a useful tablet-first starter layout based on racing workflows."""

    pages = [
        _page(
            "Race",
            {
                0: _tile("pit_limiter", "PIT\nLIMITER", "gauge", "red"),
                1: _tile("ignition", "IGNITION", "power", "green"),
                2: _tile("starter", "START", "starter", "green"),
                3: _tile("headlights", "LIGHTS", "headlight", "green"),
                4: _tile("headlights_flash", "FLASH", "flash", "green"),
                5: _tile("wipers", "WIPERS", "wiper", "purple"),
                6: _tile("look_left", "LOOK\nLEFT", "eye-left"),
                7: _tile("look_right", "LOOK\nRIGHT", "eye-right"),
                8: _tile("pause", "SIM\nPAUSE", "pause", "green"),
                9: _tile("reset_car", "RESET\nCAR", "reset", "purple"),
                10: _tile("virtual_mirror_toggle", "VIRTUAL\nMIRROR", "mirror", "teal"),
                11: _tile("driving_line_toggle", "DRIVING\nLINE", "road", "teal"),
                12: _tile("tc_increase", "TC +", "plus", "amber"),
                13: _tile("tc_decrease", "TC −", "minus", "amber"),
                14: _tile("abs_increase", "ABS +", "plus", "blue"),
                15: _tile("abs_decrease", "ABS −", "minus", "blue"),
                16: _tile("brake_bias_increase", "BIAS\nFORWARD", "plus", "red"),
                17: _tile("brake_bias_decrease", "BIAS\nREAR", "minus", "red"),
                18: _tile("mfd_previous", "PREVIOUS", "chevron-left"),
                19: _tile("mfd_next", "NEXT", "chevron-right"),
                24: _tile("spotter_volume_increase", "SPOTTER\nVOL +", "plus", "teal"),
                25: _tile("spotter_volume_decrease", "SPOTTER\nVOL −", "minus", "teal"),
                26: _tile("spotter_mute", "MUTE\nSPOTTER", "radio", "teal"),
            },
        ),
        _page(
            "Pit",
            {
                0: _tile("pit_request", "PIT\nREQUEST", "tools", "amber"),
                1: _tile("pit_limiter", "PIT\nLIMITER", "gauge", "red"),
                2: _tile("pit_menu_up", "PIT MENU\nUP", "plus", "red"),
                3: _tile("pit_menu_down", "PIT MENU\nDOWN", "minus", "red"),
                4: _tile("pit_menu_increase", "VALUE +", "plus", "red"),
                5: _tile("pit_menu_decrease", "VALUE −", "minus", "red"),
                6: _tile("tearoff_visor", "VISOR\nTEAR OFF", "wiper", "green"),
                8: _tile("fuel_to_end_toggle", "FUEL TO\nEND", "fuel", "amber"),
                9: _tile("fuel_to_end_margin_increase", "FUEL\nMARGIN +", "plus", "amber"),
                10: _tile("fuel_to_end_margin_decrease", "FUEL\nMARGIN −", "minus", "amber"),
                16: _tile("pit_summary_toggle", "PIT\nSUMMARY", "dashboard", "red"),
            },
        ),
        _page(
            "Replay",
            {
                0: _tile("replay_to_start", "JUMP TO\nSTART", "chevron-left"),
                1: _tile("replay_to_end", "JUMP TO\nEND", "chevron-right"),
                2: _tile("replay_previous_session", "PREVIOUS\nSESSION", "chevron-left"),
                3: _tile("replay_next_lap", "NEXT LAP", "replay"),
                4: _tile("replay_previous_incident", "PREVIOUS\nINCIDENT", "chevron-left", "amber"),
                5: _tile("replay_next_incident", "NEXT\nINCIDENT", "chevron-right", "amber"),
                8: _tile("replay_rewind", "REWIND", "chevron-left"),
                9: _tile("replay_frame_rewind", "FRAME\nBACK", "chevron-left"),
                10: _tile("replay_pause_play", "PLAY /\nPAUSE", "replay"),
                11: _tile("replay_frame_advance", "FRAME\nFORWARD", "chevron-right"),
                12: _tile("replay_fast_forward", "FAST\nFORWARD", "chevron-right"),
                16: _tile("replay_rate_increase", "REPLAY\nFASTER", "plus"),
                17: _tile("replay_stop", "STOP", "pause"),
                24: _tile("focus_player_car", "FOCUS\nYOUR CAR", "target"),
                25: _tile("focus_previous_car", "CAR\nPREVIOUS", "chevron-left"),
                26: _tile("focus_next_car", "CAR NEXT", "chevron-right"),
            },
        ),
        _page(
            "Camera",
            {
                0: _tile("fov_increase", "FOV\nINCREASE", "plus"),
                1: _tile("fov_decrease", "FOV\nDECREASE", "minus"),
                2: _tile("seat_up", "DRIVER\nUP", "plus"),
                3: _tile("seat_down", "DRIVER\nDOWN", "minus"),
                4: _tile("recenter_vr", "RECENTER\nVR", "target"),
                8: _tile("ui_scale_increase", "UI SIZE\nINCREASE", "plus", "teal"),
                9: _tile("ui_scale_decrease", "UI SIZE\nDECREASE", "minus", "teal"),
                10: _tile("dash_page_next", "NEXT DASH\nPAGE", "chevron-right"),
                11: _tile("dash_page_previous", "PREVIOUS\nDASH PAGE", "chevron-left"),
                16: _tile("camera_zoom_in", "ZOOM IN", "camera", "teal"),
                17: _tile("camera_zoom_out", "ZOOM OUT", "camera", "teal"),
                18: _tile("camera_view_reset", "RESET\nVIEW", "target", "teal"),
                19: _tile("layout_edit_toggle", "EDIT\nIN-GAME UI", "tools", "teal"),
                24: _tile("screenshot", "SCREENSHOT", "camera", "purple"),
                25: _tile("giant_screenshot", "GIANT\nSCREENSHOT", "camera", "purple"),
                26: _tile("video_capture_toggle", "VIDEO\nSTART/STOP", "camera", "purple"),
            },
        ),
        _page(
            "Chat",
            {
                0: _tile("quick_chat_1", "THANKS!", "chat"),
                2: _tile("quick_chat_2", "SORRY!", "chat"),
                4: _tile("quick_chat_3", "GOOD RACE!", "chat"),
                6: _tile("quick_chat_4", "GOOD LUCK!", "chat"),
                9: _tile("quick_chat_5", "NICE PASS!", "chat"),
                11: _tile("quick_chat_6", "NO PROBLEM", "chat"),
                13: _tile("quick_chat_7", "GO LEFT", "chat"),
                15: _tile("quick_chat_8", "GO RIGHT", "chat"),
                17: _tile("quick_chat_9", "PASS LEFT", "chat"),
                19: _tile("quick_chat_10", "PASS RIGHT", "chat"),
                21: _tile("quick_chat_11", "I'M PITTING", "chat"),
                24: _tile("push_to_talk", "PUSH TO\nTALK", "radio", "green"),
                25: _tile("text_chat", "OPEN CHAT", "chat"),
            },
        ),
    ]
    return DeckLayout(pages, pages[0].page_id)


def shortcut_candidates() -> tuple[str, ...]:
    """Return low-collision virtual keys suitable for tablet-originated input."""

    prefixes = ("", "Ctrl+", "Shift+", "Alt+", "Ctrl+Shift+", "Ctrl+Alt+", "Shift+Alt+")
    return tuple(f"{prefix}F{number}" for prefix in prefixes for number in range(13, 25))


def control_is_available(game_id: str, action_id: str) -> bool:
    mapping = NATIVE_CONTROL_NAMES[game_id][action_id]
    return bool(mapping.names) and mapping.status != "not_exposed"


def suggest_shortcut(game_id: str, used: set[str]) -> str | None:
    """Choose the first case-insensitively unused low-collision shortcut."""

    if game_id not in GAMES:
        raise KeyError(game_id)
    folded = {value.strip().casefold() for value in used if value.strip()}
    for candidate in shortcut_candidates():
        if candidate.casefold() not in folded:
            return candidate
    return None


def assign_missing_shortcuts(layout: DeckLayout) -> int:
    """Fill blank per-game shortcuts without overwriting existing assignments.

    The same action receives the same shortcut everywhere it appears.  Only
    controls with an observed native action are assigned.
    """

    assigned = 0
    tiles = [tile for page in layout.pages for tile in page.tiles if tile.action_id]
    for game_id in GAMES:
        by_action: dict[str, str] = {}
        used: set[str] = set()
        for tile in tiles:
            value = tile.shortcuts.get(game_id, "").strip()
            if value:
                used.add(value)
                by_action.setdefault(tile.action_id or "", value)

        for tile in tiles:
            action_id = tile.action_id
            if action_id is None or not control_is_available(game_id, action_id):
                continue
            if tile.shortcuts.get(game_id, "").strip():
                continue
            shortcut = by_action.get(action_id)
            if shortcut is None:
                shortcut = suggest_shortcut(game_id, used)
                if shortcut is None:
                    continue
                by_action[action_id] = shortcut
                used.add(shortcut)
            tile.shortcuts[game_id] = shortcut
            assigned += 1
    return assigned


def resize_page(page: DeckPage, columns: int, rows: int) -> list[DeckTile]:
    """Resize a page, returning non-empty tiles that did not fit."""

    if (columns, rows) not in GRID_PRESETS:
        raise ValueError("unsupported deck grid size")
    old_tiles = list(page.tiles)
    capacity = columns * rows
    kept = old_tiles[:capacity]
    overflow = [tile for tile in old_tiles[capacity:] if not tile.empty]
    if len(kept) < capacity:
        kept.extend(DeckTile() for _ in range(capacity - len(kept)))
    page.columns = columns
    page.rows = rows
    page.tiles = kept
    return overflow


def swap_tiles(page: DeckPage, first: int, second: int) -> None:
    if not (0 <= first < len(page.tiles) and 0 <= second < len(page.tiles)):
        raise IndexError("deck tile index out of range")
    page.tiles[first], page.tiles[second] = page.tiles[second], page.tiles[first]


def add_page(layout: DeckLayout, name: str, columns: int = 8, rows: int = 4) -> DeckPage:
    name = name.strip() or f"Page {len(layout.pages) + 1}"
    page = DeckPage(uuid4().hex, name, columns, rows)
    layout.pages.append(page)
    layout.active_page_id = page.page_id
    return page


def delete_page(layout: DeckLayout, page_id: str) -> None:
    if len(layout.pages) == 1:
        raise ValueError("a layout must contain at least one page")
    layout.pages = [page for page in layout.pages if page.page_id != page_id]
    if layout.active_page_id == page_id:
        layout.active_page_id = layout.pages[0].page_id


def layout_to_dict(layout: DeckLayout) -> dict[str, Any]:
    return {
        "schemaVersion": layout.schema_version,
        "activePageId": layout.active_page_id,
        "pages": [
            {
                "id": page.page_id,
                "name": page.name,
                "columns": page.columns,
                "rows": page.rows,
                "tiles": [
                    {
                        "actionId": tile.action_id,
                        "label": tile.label,
                        "icon": tile.icon,
                        "accent": tile.accent,
                        "shortcuts": dict(sorted(tile.shortcuts.items())),
                    }
                    for tile in page.tiles
                ],
            }
            for page in layout.pages
        ],
    }


def layout_from_dict(value: Any) -> DeckLayout:
    if not isinstance(value, dict) or value.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"tablet layout schemaVersion must be {SCHEMA_VERSION}")
    raw_pages = value.get("pages")
    if not isinstance(raw_pages, list) or not raw_pages:
        raise ValueError("tablet layout must contain at least one page")

    pages: list[DeckPage] = []
    page_ids: set[str] = set()
    for raw_page in raw_pages:
        if not isinstance(raw_page, dict):
            raise ValueError("tablet layout page must be an object")
        page_id = raw_page.get("id")
        name = raw_page.get("name")
        columns = raw_page.get("columns")
        rows = raw_page.get("rows")
        if not isinstance(page_id, str) or not page_id or page_id in page_ids:
            raise ValueError("tablet layout page ids must be unique non-empty strings")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tablet layout page names must be non-empty strings")
        if (columns, rows) not in GRID_PRESETS:
            raise ValueError("tablet layout page uses an unsupported grid size")
        raw_tiles = raw_page.get("tiles")
        if not isinstance(raw_tiles, list) or len(raw_tiles) != columns * rows:
            raise ValueError("tablet layout tile count does not match its grid")
        tiles: list[DeckTile] = []
        for raw_tile in raw_tiles:
            if not isinstance(raw_tile, dict):
                raise ValueError("tablet layout tile must be an object")
            action_id = raw_tile.get("actionId")
            if action_id is not None and action_id not in CONTROLS:
                raise ValueError(f"tablet layout contains unknown action {action_id!r}")
            label = raw_tile.get("label", "")
            icon = raw_tile.get("icon", "dashboard")
            accent = raw_tile.get("accent", "blue")
            shortcuts = raw_tile.get("shortcuts", {})
            if not isinstance(label, str) or not isinstance(shortcuts, dict):
                raise ValueError("tablet tile label and shortcuts have invalid types")
            if icon not in ICON_NAMES or accent not in ACCENT_NAMES:
                raise ValueError("tablet tile icon or accent is unsupported")
            clean_shortcuts: dict[str, str] = {}
            for game_id, shortcut in shortcuts.items():
                if game_id not in GAMES or not isinstance(shortcut, str):
                    raise ValueError("tablet tile contains an invalid game shortcut")
                if shortcut.strip():
                    clean_shortcuts[game_id] = shortcut.strip()
            tiles.append(DeckTile(action_id, label, icon, accent, clean_shortcuts))
        page_ids.add(page_id)
        pages.append(DeckPage(page_id, name.strip(), columns, rows, tiles))

    active_page_id = value.get("activePageId")
    if active_page_id not in page_ids:
        active_page_id = pages[0].page_id
    return DeckLayout(pages, active_page_id)


def load_layout(path: Path | None = None) -> DeckLayout:
    layout_path = path or default_layout_path()
    if not layout_path.is_file():
        return default_layout()
    try:
        value = json.loads(layout_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read tablet layout at {layout_path}: {error}") from error
    return layout_from_dict(value)


def save_layout(layout: DeckLayout, path: Path | None = None) -> Path:
    layout_path = path or default_layout_path()
    layout_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = layout_path.with_suffix(layout_path.suffix + ".tmp")
    payload = json.dumps(layout_to_dict(layout), indent=2, ensure_ascii=False) + "\n"
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(layout_path)
    return layout_path
