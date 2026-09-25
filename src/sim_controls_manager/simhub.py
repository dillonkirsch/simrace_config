"""Read-only inspection of SimHub Control Mapper settings."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_RELATIVE = Path(
    "SimHub/PluginsData/Common/ControlMapperPlugin.GeneralSettingsV2.json"
)

ROLE_TO_ACTION = {
    "PitLimiter": "pit_limiter",
    "TractionControl+": "tc_increase",
    "TractionControl-": "tc_decrease",
}


@dataclass(frozen=True, slots=True)
class SimHubBinding:
    action_id: str
    role: str
    virtual_button: int


@dataclass(frozen=True, slots=True)
class SimHubInspection:
    settings_path: Path
    output_mode: int | None
    target_vjoy_id: int | None
    bindings: tuple[SimHubBinding, ...]
    missing_actions: tuple[str, ...]


def default_settings_path() -> Path:
    """Return the normal machine-wide SimHub Control Mapper settings path."""

    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        return Path(program_files_x86) / DEFAULT_SETTINGS_RELATIVE
    return Path("C:/Program Files (x86)") / DEFAULT_SETTINGS_RELATIVE


def inspect_control_mapper(path: Path | None = None) -> SimHubInspection:
    """Read the three core roles without changing SimHub's configuration."""

    settings_path = path or default_settings_path()
    try:
        value = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read SimHub settings at {settings_path}: {error}") from error

    if not isinstance(value, dict):
        raise ValueError("SimHub settings root must be a JSON object")

    output_mode = _optional_nonnegative_int(value.get("OutputMode"), "OutputMode")
    vjoy_mapping = value.get("VJoyMapping")
    if vjoy_mapping is None:
        target_vjoy_id = None
    elif not isinstance(vjoy_mapping, dict):
        raise ValueError("VJoyMapping must be a JSON object")
    else:
        target_vjoy_id = _optional_positive_int(
            vjoy_mapping.get("TargetVJoyId"), "VJoyMapping.TargetVJoyId"
        )

    buttons = _button_mappings(value)
    by_action: dict[str, SimHubBinding] = {}
    for index, mapping in enumerate(buttons):
        if not isinstance(mapping, dict):
            raise ValueError(
                f"OutputMapping.ControllerMapping.Buttons[{index}] must be an object"
            )
        role = mapping.get("TargetRole")
        action_id = ROLE_TO_ACTION.get(role)
        if action_id is None:
            continue
        if action_id in by_action:
            raise ValueError(f"SimHub role {role!r} is mapped more than once")
        button_id = mapping.get("ButtonId")
        if isinstance(button_id, bool) or not isinstance(button_id, int) or button_id < 0:
            raise ValueError(f"SimHub role {role!r} has an invalid ButtonId")
        # SimHub persists ButtonId from zero while its UI and the catalog use one.
        by_action[action_id] = SimHubBinding(action_id, role, button_id + 1)

    bindings = tuple(
        by_action[action_id]
        for action_id in ROLE_TO_ACTION.values()
        if action_id in by_action
    )
    missing = tuple(
        action_id for action_id in ROLE_TO_ACTION.values() if action_id not in by_action
    )
    return SimHubInspection(
        settings_path=settings_path,
        output_mode=output_mode,
        target_vjoy_id=target_vjoy_id,
        bindings=bindings,
        missing_actions=missing,
    )


def _button_mappings(value: dict[str, Any]) -> list[Any]:
    output_mapping = value.get("OutputMapping")
    if not isinstance(output_mapping, dict):
        raise ValueError("OutputMapping must be a JSON object")
    controller_mapping = output_mapping.get("ControllerMapping")
    if not isinstance(controller_mapping, dict):
        raise ValueError("OutputMapping.ControllerMapping must be a JSON object")
    buttons = controller_mapping.get("Buttons")
    if not isinstance(buttons, list):
        raise ValueError("OutputMapping.ControllerMapping.Buttons must be an array")
    return buttons


def _optional_nonnegative_int(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _optional_positive_int(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value
