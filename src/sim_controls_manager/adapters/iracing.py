"""Read-only iRacing controls discovery and GFCC inspection.

The GFCC layout and active-profile rules are adapted from the MIT-licensed
``dillonkirsch/iracing-tracker`` project. See THIRD_PARTY_NOTICES.md.
"""

from __future__ import annotations

import ctypes
import os
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FOLDERID_DOCUMENTS = "fdd39ad0-238f-46af-adb4-6c85480369c7"
PROFILE_DIRECTORY = Path("profiles") / "controls"
RECORD_BODY_LENGTH = 68
ZERO_GUID = b"\x00" * 16

ACTION_MAP = {
    "pit_limiter": "PitSpeedLimiter",
    "tc_increase": "TractionControlInc",
    "tc_decrease": "TractionControlDec",
}
TYPE_NAMES = {0: "unbound", 1: "axis", 2: "button", 4: "key"}
TYPE_IDS = {value: key for key, value in TYPE_NAMES.items()}


class IRacingFormatError(ValueError):
    """The selected controls.cfg is unknown, corrupt, or not lossless."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    iracing_directory: Path
    active_profile: str | None
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NativeBinding:
    binding_type: str
    native_button_index: int | None
    instance_guid: str | None
    product_guid: str | None


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str
    status: str
    binding: NativeBinding | None


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    gfcc_version: int
    controls_version: int
    actions: tuple[ActionInspection, ...]
    roundtrip_verified: bool


def control_profile_in_text(app_ini_text: str) -> str | None:
    """Return ``[ControlProfiles] Global`` from iRacing's app.ini text."""
    section = None
    for raw_line in app_ini_text.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section == "controlprofiles" and "=" in line:
            key, _, value = line.partition("=")
            if key.strip().lower() == "global":
                return value.strip() or None
    return None


def detect_iracing_directory() -> Path | None:
    """Find the iRacing Documents directory, including Known Folder redirection."""
    candidates: list[Path] = []
    documents = _known_folder(FOLDERID_DOCUMENTS)
    if documents is not None:
        candidates.append(documents / "iRacing")
    home = Path.home()
    candidates.extend(
        (
            home / "Documents" / "iRacing",
            home / "OneDrive" / "Documents" / "iRacing",
        )
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(iracing_directory: str | Path | None = None) -> DiscoveryResult:
    """Discover iRacing controls profiles without changing any files."""
    if iracing_directory is None:
        detected = detect_iracing_directory()
        if detected is None:
            raise FileNotFoundError(
                "Could not find Documents\\iRacing; pass --root with its exact path"
            )
        root = detected
    else:
        root = Path(iracing_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)

    active_profile = None
    app_ini = root / "app.ini"
    try:
        active_profile = control_profile_in_text(
            app_ini.read_text(encoding="utf-8-sig", errors="replace")
        )
    except OSError:
        pass

    profiles: list[ProfileCandidate] = []
    warnings: list[str] = []
    profile_root = root / PROFILE_DIRECTORY
    if profile_root.is_dir():
        for directory in sorted(profile_root.iterdir(), key=lambda path: path.name.lower()):
            controls_path = directory / "controls.cfg"
            if directory.is_dir() and controls_path.is_file():
                profiles.append(
                    ProfileCandidate(
                        name=directory.name,
                        controls_path=controls_path.resolve(),
                        active=directory.name == active_profile,
                        layout="control-profile",
                    )
                )
        if active_profile and not any(profile.active for profile in profiles):
            warnings.append(
                f"app.ini selects profile {active_profile!r}, but its controls.cfg was not found"
            )
        if (root / "controls.cfg").is_file():
            warnings.append(
                "A top-level controls.cfg also exists; it is treated as a stale legacy copy"
            )
    else:
        legacy_path = root / "controls.cfg"
        if legacy_path.is_file():
            profiles.append(
                ProfileCandidate(
                    name="Legacy",
                    controls_path=legacy_path.resolve(),
                    active=True,
                    layout="legacy",
                )
            )
        else:
            warnings.append("No controls.cfg was found")

    return DiscoveryResult(
        iracing_directory=root,
        active_profile=active_profile,
        profiles=tuple(profiles),
        warnings=tuple(warnings),
    )


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    """Parse and losslessly round-trip a discovered profile, then inspect actions."""
    data = profile.controls_path.read_bytes()
    document = parse_gfcc(data)
    if build_gfcc(document) != data:
        raise IRacingFormatError(
            "rebuilt controls.cfg differs from the source; refusing inspection"
        )
    entries = {
        entry["name"]: entry for entry in document["controls"]["entries"]
    }
    actions: list[ActionInspection] = []
    for action_id, native_action in ACTION_MAP.items():
        entry = entries.get(native_action)
        if entry is None:
            actions.append(ActionInspection(action_id, native_action, "unknown", None))
            continue
        actions.append(
            ActionInspection(
                action_id,
                native_action,
                "supported",
                _binding_from_entry(entry),
            )
        )
    return ProfileInspection(
        profile=profile,
        gfcc_version=document["header"]["version"],
        controls_version=document["controls"]["version"],
        actions=tuple(actions),
        roundtrip_verified=True,
    )


def parse_gfcc(data: bytes) -> dict[str, Any]:
    """Parse iRacing GFCC bytes while retaining every opaque field."""
    if data[:4] != b"GFCC":
        raise IRacingFormatError("not a controls.cfg: missing GFCC magic")
    if len(data) < 12:
        raise IRacingFormatError("truncated GFCC header")
    gfcc_version, gfcc_size = struct.unpack_from("<II", data, 4)
    if 12 + gfcc_size != len(data):
        raise IRacingFormatError(
            f"GFCC size mismatch: header says {12 + gfcc_size}, file is {len(data)}"
        )
    controls_offset = data.find(b"LRTC", 12)
    if controls_offset < 0:
        raise IRacingFormatError("LRTC chunk not found")
    if controls_offset + 12 > len(data):
        raise IRacingFormatError("truncated LRTC header")
    controls_version, controls_size = struct.unpack_from(
        "<II", data, controls_offset + 4
    )
    controls_end = controls_offset + 12 + controls_size
    if controls_end > len(data):
        raise IRacingFormatError("LRTC payload extends past end of file")
    payload = data[controls_offset + 12 : controls_end]

    entries: list[dict[str, Any]] = []
    position = 0
    while position < len(payload):
        name_end = payload.find(b"\x00", position)
        if name_end < 0:
            raise IRacingFormatError(
                f"unterminated record name at payload offset {position}"
            )
        try:
            name = payload[position:name_end].decode("ascii")
        except UnicodeDecodeError as error:
            raise IRacingFormatError(
                f"non-ASCII record name at payload offset {position}"
            ) from error
        body = payload[name_end + 1 : name_end + 1 + RECORD_BODY_LENGTH]
        if len(body) != RECORD_BODY_LENGTH:
            raise IRacingFormatError(
                f"truncated record body at payload offset {position} ({name})"
            )
        unknown, flags, binding_type, value, modifiers = struct.unpack_from(
            "<5I", body
        )
        entries.append(
            {
                "name": name,
                "unknown": unknown,
                "flags": flags,
                "binding_type": binding_type,
                "value": value,
                "modifiers": modifiers,
                "slots": (body[20:36], body[36:52], body[52:68]),
            }
        )
        position = name_end + 1 + RECORD_BODY_LENGTH

    return {
        "header": {"version": gfcc_version},
        "global_config": data[12:controls_offset],
        "controls": {"version": controls_version, "entries": entries},
        "trailer": data[controls_end:],
    }


def build_gfcc(document: dict[str, Any]) -> bytes:
    """Rebuild parsed GFCC data exactly; used to gate read/write compatibility."""
    records = bytearray()
    for entry in document["controls"]["entries"]:
        try:
            records.extend(entry["name"].encode("ascii"))
        except UnicodeEncodeError as error:
            raise IRacingFormatError(
                f"non-ASCII entry name {entry['name']!r}"
            ) from error
        records.append(0)
        records.extend(
            struct.pack(
                "<5I",
                entry["unknown"],
                entry["flags"],
                entry["binding_type"],
                entry["value"],
                entry["modifiers"],
            )
        )
        for slot in entry["slots"]:
            if not isinstance(slot, bytes) or len(slot) != 16:
                raise IRacingFormatError("GFCC device slots must be exactly 16 bytes")
            records.extend(slot)

    controls = b"LRTC" + struct.pack(
        "<II", document["controls"]["version"], len(records)
    ) + bytes(records)
    payload = document["global_config"] + controls + document["trailer"]
    return b"GFCC" + struct.pack(
        "<II", document["header"]["version"], len(payload)
    ) + payload


def _binding_from_entry(entry: dict[str, Any]) -> NativeBinding:
    binding_type_id = entry["binding_type"]
    binding_type = TYPE_NAMES.get(binding_type_id, f"unknown-{binding_type_id}")
    native_button_index = None
    instance_guid = None
    product_guid = None
    if binding_type_id == 2:
        value = entry["value"]
        if value and value & (value - 1) == 0:
            native_button_index = value.bit_length() - 1
        slots = entry["slots"]
        if slots[1] != ZERO_GUID:
            instance_guid = guid_to_string(slots[1])
        if slots[2] != ZERO_GUID:
            product_guid = guid_to_string(slots[2])
    return NativeBinding(
        binding_type=binding_type,
        native_button_index=native_button_index,
        instance_guid=instance_guid,
        product_guid=product_guid,
    )


def guid_to_string(value: bytes) -> str:
    if len(value) != 16:
        raise IRacingFormatError("GUID must be 16 bytes")
    first, second, third = struct.unpack_from("<IHH", value)
    return (
        f"{first:08X}-{second:04X}-{third:04X}-"
        f"{value[8:10].hex().upper()}-{value[10:].hex().upper()}"
    )


def _known_folder(folder_id: str) -> Path | None:
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
    except Exception:
        pass
    return None
