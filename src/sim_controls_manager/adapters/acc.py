"""Assetto Corsa Competizione shortcut-button adapter."""

from __future__ import annotations

import codecs
import ctypes
from ctypes import wintypes
import json
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sim_controls_manager.catalog import ACTION_IDS, Catalog
from sim_controls_manager.file_change import sha256


FOLDERID_DOCUMENTS = "fdd39ad0-238f-46af-adb4-6c85480369c7"
CONTROLS_FILE = Path("Config") / "controls.json"
ACTION_MAP = {
    "pit_limiter": "PitLimiter",
    "tc_increase": "IncreaseTC",
    "tc_decrease": "DecreaseTC",
}
SIM_PROCESS_NAMES = frozenset(("ac2-win64-shipping.exe", "acc.exe"))


class ACCFormatError(ValueError):
    """The selected ACC controls JSON is unsupported or ambiguous."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    acc_directory: Path
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeBinding:
    binding_type: str
    native_button_index: int | None
    device_index: int | None
    instance_guid: str | None
    product_name: str | None


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str
    status: str
    binding: NativeBinding


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    version: int
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


def detect_acc_directory() -> Path | None:
    candidates: list[Path] = []
    documents = _known_folder(FOLDERID_DOCUMENTS)
    if documents is not None:
        candidates.append(documents / "Assetto Corsa Competizione")
    home = Path.home()
    candidates.extend(
        (
            home / "Documents" / "Assetto Corsa Competizione",
            home / "OneDrive" / "Documents" / "Assetto Corsa Competizione",
        )
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(acc_directory: str | Path | None = None) -> DiscoveryResult:
    if acc_directory is None:
        root = detect_acc_directory()
        if root is None:
            raise FileNotFoundError(
                "Could not find Documents\\Assetto Corsa Competizione; "
                "pass --root with its exact path"
            )
    else:
        root = Path(acc_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    controls_path = root / CONTROLS_FILE
    profiles: tuple[ProfileCandidate, ...] = ()
    warnings: tuple[str, ...] = ()
    if controls_path.is_file():
        profiles = (
            ProfileCandidate("Live", controls_path.resolve(), True, "live"),
        )
    else:
        warnings = (f"Live controls file was not found at {controls_path}",)
    return DiscoveryResult(root, profiles, warnings)


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    _text, document, _bom = _decode_controls(profile.controls_path.read_bytes())
    devices = document["commandDevices"]
    actions: list[ActionInspection] = []
    for action_id in ACTION_IDS:
        native_action = ACTION_MAP[action_id]
        matches: list[NativeBinding] = []
        for device_index, device in enumerate(devices):
            for entry in device["raceCommandButtonList"]:
                if entry.get("instantActionCode") == native_action:
                    matches.append(_binding_from_entry(device_index, device, entry))
        binding = matches[0] if matches else _unbound()
        actions.append(ActionInspection(action_id, native_action, "supported", binding))
    return ProfileInspection(profile, document["version"], tuple(actions), True)


def plan_bindings(profile: ProfileCandidate, catalog: Catalog) -> BindingPlan:
    source = profile.controls_path.read_bytes()
    text, document, bom = _decode_controls(source)
    devices = document["commandDevices"]
    device_index = _selected_device_index(devices, catalog)
    device = devices[device_index]
    entries = device["raceCommandButtonList"]

    requested_native = {
        ACTION_MAP[binding.action_id] for binding in catalog.bindings
    }
    desired_claims = {
        binding.virtual_button - 1: ACTION_MAP[binding.action_id]
        for binding in catalog.bindings
    }
    for entry in entries:
        button = entry.get("buttonIndex")
        action = entry.get("instantActionCode")
        if (
            isinstance(button, int)
            and button in desired_claims
            and action != desired_claims[button]
            and action not in requested_native
        ):
            raise ValueError(
                f"button is already assigned to native action {action or 'unknown'}"
            )

    list_start, list_end = _device_button_list_span(text, device_index)
    list_text = text[list_start : list_end + 1]
    object_spans = _array_object_spans(list_text, 0, len(list_text) - 1)
    if len(object_spans) != len(entries):
        raise ACCFormatError("button-list text does not match decoded JSON entries")

    changes: list[BindingChange] = []
    replacements: list[tuple[int, int, str]] = []
    new_entries: list[dict[str, Any]] = []
    for binding in catalog.bindings:
        native_action = ACTION_MAP[binding.action_id]
        desired_button = binding.virtual_button - 1
        matching_indexes = [
            index
            for index, entry in enumerate(entries)
            if entry.get("instantActionCode") == native_action
        ]
        if len(matching_indexes) > 1:
            raise ACCFormatError(
                f"multiple {native_action!r} entries exist on the selected device"
            )
        before = (
            _binding_from_entry(device_index, device, entries[matching_indexes[0]])
            if matching_indexes
            else _unbound()
        )
        after = NativeBinding(
            "button",
            desired_button,
            device_index,
            device["instanceGuid"],
            device["productName"],
        )
        if before == after:
            continue
        changes.append(BindingChange(binding.action_id, native_action, before, after))
        if matching_indexes:
            entry_index = matching_indexes[0]
            start, end = object_spans[entry_index]
            updated = _update_button_entry(list_text[start : end + 1], desired_button)
            replacements.append((start, end + 1, updated))
        else:
            new_entries.append(_new_button_entry(native_action, desired_button))

    for start, end, replacement in sorted(replacements, reverse=True):
        list_text = list_text[:start] + replacement + list_text[end:]
    if new_entries:
        list_text = _append_button_entries(list_text, new_entries, text, list_start)
    next_text = text[:list_start] + list_text + text[list_end + 1 :]
    next_bytes = bom + next_text.encode("utf-8")

    _next_text, verified, _next_bom = _decode_controls(next_bytes)
    selected = verified["commandDevices"][device_index]["raceCommandButtonList"]
    for binding in catalog.bindings:
        native_action = ACTION_MAP[binding.action_id]
        expected_button = binding.virtual_button - 1
        matches = [
            entry
            for entry in selected
            if entry.get("instantActionCode") == native_action
        ]
        if len(matches) != 1 or matches[0].get("buttonIndex") != expected_button:
            raise ACCFormatError(f"planned {native_action} binding failed validation")
    return BindingPlan(profile, sha256(source), next_bytes, tuple(changes))


def validate_controls_bytes(data: bytes) -> bool:
    _decode_controls(data)
    return True


def is_acc_running() -> bool:
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
        raise ACCFormatError(f"controls.json is not valid UTF-8 JSON: {error}") from error
    if not isinstance(value, dict) or value.get("version") != 0:
        raise ACCFormatError("unsupported controls.json root or version")
    devices = value.get("commandDevices")
    if not isinstance(devices, list):
        raise ACCFormatError("commandDevices must be an array")
    for index, device in enumerate(devices):
        if not isinstance(device, dict) or device.get("version") != 0:
            raise ACCFormatError(f"commandDevices[{index}] has an unsupported version")
        for key in ("productName", "instanceGuid"):
            if not isinstance(device.get(key), str):
                raise ACCFormatError(f"commandDevices[{index}].{key} must be a string")
        buttons = device.get("raceCommandButtonList")
        if not isinstance(buttons, list) or not all(
            isinstance(entry, dict) for entry in buttons
        ):
            raise ACCFormatError(
                f"commandDevices[{index}].raceCommandButtonList must be an object array"
            )
    return text, value, bom


def _selected_device_index(devices: list[dict[str, Any]], catalog: Catalog) -> int:
    selected = catalog.virtual_device
    if selected.instance_guid:
        expected = _normalized_guid(selected.instance_guid)
        matches = [
            index
            for index, device in enumerate(devices)
            if _normalized_guid(device["instanceGuid"]) == expected
        ]
        criterion = f"instance GUID {selected.instance_guid}"
    else:
        expected_name = selected.identity.casefold()
        matches = [
            index
            for index, device in enumerate(devices)
            if device["productName"].strip().casefold() == expected_name
        ]
        criterion = f"name {selected.identity!r}"
    if not matches:
        raise ValueError(f"selected virtual controller with {criterion} is not in commandDevices")
    if len(matches) != 1:
        raise ValueError(f"selected virtual controller with {criterion} is ambiguous")
    index = matches[0]
    if bool(devices[index].get("isPedals")):
        raise ValueError("selected device is marked as pedals; choose the SimHub shortcut device")
    return index


def _binding_from_entry(
    device_index: int, device: dict[str, Any], entry: dict[str, Any]
) -> NativeBinding:
    button = entry.get("buttonIndex")
    if not isinstance(button, int) or button < 0:
        return _unbound()
    return NativeBinding(
        "button",
        button,
        device_index,
        device["instanceGuid"],
        device["productName"],
    )


def _unbound() -> NativeBinding:
    return NativeBinding("unbound", None, None, None, None)


def _new_button_entry(native_action: str, button: int) -> dict[str, Any]:
    return {
        "buttonIndex": button,
        "powIndex": -1,
        "powValue": 0,
        "keyName": "None",
        "gamepadButtonName": "None",
        "instantActionCode": native_action,
        "extendedActionCode": "None",
        "extendedTime": 2,
        "pinkieInstanceActionCode": "None",
        "pinkieExtendedActionCode": "None",
    }


def _update_button_entry(object_text: str, button: int) -> str:
    replacements: tuple[tuple[str, str], ...] = (
        ("buttonIndex", str(button)),
        ("powIndex", "-1"),
        ("powValue", "0"),
        ("keyName", '"None"'),
        ("gamepadButtonName", '"None"'),
    )
    updated = object_text
    for key, value in replacements:
        pattern = re.compile(rf'("{re.escape(key)}"\s*:\s*)(?:-?\d+|"(?:\\.|[^"\\])*")')
        updated, count = pattern.subn(lambda match: match.group(1) + value, updated, count=1)
        if count != 1:
            raise ACCFormatError(f"button entry is missing {key}")
    return updated


def _append_button_entries(
    list_text: str,
    entries: list[dict[str, Any]],
    full_text: str,
    list_start: int,
) -> str:
    line_start = full_text.rfind("\n", 0, list_start) + 1
    key_line = full_text[line_start:list_start]
    base_indent = key_line[: len(key_line) - len(key_line.lstrip("\t "))]
    indent_unit = "\t" if "\t" in base_indent or not base_indent else "    "
    item_indent = base_indent + indent_unit
    field_indent = item_indent + indent_unit
    newline = "\r\n" if "\r\n" in full_text else "\n"
    serialized = ("," + newline).join(
        _format_button_entry(entry, item_indent, field_indent, newline)
        for entry in entries
    )
    content = list_text[1:-1]
    if not content.strip():
        return "[" + newline + serialized + newline + base_indent + "]"
    last = len(content.rstrip())
    trailing = content[last:]
    return "[" + content[:last] + "," + newline + serialized + trailing + "]"


def _format_button_entry(
    entry: dict[str, Any], item_indent: str, field_indent: str, newline: str
) -> str:
    fields = []
    for key, value in entry.items():
        fields.append(
            f"{field_indent}{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}"
        )
    return (
        item_indent
        + "{"
        + newline
        + ("," + newline).join(fields)
        + newline
        + item_indent
        + "}"
    )


def _device_button_list_span(text: str, device_index: int) -> tuple[int, int]:
    devices_start = _key_array_start(text, "commandDevices", 0, len(text))
    devices_end = _matching_delimiter(text, devices_start, "[", "]")
    devices = _array_object_spans(text, devices_start, devices_end)
    if device_index >= len(devices):
        raise ACCFormatError("commandDevices text does not match decoded JSON")
    object_start, object_end = devices[device_index]
    list_start = _key_array_start(
        text, "raceCommandButtonList", object_start, object_end + 1
    )
    return list_start, _matching_delimiter(text, list_start, "[", "]")


def _key_array_start(text: str, key: str, start: int, end: int) -> int:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[', text[start:end])
    if match is None:
        raise ACCFormatError(f"JSON key {key!r} was not found")
    absolute = start + match.start()
    return text.find("[", absolute, start + match.end())


def _array_object_spans(text: str, array_start: int, array_end: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = array_start + 1
    while index < array_end:
        character = text[index]
        if character in " \t\r\n,":
            index += 1
            continue
        if character != "{":
            raise ACCFormatError("expected an object inside a JSON array")
        end = _matching_delimiter(text, index, "{", "}")
        spans.append((index, end))
        index = end + 1
    return spans


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
    raise ACCFormatError(f"unterminated JSON {opening}{closing} block")


def _normalized_guid(value: str) -> str:
    return value.strip().strip("{}").casefold()


def _known_folder(folder_id: str) -> Path | None:
    if os.name != "nt":
        return None
    try:
        guid = (ctypes.c_byte * 16)(*uuid.UUID(folder_id).bytes_le)
        path_pointer = ctypes.c_wchar_p()
        if (
            ctypes.windll.shell32.SHGetKnownFolderPath(
                guid, 0, None, ctypes.byref(path_pointer)
            )
            == 0
        ):
            path = Path(path_pointer.value)
            ctypes.windll.ole32.CoTaskMemFree(path_pointer)
            return path
    except (AttributeError, OSError, ValueError):
        return None
    return None
