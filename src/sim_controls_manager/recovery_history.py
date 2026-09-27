"""Read-only receipt discovery for the recovery workspace."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sim_controls_manager.file_change import preview_restore

STATUS_LABELS = {
    "ready": "Ready to restore", "already-restored": "Already restored",
    "changed-since-apply": "File changed", "target-missing": "Target missing",
    "invalid": "Needs attention",
}


@dataclass(frozen=True)
class HistoryEntry:
    path: Path
    created: str
    simulator: str
    profile: str
    target: str
    status: str
    error: str = ""

    @property
    def date_label(self):
        try:
            return datetime.fromisoformat(self.created.replace("Z", "+00:00")).astimezone().strftime("%b %d, %Y  ·  %H:%M")
        except ValueError:
            return "Unknown date"


def target_identity(target: str) -> tuple[str, str]:
    path = Path(target)
    name = path.name.casefold()
    if name == "controls.cfg":
        return "iRacing", path.parent.name if path.parent.parent.name == "controls" else "Legacy"
    if name == "controls.json":
        return "ACC", "Live controls"
    if path.suffix.casefold() == ".ini":
        return "Assetto Corsa", "Live controls" if name == "controls.ini" else path.stem
    if path.suffix.casefold() == ".inputdeviceconfiguration":
        return "Assetto Corsa EVO", "Live controls"
    if path.suffix.casefold() == ".json":
        return "Le Mans Ultimate", path.stem
    return "Unknown simulator", path.name or "Unknown profile"


def inspect_entry(path: Path) -> HistoryEntry:
    created = target = ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            created = data.get("createdAt", "")
            target = data.get("originalPath", "")
            created = created if isinstance(created, str) else ""
            target = target if isinstance(target, str) else ""
        preview = preview_restore(path)
        status, error = preview.status, ""
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        status, error = "invalid", str(exc)
    simulator, profile = target_identity(target)
    return HistoryEntry(path, created, simulator, profile, target, status, error)


def discover_history(root: Path, extra_paths=()) -> tuple[HistoryEntry, ...]:
    paths = set(root.rglob("*-receipt.json")) if root.is_dir() else set()
    paths.update(Path(path) for path in extra_paths if path)
    return tuple(sorted((inspect_entry(path) for path in paths),
                        key=lambda entry: (entry.created, str(entry.path)), reverse=True))
