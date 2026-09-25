"""Le Mans Ultimate controller-preset shortcut adapter."""

from __future__ import annotations

import codecs
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sim_controls_manager.catalog import ACTION_IDS, Catalog
from sim_controls_manager.file_change import sha256


PRESET_DIRECTORY = Path("UserData") / "Controller" / "Presets"
ACTION_MAP = {
    "pit_limiter": "Speed Limiter",
    "tc_increase": "Traction Control Up",
    "tc_decrease": "Traction Control Down",
}
BUTTON_ID_OFFSET = 32
SIM_PROCESS_NAMES = frozenset(
    ("le mans ultimate.exe", "launch le mans ultimate.exe")
)


class LeMansUltimateFormatError(ValueError):
    """The selected LMU controller preset is unsupported or ambiguous."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    lmu_directory: Path
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeBinding:
    binding_type: str
    native_id: int | None
    virtual_button: int | None
    device_key: str | None
    instance_name: str | None


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str
    status: str
    binding: NativeBinding


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    input_type: str
    actions: tuple[ActionInspection, ...]
    source_verified: bool


@dataclass(frozen=True, slots=True)
class BindingChange:
    action_id: str
    native_action: str
    before: NativeBinding
    after: NativeBinding


@dataclass(frozen=True, slots=True)
class BindingPlan:
    profile: ProfileCandidate
    source_hash: str
    next_bytes: bytes
    changes: tuple[BindingChange, ...]
    unsupported_actions: tuple[str, ...] = ()


def detect_lmu_directory() -> Path | None:
    candidates: list[Path] = []
    for variable in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        value = os.environ.get(variable)
        if value:
            candidates.append(
                Path(value) / "Steam" / "steamapps" / "common" / "Le Mans Ultimate"
            )
    candidates.append(
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate")
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(lmu_directory: str | Path | None = None) -> DiscoveryResult:
    if lmu_directory is None:
        root = detect_lmu_directory()
        if root is None:
            raise FileNotFoundError(
                "Could not find the Le Mans Ultimate install; pass --root with its exact path"
            )
    else:
        root = Path(lmu_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    preset_directory = root / PRESET_DIRECTORY
    profiles: list[ProfileCandidate] = []
    warnings: list[str] = []
    skipped = 0
    if preset_directory.is_dir():
        candidates = (
            path for path in preset_directory.iterdir() if path.suffix.casefold() == ".json"
        )
        for path in sorted(candidates, key=lambda item: item.name.casefold()):
            if _looks_like_directinput_preset(path):
                profiles.append(ProfileCandidate(path.stem, path.resolve(), False, "preset"))
            else:
                skipped += 1
    else:
        warnings.append(f"Controller preset folder was not found at {preset_directory}")
    if preset_directory.is_dir() and not profiles:
        warnings.append(f"No controller JSON presets were found at {preset_directory}")
    if skipped:
        warnings.append(
            f"Skipped {skipped} keyboard/gamepad preset{'s' if skipped != 1 else ''}; "
            "only DirectInput controller presets can be edited"
        )
    return DiscoveryResult(root, tuple(profiles), tuple(warnings))


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    _text, document, _bom = _decode_controls(profile.controls_path.read_bytes())
    actions: list[ActionInspection] = []
    inputs = document["Input"]
    devices = document["Devices"]
    for action_id in ACTION_IDS:
        native_action = ACTION_MAP[action_id]
        entry = inputs.get(native_action)
        binding = _binding_from_entry(entry, devices) if entry is not None else _unbound()
        actions.append(ActionInspection(action_id, native_action, "supported", binding))
    return ProfileInspection(profile, document["Type"], tuple(actions), True)


def plan_bindings(profile: ProfileCandidate, catalog: Catalog) -> BindingPlan:
    source = profile.controls_path.read_bytes()
    text, document, bom = _decode_controls(source)
    inputs = document["Input"]
    devices = document["Devices"]
    device_key, device = _selected_device(devices, catalog)
    button_count = device.get("layout", {}).get("buttons")
    largest_button = max(binding.virtual_button for binding in catalog.bindings)
    if not isinstance(button_count, int) or button_count <= 0:
        raise ValueError("selected device does not expose shortcut buttons")
    if largest_button > button_count:
        raise ValueError(
            f"selected device exposes {button_count} buttons, but button {largest_button} was requested"
        )

    target_actions = {ACTION_MAP[binding.action_id] for binding in catalog.bindings}
    desired_ids = {
        BUTTON_ID_OFFSET + binding.virtual_button - 1: ACTION_MAP[binding.action_id]
        for binding in catalog.bindings
    }
    for action, entry in inputs.items():
        if not isinstance(entry, dict):
            continue
        native_id = entry.get("id")
        if (
            entry.get("device") == device_key
            and native_id in desired_ids
            and action != desired_ids[native_id]
            and action not in target_actions
        ):
            raise ValueError(
                f"button {native_id - BUTTON_ID_OFFSET + 1} is already assigned to native action {action}"
            )

    input_start = _key_object_start(text, "Input", 0, len(text))
    input_end = _matching_delimiter(text, input_start, "{", "}")
    input_text = text[input_start : input_end + 1]
    replacements: list[tuple[int, int, str]] = []
    additions: list[tuple[str, str, int]] = []
    changes: list[BindingChange] = []
    for binding in catalog.bindings:
        native_action = ACTION_MAP[binding.action_id]
        native_id = BUTTON_ID_OFFSET + binding.virtual_button - 1
        old_entry = inputs.get(native_action)
        before = _binding_from_entry(old_entry, devices) if old_entry is not None else _unbound()
        after = NativeBinding(
            "button", native_id, binding.virtual_button, device_key, device["instance name"]
        )
        if before == after:
            continue
        changes.append(BindingChange(binding.action_id, native_action, before, after))
        if old_entry is None:
            additions.append((native_action, device_key, native_id))
        else:
            start = _property_object_start(input_text, native_action)
            end = _matching_delimiter(input_text, start, "{", "}")
            replacements.append(
                (start, end + 1, _update_input_entry(input_text[start : end + 1], device_key, native_id))
            )

    for start, end, replacement in sorted(replacements, reverse=True):
        input_text = input_text[:start] + replacement + input_text[end:]
    if additions:
        input_text = _append_input_entries(input_text, additions, text, input_start)
    next_text = text[:input_start] + input_text + text[input_end + 1 :]
    next_bytes = bom + next_text.encode("utf-8")

    _next_text, verified, _next_bom = _decode_controls(next_bytes)
    for binding in catalog.bindings:
        native_action = ACTION_MAP[binding.action_id]
        entry = verified["Input"].get(native_action)
        expected = BUTTON_ID_OFFSET + binding.virtual_button - 1
        if not isinstance(entry, dict) or entry.get("device") != device_key or entry.get("id") != expected:
            raise LeMansUltimateFormatError(
                f"planned {native_action} binding failed validation"
            )
    return BindingPlan(profile, sha256(source), next_bytes, tuple(changes))


def validate_controls_bytes(data: bytes) -> bool:
    _decode_controls(data)
    return True


def _looks_like_directinput_preset(path: Path) -> bool:
    try:
        data = path.read_bytes()
        bom = codecs.BOM_UTF8 if data.startswith(codecs.BOM_UTF8) else b""
        value = json.loads(data[len(bom) :].decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("Type") == "Direct Input"
        and isinstance(value.get("Devices"), dict)
        and isinstance(value.get("Input"), dict)
    )


def is_lmu_running() -> bool:
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ("tasklist", "/FO", "CSV", "/NH"),
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return True
    if result.returncode != 0:
        return True
    for line in result.stdout.splitlines():
        process_name = line.strip().strip('"').split('","', 1)[0].casefold()
        if process_name in SIM_PROCESS_NAMES:
            return True
    return False


def _decode_controls(data: bytes) -> tuple[str, dict[str, Any], bytes]:
    bom = codecs.BOM_UTF8 if data.startswith(codecs.BOM_UTF8) else b""
    try:
        text = data[len(bom) :].decode("utf-8")
        value = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LeMansUltimateFormatError(f"preset is not valid UTF-8 JSON: {error}") from error
    if not isinstance(value, dict):
        raise LeMansUltimateFormatError("preset root must be an object")
    if not isinstance(value.get("Type"), str):
        raise LeMansUltimateFormatError("preset Type must be a string")
    devices = value.get("Devices")
    inputs = value.get("Input")
    if not isinstance(devices, dict) or not isinstance(inputs, dict):
        raise LeMansUltimateFormatError("preset Devices and Input must be objects")
    for key, device in devices.items():
        if not isinstance(key, str) or not isinstance(device, dict):
            raise LeMansUltimateFormatError("preset Devices entries must be objects")
        if not isinstance(device.get("instance name"), str):
            raise LeMansUltimateFormatError(f"device {key!r} has no instance name")
    for action, entry in inputs.items():
        if (
            not isinstance(action, str)
            or not isinstance(entry, dict)
            or not isinstance(entry.get("device"), str)
            or not isinstance(entry.get("id"), int)
        ):
            raise LeMansUltimateFormatError(f"Input entry {action!r} is malformed")
    return text, value, bom


def _selected_device(
    devices: dict[str, dict[str, Any]], catalog: Catalog
) -> tuple[str, dict[str, Any]]:
    expected = catalog.virtual_device.identity.strip().casefold()
    matches = [
        (key, device)
        for key, device in devices.items()
        if device["instance name"].strip().casefold() == expected
    ]
    if not matches:
        raise ValueError(
            f"selected virtual controller named {catalog.virtual_device.identity!r} is not in this preset"
        )
    if len(matches) != 1:
        raise ValueError(
            f"selected virtual controller named {catalog.virtual_device.identity!r} is ambiguous"
        )
    key, device = matches[0]
    device_type = str(device.get("Type", "")).casefold()
    if "pedal" in device_type:
        raise ValueError("selected device is marked as pedals; choose the SimHub shortcut device")
    return key, device


def _binding_from_entry(
    entry: Any, devices: dict[str, dict[str, Any]]
) -> NativeBinding:
    if not isinstance(entry, dict):
        return _unbound()
    native_id = entry.get("id")
    device_key = entry.get("device")
    if not isinstance(native_id, int) or not isinstance(device_key, str):
        return _unbound()
    device = devices.get(device_key)
    instance_name = device.get("instance name") if isinstance(device, dict) else None
    virtual_button = native_id - BUTTON_ID_OFFSET + 1 if native_id >= BUTTON_ID_OFFSET else None
    return NativeBinding(
        "button" if virtual_button is not None else "other",
        native_id,
        virtual_button,
        device_key,
        instance_name if isinstance(instance_name, str) else None,
    )


def _unbound() -> NativeBinding:
    return NativeBinding("unbound", None, None, None, None)


def _update_input_entry(object_text: str, device_key: str, native_id: int) -> str:
    device_pattern = re.compile(r'("device"\s*:\s*)"(?:\\.|[^"\\])*"')
    updated, count = device_pattern.subn(
        lambda match: match.group(1) + json.dumps(device_key, ensure_ascii=False),
        object_text,
        count=1,
    )
    if count != 1:
        raise LeMansUltimateFormatError("Input entry is missing device")
    id_pattern = re.compile(r'("id"\s*:\s*)-?\d+')
    updated, count = id_pattern.subn(
        lambda match: match.group(1) + str(native_id), updated, count=1
    )
    if count != 1:
        raise LeMansUltimateFormatError("Input entry is missing id")
    return updated


def _append_input_entries(
    object_text: str,
    entries: list[tuple[str, str, int]],
    full_text: str,
    object_start: int,
) -> str:
    line_start = full_text.rfind("\n", 0, object_start) + 1
    key_line = full_text[line_start:object_start]
    base_indent = key_line[: len(key_line) - len(key_line.lstrip("\t "))]
    indent_unit = "\t" if "\t" in base_indent or not base_indent else "    "
    item_indent = base_indent + indent_unit
    field_indent = item_indent + indent_unit
    newline = "\r\n" if "\r\n" in full_text else "\n"
    serialized_items = []
    for action, device_key, native_id in entries:
        serialized_items.append(
            item_indent
            + json.dumps(action, ensure_ascii=False)
            + ": {"
            + newline
            + field_indent
            + '"device": '
            + json.dumps(device_key, ensure_ascii=False)
            + ","
            + newline
            + field_indent
            + '"id": '
            + str(native_id)
            + newline
            + item_indent
            + "}"
        )
    serialized = ("," + newline).join(serialized_items)
    content = object_text[1:-1]
    if not content.strip():
        return "{" + newline + serialized + newline + base_indent + "}"
    last = len(content.rstrip())
    trailing = content[last:]
    return "{" + content[:last] + "," + newline + serialized + trailing + "}"


def _key_object_start(text: str, key: str, start: int, end: int) -> int:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\{{', text[start:end])
    if match is None:
        raise LeMansUltimateFormatError(f"JSON key {key!r} was not found")
    absolute = start + match.start()
    return text.find("{", absolute, start + match.end())


def _property_object_start(object_text: str, key: str) -> int:
    return _key_object_start(object_text, key, 0, len(object_text))


def _matching_delimiter(text: str, start: int, opening: str, closing: str) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return index
    raise LeMansUltimateFormatError(f"unterminated JSON {opening}{closing} block")
