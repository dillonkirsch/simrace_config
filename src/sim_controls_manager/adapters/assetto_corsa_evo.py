"""Assetto Corsa EVO protobuf-style shortcut adapter."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from sim_controls_manager.catalog import ACTION_IDS, Catalog
from sim_controls_manager.file_change import sha256


FOLDERID_SAVED_GAMES = "4c5c32ff-bb9d-43b0-bf7d-1cdf19b9dbea"
CONTROLS_FILE = Path("input_devices.inputdeviceconfiguration")
ACTION_MAP = {
    "pit_limiter": (138, None, "InputAction_Car_Pit_Limiter_Toggle"),
    # AC EVO represents both directions as payloads of one X_2 action. Its
    # installed paddle mapping establishes payload slots 1/2; which TC
    # direction each slot triggers still requires an in-game verification.
    "tc_increase": (140, 1, "InputAction_Car_TractionControl_Cycle_X_2 [1]"),
    "tc_decrease": (140, 2, "InputAction_Car_TractionControl_Cycle_X_2 [2]"),
}
MAX_DIRECTINPUT_BUTTONS = 128
SIM_PROCESS_NAMES = frozenset(("assettocorsaevo.exe",))


class AssettoCorsaEVOFormatError(ValueError):
    """The selected AC EVO input-device file is unsupported or malformed."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    assetto_corsa_evo_directory: Path
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeBinding:
    binding_type: str
    native_button_index: int | None
    device_index: int | None
    instance_guid: str | None
    product_name: str | None
    payload: int | None


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str
    status: str
    binding: NativeBinding


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    controller_count: int
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


@dataclass(frozen=True, slots=True)
class _Field:
    number: int
    wire_type: int
    raw: bytes
    value: int | bytes


@dataclass(frozen=True, slots=True)
class _Controller:
    top_field: _Field
    payload_fields: tuple[_Field, ...]
    product_name: str
    instance_guid: str
    product_guid: str
    xinput: bool


def detect_assetto_corsa_evo_directory() -> Path | None:
    saved_games = _known_folder(FOLDERID_SAVED_GAMES)
    candidates = []
    if saved_games is not None:
        candidates.append(saved_games / "ACE")
    candidates.append(Path.home() / "Saved Games" / "ACE")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(assetto_corsa_evo_directory: str | Path | None = None) -> DiscoveryResult:
    if assetto_corsa_evo_directory is None:
        root = detect_assetto_corsa_evo_directory()
        if root is None:
            raise FileNotFoundError(
                "Could not find Saved Games\\ACE; pass --root with its exact path"
            )
    else:
        root = Path(assetto_corsa_evo_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)
    path = root / CONTROLS_FILE
    profiles: tuple[ProfileCandidate, ...] = ()
    warnings: tuple[str, ...] = ()
    if path.is_file():
        profiles = (ProfileCandidate("Live", path.resolve(), True, "protobuf"),)
    else:
        warnings = (f"Live device controls were not found at {path}",)
    return DiscoveryResult(root, profiles, warnings)


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    source = profile.controls_path.read_bytes()
    controllers = _decode_controllers(source)
    actions = []
    for action_id in ACTION_IDS:
        action, payload, native_name = ACTION_MAP[action_id]
        matches = _matching_bindings(controllers, action, payload)
        if len(matches) > 1:
            raise AssettoCorsaEVOFormatError(
                f"multiple bindings exist for {native_name}"
            )
        binding = matches[0] if matches else _unbound(payload)
        actions.append(ActionInspection(action_id, native_name, "supported", binding))
    return ProfileInspection(profile, len(controllers), tuple(actions), True)


def plan_bindings(profile: ProfileCandidate, catalog: Catalog) -> BindingPlan:
    source = profile.controls_path.read_bytes()
    top_fields = _parse_message(source)
    controllers = _controllers_from_fields(top_fields)
    selected_index = _selected_controller_index(controllers, catalog)

    desired = {}
    for binding in catalog.bindings:
        if binding.virtual_button > MAX_DIRECTINPUT_BUTTONS:
            raise ValueError(
                f"AC EVO DirectInput supports at most {MAX_DIRECTINPUT_BUTTONS} buttons"
            )
        action, payload, _name = ACTION_MAP[binding.action_id]
        desired[(action, payload)] = binding.virtual_button - 1

    for field in controllers[selected_index].payload_fields:
        if field.number != 2 or field.wire_type != 2:
            continue
        key, button = _command_key_and_button(field.value)
        if button in desired.values() and key not in desired:
            raise ValueError(
                f"button {button + 1} is already assigned to AC EVO action {key[0]}"
            )

    existing: dict[tuple[int, int | None], list[NativeBinding]] = {}
    for key in desired:
        matches = _matching_bindings(controllers, *key)
        if len(matches) > 1:
            raise AssettoCorsaEVOFormatError(
                f"multiple bindings exist for AC EVO action {key[0]} payload {key[1]}"
            )
        existing[key] = matches

    changes = []
    changed_keys: set[tuple[int, int | None]] = set()
    for binding in catalog.bindings:
        action, payload, native_name = ACTION_MAP[binding.action_id]
        key = (action, payload)
        before = existing[key][0] if existing[key] else _unbound(payload)
        controller = controllers[selected_index]
        after = NativeBinding(
            "button",
            binding.virtual_button - 1,
            selected_index,
            controller.instance_guid,
            controller.product_name,
            payload,
        )
        if before != after:
            changes.append(BindingChange(binding.action_id, native_name, before, after))
            changed_keys.add(key)

    if not changes:
        return BindingPlan(profile, sha256(source), source, ())

    rebuilt_controller_payloads: dict[int, bytes] = {}
    for index, controller in enumerate(controllers):
        parts = []
        for field in controller.payload_fields:
            if field.number == 2 and field.wire_type == 2:
                key, _button = _command_key_and_button(field.value)
                if key in changed_keys:
                    continue
            parts.append(field.raw)
        if index == selected_index:
            for binding in catalog.bindings:
                action, payload, _native_name = ACTION_MAP[binding.action_id]
                if (action, payload) in changed_keys:
                    command = _encode_command(action, payload, binding.virtual_button - 1)
                    parts.append(_encode_length_field(2, command))
        rebuilt_controller_payloads[index] = b"".join(parts)

    next_parts = []
    controller_cursor = 0
    for field in top_fields:
        if field.number == 1 and field.wire_type == 2:
            payload = rebuilt_controller_payloads[controller_cursor]
            next_parts.append(_encode_length_field(1, payload))
            controller_cursor += 1
        else:
            next_parts.append(field.raw)
    next_bytes = b"".join(next_parts)

    verified = _decode_controllers(next_bytes)
    for binding in catalog.bindings:
        action, payload, native_name = ACTION_MAP[binding.action_id]
        matches = _matching_bindings(verified, action, payload)
        if (
            len(matches) != 1
            or matches[0].device_index != selected_index
            or matches[0].native_button_index != binding.virtual_button - 1
        ):
            raise AssettoCorsaEVOFormatError(
                f"planned {native_name} binding failed validation"
            )
    return BindingPlan(profile, sha256(source), next_bytes, tuple(changes))


def validate_controls_bytes(data: bytes) -> bool:
    _decode_controllers(data)
    return True


def is_assetto_corsa_evo_running() -> bool:
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
        name = line.strip().strip('"').split('","', 1)[0].casefold()
        if name in SIM_PROCESS_NAMES:
            return True
    return False


def _decode_controllers(data: bytes) -> tuple[_Controller, ...]:
    fields = _parse_message(data)
    if any(field.number != 1 or field.wire_type != 2 for field in fields):
        raise AssettoCorsaEVOFormatError(
            "unsupported InputDeviceConfiguration root fields"
        )
    controllers = _controllers_from_fields(fields)
    if not controllers:
        raise AssettoCorsaEVOFormatError("input-device file has no controllers")
    return controllers


def _controllers_from_fields(fields: tuple[_Field, ...]) -> tuple[_Controller, ...]:
    controllers = []
    for top_field in fields:
        if top_field.number != 1 or top_field.wire_type != 2:
            continue
        payload_fields = _parse_message(top_field.value)
        identity_fields = [
            field for field in payload_fields if field.number == 1 and field.wire_type == 2
        ]
        if len(identity_fields) != 1:
            raise AssettoCorsaEVOFormatError(
                "controller record must contain exactly one identity"
            )
        identity = _parse_message(identity_fields[0].value)
        controllers.append(
            _Controller(
                top_field,
                payload_fields,
                _string_field(identity, 1),
                _string_field(identity, 2),
                _string_field(identity, 5),
                bool(_varint_field(identity, 4, 0)),
            )
        )
    return tuple(controllers)


def _selected_controller_index(
    controllers: tuple[_Controller, ...], catalog: Catalog
) -> int:
    selected = catalog.virtual_device
    matches: list[int] = []
    if selected.instance_guid:
        expected = _normalized_guid(selected.instance_guid)
        matches = [
            index
            for index, controller in enumerate(controllers)
            if controller.instance_guid
            and _normalized_guid(controller.instance_guid) == expected
        ]
    if not matches:
        expected_name = selected.identity.strip().casefold()
        matches = [
            index
            for index, controller in enumerate(controllers)
            if controller.product_name.strip().casefold() == expected_name
        ]
    if not matches:
        raise ValueError(
            f"selected virtual controller {selected.identity!r} is not registered in AC EVO"
        )
    if len(matches) != 1:
        raise ValueError(
            f"selected virtual controller {selected.identity!r} is ambiguous in AC EVO"
        )
    index = matches[0]
    controller = controllers[index]
    if controller.xinput:
        raise ValueError("selected controller is XInput; choose the SimHub DirectInput device")
    if "pedal" in controller.product_name.casefold():
        raise ValueError("selected device appears to be pedals; choose the SimHub shortcut device")
    return index


def _matching_bindings(
    controllers: tuple[_Controller, ...], action: int, payload: int | None
) -> list[NativeBinding]:
    matches = []
    for device_index, controller in enumerate(controllers):
        for field in controller.payload_fields:
            if field.number != 2 or field.wire_type != 2:
                continue
            key, button = _command_key_and_button(field.value)
            if key == (action, payload):
                matches.append(
                    NativeBinding(
                        "button",
                        button,
                        device_index,
                        controller.instance_guid or None,
                        controller.product_name or None,
                        payload,
                    )
                )
    return matches


def _command_key_and_button(data: bytes) -> tuple[tuple[int, int | None], int]:
    fields = _parse_message(data)
    action_fields = [field for field in fields if field.number == 1 and field.wire_type == 2]
    if len(action_fields) != 1:
        raise AssettoCorsaEVOFormatError("device command has no unique ActionBase")
    action_base = _parse_message(action_fields[0].value)
    action = _varint_field(action_base, 1, None)
    if action is None:
        raise AssettoCorsaEVOFormatError("ActionBase has no input action")
    payload_value = _varint_field(action_base, 3, None)
    payload = payload_value if action == 140 else None
    button = _varint_field(fields, 2, 0)
    assert button is not None
    return (action, payload), button


def _encode_command(action: int, payload: int | None, button_index: int) -> bytes:
    action_parts = [_encode_varint_field(1, action)]
    if payload is not None:
        action_parts.extend(
            (
                _encode_varint_field(2, 1),
                _encode_varint_field(3, payload),
                _encode_varint_field(4, (1 << 64) - 1),
            )
        )
    action_parts.append(_encode_varint_field(5, action))
    command = _encode_length_field(1, b"".join(action_parts))
    if button_index:
        command += _encode_varint_field(2, button_index)
    return command


def _parse_message(data: bytes) -> tuple[_Field, ...]:
    fields = []
    offset = 0
    while offset < len(data):
        start = offset
        key, offset = _read_varint(data, offset)
        number = key >> 3
        wire_type = key & 7
        if number == 0:
            raise AssettoCorsaEVOFormatError("protobuf field number cannot be zero")
        if wire_type == 0:
            value, offset = _read_varint(data, offset)
        elif wire_type == 1:
            end = offset + 8
            if end > len(data):
                raise AssettoCorsaEVOFormatError("truncated fixed64 field")
            value = data[offset:end]
            offset = end
        elif wire_type == 2:
            length, offset = _read_varint(data, offset)
            end = offset + length
            if end > len(data):
                raise AssettoCorsaEVOFormatError("truncated length-delimited field")
            value = data[offset:end]
            offset = end
        elif wire_type == 5:
            end = offset + 4
            if end > len(data):
                raise AssettoCorsaEVOFormatError("truncated fixed32 field")
            value = data[offset:end]
            offset = end
        else:
            raise AssettoCorsaEVOFormatError(
                f"unsupported protobuf wire type {wire_type}"
            )
        fields.append(_Field(number, wire_type, data[start:offset], value))
    return tuple(fields)


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise AssettoCorsaEVOFormatError("truncated protobuf varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
    raise AssettoCorsaEVOFormatError("protobuf varint is too long")


def _encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("protobuf varint must be non-negative")
    output = bytearray()
    while value > 0x7F:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _encode_varint_field(number: int, value: int) -> bytes:
    return _encode_varint(number << 3) + _encode_varint(value)


def _encode_length_field(number: int, value: bytes) -> bytes:
    return _encode_varint((number << 3) | 2) + _encode_varint(len(value)) + value


def _string_field(fields: tuple[_Field, ...], number: int) -> str:
    matches = [field for field in fields if field.number == number and field.wire_type == 2]
    if not matches:
        return ""
    if len(matches) != 1:
        raise AssettoCorsaEVOFormatError(f"duplicate controller identity field {number}")
    try:
        return matches[0].value.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssettoCorsaEVOFormatError("controller identity is not UTF-8") from error


def _varint_field(
    fields: tuple[_Field, ...], number: int, default: int | None
) -> int | None:
    matches = [field for field in fields if field.number == number and field.wire_type == 0]
    if not matches:
        return default
    if len(matches) != 1:
        raise AssettoCorsaEVOFormatError(f"duplicate protobuf field {number}")
    assert isinstance(matches[0].value, int)
    return matches[0].value


def _unbound(payload: int | None) -> NativeBinding:
    return NativeBinding("unbound", None, None, None, None, payload)


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
