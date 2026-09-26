"""Read-only Automobilista 2 controller-settings adapter.

AMS2 stores controller profiles in a Twofish-encrypted ``.sav`` container.  This
module deliberately stops at container validation and discovery: without a
verified decoder, checksum algorithm, and controlled before/after samples, a
binding write cannot meet the project's lossless-update requirements.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from sim_controls_manager.catalog import ACTION_IDS, Catalog


FOLDERID_DOCUMENTS = "fdd39ad0-238f-46af-adb4-6c85480369c7"
SAVEGAME_DIRECTORY = "savegame"
GAME_DIRECTORY = "automobilista 2"
PROFILES_DIRECTORY = "profiles"
CONTROLLER_FILE_PATTERN = "*.controllersettings.v*.sav"
CONTAINER_HEADER_SIZE = 8
ENCRYPTED_BLOCK_SIZE = 16
CIPHER_NAME = "Twofish"
ACTION_MAP = {
    "pit_limiter": "Toggle Pit Speed Limiter",
    "tc_increase": "Onboard Traction Control Increase",
    "tc_decrease": "Onboard Traction Control Decrease",
}


class Automobilista2FormatError(ValueError):
    """The selected AMS2 controller save is malformed or unsupported."""


@dataclass(frozen=True, slots=True)
class ProfileCandidate:
    name: str
    controls_path: Path
    active: bool
    layout: str
    account_id: str
    format_version: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    automobilista_2_directory: Path
    profiles: tuple[ProfileCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContainerInfo:
    header_word: int
    declared_length: int
    encrypted_length: int
    padding_length: int
    encrypted_blocks: int
    repeated_blocks: int


@dataclass(frozen=True, slots=True)
class ActionInspection:
    action_id: str
    native_action: str
    status: str
    binding: None = None


@dataclass(frozen=True, slots=True)
class ProfileInspection:
    profile: ProfileCandidate
    container: ContainerInfo
    actions: tuple[ActionInspection, ...]
    source_verified: bool
    write_supported: bool


def detect_automobilista_2_directory() -> Path | None:
    """Return the first existing Documents-based AMS2 data directory."""

    candidates: list[Path] = []
    documents = _known_folder(FOLDERID_DOCUMENTS)
    if documents is not None:
        candidates.append(documents / "Automobilista 2")
    home = Path.home()
    candidates.extend(
        (
            home / "Documents" / "Automobilista 2",
            home / "OneDrive" / "Documents" / "Automobilista 2",
        )
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def discover(
    automobilista_2_directory: str | Path | None = None,
) -> DiscoveryResult:
    """Discover every account's controller-settings container without writing."""

    if automobilista_2_directory is None:
        root = detect_automobilista_2_directory()
        if root is None:
            raise FileNotFoundError(
                "Could not find Documents\\Automobilista 2; pass --root with its exact path"
            )
    else:
        root = Path(automobilista_2_directory).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)

    savegame = root / SAVEGAME_DIRECTORY
    profiles: list[ProfileCandidate] = []
    warnings: list[str] = []
    if savegame.is_dir():
        for account_directory in sorted(
            (item for item in savegame.iterdir() if item.is_dir()),
            key=lambda item: item.name.casefold(),
        ):
            profiles_directory = (
                account_directory / GAME_DIRECTORY / PROFILES_DIRECTORY
            )
            if not profiles_directory.is_dir():
                continue
            for path in sorted(
                profiles_directory.glob(CONTROLLER_FILE_PATTERN),
                key=lambda item: item.name.casefold(),
            ):
                match = re.fullmatch(
                    r"(?P<profile>.+)\.controllersettings\.v(?P<version>[0-9.]+)\.sav",
                    path.name,
                    flags=re.IGNORECASE,
                )
                if match is None:
                    continue
                profile_name = match.group("profile")
                profiles.append(
                    ProfileCandidate(
                        name=f"{account_directory.name}/{profile_name}",
                        controls_path=path.resolve(),
                        active=False,
                        layout="twofish-save",
                        account_id=account_directory.name,
                        format_version=match.group("version"),
                    )
                )
    else:
        warnings.append(f"Savegame folder was not found at {savegame}")

    if savegame.is_dir() and not profiles:
        warnings.append(f"No controller-settings saves were found below {savegame}")
    if profiles:
        warnings.append(
            "AMS2 does not expose the active in-game controller slot in a verified "
            "external format; discovered saves are read-only"
        )
    if len({profile.account_id for profile in profiles}) > 1:
        warnings.append(
            "Multiple AMS2 account directories were found; choose the account explicitly"
        )
    return DiscoveryResult(root, tuple(profiles), tuple(warnings))


def inspect_profile(profile: ProfileCandidate) -> ProfileInspection:
    """Validate the encrypted container and report the write-gated actions."""

    container = analyze_container(profile.controls_path.read_bytes())
    actions = tuple(
        ActionInspection(action_id, ACTION_MAP[action_id], "format_locked")
        for action_id in ACTION_IDS
    )
    return ProfileInspection(profile, container, actions, False, False)


def analyze_container(data: bytes) -> ContainerInfo:
    """Validate structural facts that do not require decrypting the save payload."""

    if len(data) < CONTAINER_HEADER_SIZE + ENCRYPTED_BLOCK_SIZE:
        raise Automobilista2FormatError("controller save is too short")
    header_word, declared_length = struct.unpack_from("<II", data)
    encrypted = data[CONTAINER_HEADER_SIZE:]
    if len(encrypted) % ENCRYPTED_BLOCK_SIZE:
        raise Automobilista2FormatError(
            "encrypted payload length is not a multiple of 16 bytes"
        )
    padding_length = len(encrypted) - declared_length
    if not 1 <= padding_length <= ENCRYPTED_BLOCK_SIZE:
        raise Automobilista2FormatError(
            "declared payload length is inconsistent with the encrypted container"
        )
    blocks = tuple(
        encrypted[offset : offset + ENCRYPTED_BLOCK_SIZE]
        for offset in range(0, len(encrypted), ENCRYPTED_BLOCK_SIZE)
    )
    repeated_blocks = len(blocks) - len(set(blocks))
    return ContainerInfo(
        header_word=header_word,
        declared_length=declared_length,
        encrypted_length=len(encrypted),
        padding_length=padding_length,
        encrypted_blocks=len(blocks),
        repeated_blocks=repeated_blocks,
    )


def validate_controls_bytes(data: bytes) -> bool:
    """Return whether bytes have a structurally valid AMS2 encrypted container."""

    try:
        analyze_container(data)
    except (Automobilista2FormatError, struct.error):
        return False
    return True


def plan_bindings(profile: ProfileCandidate, catalog: Catalog):
    """Refuse writes until the encrypted format and active slot are verified."""

    del profile, catalog
    raise Automobilista2FormatError(
        "AMS2 binding writes are locked: the Twofish controller payload, checksum, "
        "button encoding, and active in-game slot have not been verified"
    )


def _known_folder(folder_id: str) -> Path | None:
    if not hasattr(ctypes, "windll"):
        return None
    try:
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        guid = _guid(folder_id)
        result = ctypes.c_wchar_p()
        status = shell32.SHGetKnownFolderPath(
            ctypes.byref(guid), 0, None, ctypes.byref(result)
        )
        if status != 0:
            return None
        try:
            return Path(result.value)
        finally:
            ole32.CoTaskMemFree(result)
    except (AttributeError, OSError, ValueError):
        return None


class _GUID(ctypes.Structure):
    _fields_ = (
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    )


def _guid(value: str) -> _GUID:
    parts = value.split("-")
    tail = bytes.fromhex(parts[3] + parts[4])
    return _GUID(
        int(parts[0], 16),
        int(parts[1], 16),
        int(parts[2], 16),
        (ctypes.c_ubyte * 8)(*tail),
    )
