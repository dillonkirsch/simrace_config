"""Audit mapped native names against the installed control inventory document."""

from __future__ import annotations

import re
from pathlib import Path

from sim_controls_manager.control_names import NATIVE_CONTROL_NAMES


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "CONTROL_INVENTORY.md"


def _section(text: str, start: str, end: str | None = None) -> str:
    value = text.split(start, 1)[1]
    return value.split(end, 1)[0] if end else value


def _code_lines(text: str) -> set[str]:
    lines: set[str] = set()
    for block in re.findall(r"```text\n(.*?)\n```", text, flags=re.DOTALL):
        lines.update(line.strip() for line in block.splitlines() if line.strip())
    return lines


def inventory_names() -> dict[str, set[str]]:
    text = INVENTORY.read_text(encoding="utf-8")
    iracing = _code_lines(
        _section(text, "### Complete action-name union (369)", "## Assetto Corsa")
    )
    assetto_corsa = _code_lines(
        _section(text, "### Sections in the live controls file (44)", "## Assetto Corsa Competizione")
    )
    acc = _code_lines(
        _section(text, "### Complete action-code union currently stored (31)", "## Assetto Corsa EVO")
    )
    ace = _code_lines(
        _section(text, "### Complete embedded InputAction enum (253)", "## Automobilista 2")
    )
    ams2 = _code_lines(
        _section(text, "### Installed control-label union (108)", "## Le Mans Ultimate")
    )
    lmu = _code_lines(_section(text, "### Complete union of preset Input keys (110)"))
    return {
        "iracing": iracing,
        "assetto_corsa": assetto_corsa,
        "assetto_corsa_competizione": acc,
        "assetto_corsa_evo": ace,
        "automobilista_2": ams2,
        "le_mans_ultimate": lmu,
    }


def mapped_native_names(game_id: str) -> set[str]:
    result: set[str] = set()
    for mapping in NATIVE_CONTROL_NAMES[game_id].values():
        for name in mapping.names:
            if game_id == "assetto_corsa":
                match = re.match(r"\[([^]]+)\]", name)
                if match:
                    result.add(match.group(1))
            else:
                result.add(name)
    return result


def remaining_native_names() -> dict[str, set[str]]:
    return {
        game_id: names - mapped_native_names(game_id)
        for game_id, names in inventory_names().items()
    }


def coverage_summary() -> dict[str, object]:
    remaining = remaining_native_names()
    ace = remaining["assetto_corsa_evo"]
    ace_internal_markers = (
        "InputAction_Editor_",
        "InputAction_Dev_",
        "InputAction_AIDev_",
        "InputAction_Terrain_",
        "InputAction_CarDev_",
        "InputAction_Weather_",
        "InputAction_Reload_SelectedDevUiCar",
    )
    ace_internal = {
        name for name in ace if any(marker in name for marker in ace_internal_markers)
    }
    ace_showroom = {name for name in ace if "InputAction_Showroom_" in name}
    ac_metadata = remaining["assetto_corsa"]
    user_facing_by_game = {
        game_id: len(names)
        for game_id, names in remaining.items()
    }
    user_facing_by_game["assetto_corsa"] -= len(ac_metadata)
    user_facing_by_game["assetto_corsa_evo"] -= len(ace_internal | ace_showroom)
    return {
        "remaining_raw": sum(map(len, remaining.values())),
        "non_action_metadata": len(ac_metadata),
        "developer_internal": len(ace_internal),
        "showroom_only": len(ace_showroom),
        "remaining_user_facing": sum(user_facing_by_game.values()),
        "remaining_user_facing_by_game": user_facing_by_game,
    }


def main() -> None:
    inventories = inventory_names()
    remaining = remaining_native_names()
    summary = coverage_summary()
    print("summary:")
    for key, value in summary.items():
        print(f"  {key}={value}")
    for game_id in inventories:
        covered = len(inventories[game_id]) - len(remaining[game_id])
        print(
            f"{game_id}: inventory={len(inventories[game_id])} "
            f"covered={covered} remaining={len(remaining[game_id])}"
        )
        for name in sorted(remaining[game_id]):
            print(f"  {name}")


if __name__ == "__main__":
    main()
