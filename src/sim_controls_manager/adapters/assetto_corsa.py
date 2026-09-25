"""Lossless Assetto Corsa controls.ini discovery, inspection, and planning."""

from __future__ import annotations

import codecs
import ctypes
from ctypes import wintypes
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from sim_controls_manager.catalog import ACTION_IDS, Catalog
from sim_controls_manager.file_change import sha256


FOLDERID_DOCUMENTS = "fdd39ad0-238f-46af-adb4-6c85480369c7"
LIVE_CONTROLS = Path("cfg") / "controls.ini"
PRESET_DIRECTORY = Path("cfg") / "controllers" / "presets"
ACTION_MAP = {
    "tc_increase": "TCUP",
    "tc_decrease": "TCDN",
}
SIM_PROCESS_NAMES = frozenset(("acs.exe", "assettocorsa.exe"))
_CONTROLLER_NAME = re.compile(r"^CON(\d+)$", re.IGNORECASE)
_CONTROLLER_GUID = re.compile(r"^PGUID(\d+)$", re.IGNORECASE)
_DIRECT_GEAR = re.compile(r"^GEAR_(?:[1-9]|R)$", re.IGNORECASE)


class AssettoCorsaFormatError(ValueError):
    """The selected INI is ambiguous, unsupported, or cannot be rebuilt exactly."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    assetto_corsa_directory: Path
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeBinding:
    binding_type: str
    joy_index: int | None
    native_button_index: int | None
    key: str | None
    xbox_button: str | None


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str | None
    status: str
    binding: NativeBinding | None


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    encoding: str
    actions: tuple[ActionInspection, ...]
    roundtrip_verified: bool


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
    unsupported_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IniDocument:
    encoding: str
    bom: bytes
    lines: tuple[str, ...]
    sections: dict[str, dict[str, int]]


def detect_assetto_corsa_directory() -> Path | None:
    """Find the user's Assetto Corsa documents directory."""

    candidates: list[Path] = []
    documents = _known_folder(FOLDERID_DOCUMENTS)
    if documents is not None:
        candidates.append(documents / "Assetto Corsa")
    home = Path.home()
    candidates.extend(
        (
            home / "Documents" / "Assetto Corsa",
            home / "OneDrive" / "Documents" / "Assetto Corsa",
        )
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(assetto_corsa_directory: str | Path | None = None) -> DiscoveryResult:
    """Discover the live controls file and saved controller presets."""

    if assetto_corsa_directory is None:
        root = detect_assetto_corsa_directory()
        if root is None:
            raise FileNotFoundError(
                "Could not find Documents\\Assetto Corsa; pass --root with its exact path"
            )
    else:
        root = Path(assetto_corsa_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)

    profiles: list[ProfileCandidate] = []
    warnings: list[str] = []
    live_path = root / LIVE_CONTROLS
    if live_path.is_file():
        profiles.append(ProfileCandidate("Live", live_path.resolve(), True, "live"))
    else:
        warnings.append(f"Live controls file was not found at {live_path}")

    preset_root = root / PRESET_DIRECTORY
    if preset_root.is_dir():
        for preset in sorted(preset_root.glob("*.ini"), key=lambda path: path.name.casefold()):
            if preset.is_file():
                profiles.append(
                    ProfileCandidate(preset.stem, preset.resolve(), False, "preset")
                )
    return DiscoveryResult(root, tuple(profiles), tuple(warnings))


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    """Losslessly parse a profile and report the app catalog's three actions."""

    source = profile.controls_path.read_bytes()
    document = parse_controls(source)
    if build_controls(document) != source:
        raise AssettoCorsaFormatError(
            "rebuilt controls.ini differs from the source; refusing inspection"
        )
    actions: list[ActionInspection] = []
    for action_id in ACTION_IDS:
        native_action = ACTION_MAP.get(action_id)
        if native_action is None:
            actions.append(ActionInspection(action_id, None, "unsupported", None))
        elif native_action not in document.sections:
            actions.append(ActionInspection(action_id, native_action, "unknown", None))
        else:
            actions.append(
                ActionInspection(
                    action_id,
                    native_action,
                    "supported",
                    _binding_from_section(document, native_action),
                )
            )
    return ProfileInspection(
        profile,
        "UTF-8" if document.encoding == "utf-8" else "Windows-1252",
        tuple(actions),
        True,
    )


def plan_bindings(profile: ProfileCandidate, catalog: Catalog) -> BindingPlan:
    """Prepare a minimal, byte-preserving patch for supported catalog actions."""

    source = profile.controls_path.read_bytes()
    document = parse_controls(source)
    if build_controls(document) != source:
        raise AssettoCorsaFormatError(
            "source controls.ini did not round-trip byte-exactly"
        )

    requested = tuple(binding.action_id for binding in catalog.bindings)
    unsupported = tuple(action_id for action_id in requested if action_id not in ACTION_MAP)
    supported = tuple(binding for binding in catalog.bindings if binding.action_id in ACTION_MAP)
    if not supported:
        return BindingPlan(profile, sha256(source), source, (), unsupported)

    for binding in supported:
        native_action = ACTION_MAP[binding.action_id]
        _require_action_section(document, native_action)

    if "HEADER" not in document.sections or "INPUT_METHOD" not in document.sections["HEADER"]:
        raise AssettoCorsaFormatError("required [HEADER] INPUT_METHOD is missing")
    input_method = _value(document, "HEADER", "INPUT_METHOD")
    if input_method.casefold() != "wheel":
        raise ValueError(
            f"profile INPUT_METHOD is {input_method!r}; select Wheel controls in "
            "Assetto Corsa before mapping a DirectInput device"
        )

    joy_index = _selected_controller_index(document, catalog)
    desired_claims = {
        (joy_index, binding.virtual_button - 1): ACTION_MAP[binding.action_id]
        for binding in supported
    }
    conflicts: list[str] = []
    target_sections = {ACTION_MAP[binding.action_id] for binding in supported}
    for claim, native_action in _button_claims(document):
        desired_action = desired_claims.get(claim)
        if (
            desired_action is not None
            and native_action != desired_action
            and native_action not in target_sections
        ):
            conflicts.append(
                f"button is already assigned to native action {native_action}"
            )
    if conflicts:
        raise ValueError("; ".join(sorted(set(conflicts))))

    lines = list(document.lines)
    changes: list[BindingChange] = []
    for binding in supported:
        native_action = ACTION_MAP[binding.action_id]
        before = _binding_from_section(document, native_action)
        desired_button = binding.virtual_button - 1
        _replace_value(lines, document, native_action, "JOY", str(joy_index))
        _replace_value(lines, document, native_action, "BUTTON", str(desired_button))
        _replace_value(lines, document, native_action, "KEY", "-1")
        _replace_value(lines, document, native_action, "XBOXBUTTON", "-1")
        after = NativeBinding("button", joy_index, desired_button, None, None)
        if before != after:
            changes.append(BindingChange(binding.action_id, native_action, before, after))

    proposed = IniDocument(document.encoding, document.bom, tuple(lines), document.sections)
    next_bytes = build_controls(proposed)
    reparsed = parse_controls(next_bytes)
    if build_controls(reparsed) != next_bytes:
        raise AssettoCorsaFormatError(
            "planned controls.ini did not round-trip byte-exactly"
        )
    return BindingPlan(
        profile,
        sha256(source),
        next_bytes,
        tuple(changes),
        unsupported,
    )


def parse_controls(data: bytes) -> IniDocument:
    """Parse enough INI structure to patch bindings while retaining every byte."""

    bom = codecs.BOM_UTF8 if data.startswith(codecs.BOM_UTF8) else b""
    payload = data[len(bom) :]
    try:
        text = payload.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = payload.decode("cp1252")
        encoding = "cp1252"

    lines = tuple(text.splitlines(keepends=True))
    if not lines and text:
        lines = (text,)
    sections: dict[str, dict[str, int]] = {}
    current: str | None = None
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith((";", "#")):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            name = stripped[1:-1].strip().upper()
            if not name:
                raise AssettoCorsaFormatError("empty INI section name")
            if name in sections:
                raise AssettoCorsaFormatError(f"duplicate INI section [{name}]")
            sections[name] = {}
            current = name
            continue
        if current is None or "=" not in raw_line:
            continue
        key = raw_line.split("=", 1)[0].strip().upper()
        if not key:
            raise AssettoCorsaFormatError(f"empty key in [{current}]")
        if key in sections[current]:
            raise AssettoCorsaFormatError(f"duplicate key {key} in [{current}]")
        sections[current][key] = index
    if "CONTROLLERS" not in sections:
        raise AssettoCorsaFormatError("required [CONTROLLERS] section is missing")
    return IniDocument(encoding, bom, lines, sections)


def build_controls(document: IniDocument) -> bytes:
    """Rebuild an INI document without normalizing formatting or line endings."""

    return document.bom + "".join(document.lines).encode(document.encoding)


def validate_controls_bytes(data: bytes) -> bool:
    document = parse_controls(data)
    return build_controls(document) == data


def is_assetto_corsa_running() -> bool:
    """Fail closed if Assetto Corsa's game or official launcher is running."""

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


def _require_action_section(document: IniDocument, section: str) -> None:
    if section not in document.sections:
        raise AssettoCorsaFormatError(f"required native action [{section}] is missing")
    required = {"JOY", "BUTTON", "KEY", "XBOXBUTTON"}
    missing = required - document.sections[section].keys()
    if missing:
        raise AssettoCorsaFormatError(
            f"[{section}] is missing required keys: {', '.join(sorted(missing))}"
        )


def _binding_from_section(document: IniDocument, section: str) -> NativeBinding:
    _require_action_section(document, section)
    joy = _integer_value(document, section, "JOY")
    button = _integer_value(document, section, "BUTTON")
    key = _optional_binding_value(_value(document, section, "KEY"))
    xbox = _optional_binding_value(_value(document, section, "XBOXBUTTON"))
    if joy >= 0 and button >= 0:
        return NativeBinding("button", joy, button, key, xbox)
    if key is not None:
        return NativeBinding("key", None, None, key, xbox)
    if xbox is not None:
        return NativeBinding("xbox_button", None, None, None, xbox)
    return NativeBinding("unbound", None, None, None, None)


def _selected_controller_index(document: IniDocument, catalog: Catalog) -> int:
    controller_section = document.sections["CONTROLLERS"]
    names: dict[int, str] = {}
    guids: dict[int, str] = {}
    for key in controller_section:
        name_match = _CONTROLLER_NAME.fullmatch(key)
        guid_match = _CONTROLLER_GUID.fullmatch(key)
        if name_match:
            names[int(name_match.group(1))] = _value(document, "CONTROLLERS", key)
        elif guid_match:
            guids[int(guid_match.group(1))] = _value(document, "CONTROLLERS", key)

    device = catalog.virtual_device
    candidates = set(names) | set(guids)
    if device.product_guid:
        expected_guid = _normalized_guid(device.product_guid)
        candidates = {
            index
            for index in candidates
            if _normalized_guid(guids.get(index, "")) == expected_guid
        }
    else:
        expected_name = device.identity.casefold()
        candidates = {
            index
            for index in candidates
            if names.get(index, "").strip().casefold() == expected_name
        }
    if len(candidates) != 1:
        criterion = (
            f"product GUID {device.product_guid}"
            if device.product_guid
            else f"name {device.identity!r}"
        )
        if not candidates:
            raise ValueError(f"selected virtual controller with {criterion} is not in [CONTROLLERS]")
        raise ValueError(f"selected virtual controller with {criterion} is ambiguous")
    return next(iter(candidates))


def _button_claims(document: IniDocument):
    for section, keys in document.sections.items():
        if "JOY" not in keys or ("BUTTON" not in keys and section != "SHIFTER"):
            continue
        joy = _integer_value(document, section, "JOY")
        if joy < 0:
            continue
        if "BUTTON" in keys:
            button = _integer_value(document, section, "BUTTON")
            if button >= 0:
                yield (joy, button), section
        if section == "SHIFTER":
            for key in keys:
                if _DIRECT_GEAR.fullmatch(key):
                    button = _integer_value(document, section, key)
                    if button >= 0:
                        yield (joy, button), f"SHIFTER/{key}"


def _replace_value(
    lines: list[str], document: IniDocument, section: str, key: str, value: str
) -> None:
    index = document.sections[section][key]
    raw_line = lines[index]
    ending = ""
    for candidate in ("\r\n", "\n", "\r"):
        if raw_line.endswith(candidate):
            ending = candidate
            raw_line = raw_line[: -len(candidate)]
            break
    prefix = raw_line.split("=", 1)[0]
    lines[index] = f"{prefix}={value}{ending}"


def _value(document: IniDocument, section: str, key: str) -> str:
    try:
        line = document.lines[document.sections[section][key]]
    except KeyError as error:
        raise AssettoCorsaFormatError(f"missing {key} in [{section}]") from error
    return line.split("=", 1)[1].strip()


def _integer_value(document: IniDocument, section: str, key: str) -> int:
    value = _value(document, section, key)
    try:
        return int(value)
    except ValueError as error:
        raise AssettoCorsaFormatError(
            f"{key} in [{section}] must be an integer, received {value!r}"
        ) from error


def _optional_binding_value(value: str) -> str | None:
    stripped = value.strip()
    return None if stripped in ("", "-1") else stripped


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
