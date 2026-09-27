"""Plan conservative cross-game copies from an iRacing controls profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sim_controls_manager.adapters import (
    acc,
    assetto_corsa,
    assetto_corsa_evo,
    iracing,
    le_mans_ultimate,
)
from sim_controls_manager.catalog import Binding, Catalog, VirtualDevice
from sim_controls_manager.control_names import CONTROLS, NATIVE_CONTROL_NAMES
from sim_controls_manager.file_change import sha256


GAME_LABELS = {
    "assetto_corsa": "Assetto Corsa",
    "acc": "ACC",
    "assetto_corsa_evo": "Assetto Corsa EVO",
    "lmu": "Le Mans Ultimate",
}

ACTION_MAPS = {
    "assetto_corsa": assetto_corsa.ACTION_MAP,
    "acc": acc.ACTION_MAP,
    "assetto_corsa_evo": {
        action_id: native
        for action_id, native in assetto_corsa_evo.ACTION_MAP.items()
        if NATIVE_CONTROL_NAMES["assetto_corsa_evo"][action_id].status == "exact"
    },
    "lmu": le_mans_ultimate.ACTION_MAP,
}
TRANSFER_ACTION_IDS = tuple(
    control_id
    for control_id in CONTROLS
    if any(control_id in action_map for action_map in ACTION_MAPS.values())
)


@dataclass(frozen=True, slots=True)
class SourceCatalogs:
    catalogs: tuple[Catalog, ...]
    copied_actions: tuple[str, ...]
    skipped_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetPlan:
    game_id: str
    game_name: str
    profile: Any
    source_hash: str
    next_bytes: bytes
    changes: tuple[Any, ...]
    unsupported_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransferPreview:
    source_profile: iracing.ProfileCandidate
    source_actions: tuple[str, ...]
    skipped_source_actions: tuple[str, ...]
    targets: tuple[TargetPlan, ...]
    skipped_games: tuple[tuple[str, str], ...]


def catalogs_from_iracing(
    profile: iracing.ProfileCandidate,
    devices: tuple[iracing.DeviceInfo, ...],
) -> SourceCatalogs:
    """Translate verified iRacing button bindings into per-device catalogs.

    Axis, keyboard, unbound, ambiguous, and unidentified-device bindings are
    deliberately omitted. This keeps the transfer limited to controls whose
    meaning and physical button can both be represented by at least one target.
    """

    source_bytes = profile.controls_path.read_bytes()
    document = iracing.parse_gfcc(source_bytes)
    if iracing.build_gfcc(document) != source_bytes:
        raise iracing.IRacingFormatError(
            "source controls.cfg did not round-trip byte-exactly"
        )
    entries_by_name = {
        entry["name"]: entry for entry in document["controls"]["entries"]
    }
    devices_by_instance = {
        device.instance_guid.strip("{}").casefold(): device for device in devices
    }
    grouped: dict[tuple[str, str, str], list[Binding]] = {}
    skipped: list[str] = []

    for action_id in TRANSFER_ACTION_IDS:
        native_names = NATIVE_CONTROL_NAMES["iracing"][action_id].names
        matches = []
        for native_name in native_names:
            entry = entries_by_name.get(native_name)
            if entry is None or entry["binding_type"] != 2:
                continue
            value = entry["value"]
            if not value or value & (value - 1):
                continue
            instance_bytes = entry["slots"][1]
            product_bytes = entry["slots"][2]
            if instance_bytes == iracing.ZERO_GUID or product_bytes == iracing.ZERO_GUID:
                continue
            matches.append(
                (
                    value.bit_length(),
                    iracing.guid_to_string(instance_bytes),
                    iracing.guid_to_string(product_bytes),
                )
            )
        if len(matches) != 1:
            skipped.append(action_id)
            continue
        button, instance_guid, product_guid = matches[0]
        device = devices_by_instance.get(instance_guid.strip("{}").casefold())
        if (
            device is None
            or device.product_guid.strip("{}").casefold()
            != product_guid.strip("{}").casefold()
        ):
            skipped.append(action_id)
            continue
        key = (
            device.name,
            instance_guid.upper(),
            product_guid.upper(),
        )
        grouped.setdefault(key, []).append(Binding(action_id, button))

    catalogs = []
    copied: list[str] = []
    for (name, instance_guid, product_guid), bindings in grouped.items():
        actions_by_button: dict[int, list[str]] = {}
        for binding in bindings:
            actions_by_button.setdefault(binding.virtual_button, []).append(
                binding.action_id
            )
        unique_bindings = tuple(
            binding
            for binding in bindings
            if len(actions_by_button[binding.virtual_button]) == 1
        )
        for action_ids in actions_by_button.values():
            if len(action_ids) > 1:
                skipped.extend(action_ids)
        if not unique_bindings:
            continue
        copied.extend(binding.action_id for binding in unique_bindings)
        catalogs.append(
            Catalog(
                1,
                VirtualDevice(
                    "simhub-control-mapper",
                    name,
                    instance_guid,
                    product_guid,
                ),
                unique_bindings,
            )
        )
    return SourceCatalogs(tuple(catalogs), tuple(copied), tuple(skipped))


def _target_catalog(
    catalog: Catalog,
    game_id: str,
    available_actions: set[str] | None,
) -> Catalog | None:
    action_map = ACTION_MAPS[game_id]
    bindings = tuple(
        binding
        for binding in catalog.bindings
        if binding.action_id in action_map
        and (available_actions is None or binding.action_id in available_actions)
    )
    if not bindings:
        return None
    return Catalog(catalog.schema_version, catalog.virtual_device, bindings)


def build_preview(
    source_profile: iracing.ProfileCandidate,
    devices: tuple[iracing.DeviceInfo, ...],
    target_profiles: dict[str, Any],
    skipped_games: tuple[tuple[str, str], ...] = (),
) -> TransferPreview:
    """Plan every target independently so one incompatible game is only skipped."""

    source = catalogs_from_iracing(source_profile, devices)
    if not source.catalogs:
        raise ValueError(
            "The selected iRacing profile has no transferable button bindings on "
            "a currently connected controller."
        )

    planners: dict[str, Callable[..., Any]] = {
        "assetto_corsa": assetto_corsa.plan_bindings,
        "acc": acc.plan_bindings,
        "assetto_corsa_evo": assetto_corsa_evo.plan_bindings,
        "lmu": le_mans_ultimate.plan_bindings,
    }
    targets: list[TargetPlan] = []
    skipped = list(skipped_games)
    for game_id, profile in target_profiles.items():
        game_name = GAME_LABELS[game_id]
        try:
            original = profile.controls_path.read_bytes()
            working = original
            changes: list[Any] = []
            available_actions = None
            if game_id == "assetto_corsa":
                document = assetto_corsa.parse_controls(original)
                available_actions = {
                    action_id
                    for action_id, native_name in assetto_corsa.ACTION_MAP.items()
                    if native_name in document.sections
                }
            supported_ids = {
                action_id
                for action_id in source.copied_actions
                if action_id in ACTION_MAPS[game_id]
                and (
                    available_actions is None
                    or action_id in available_actions
                )
            }
            unsupported: list[str] = [
                action_id
                for action_id in source.copied_actions
                if action_id not in supported_ids
            ]
            for catalog in source.catalogs:
                target_catalog = _target_catalog(
                    catalog, game_id, available_actions
                )
                if target_catalog is None:
                    continue
                plan = planners[game_id](
                    profile, target_catalog, source_bytes=working
                )
                working = plan.next_bytes
                changes.extend(plan.changes)
                unsupported.extend(getattr(plan, "unsupported_actions", ()))
            targets.append(
                TargetPlan(
                    game_id,
                    game_name,
                    profile,
                    sha256(original),
                    working,
                    tuple(changes),
                    tuple(dict.fromkeys(unsupported)),
                )
            )
        except Exception as error:
            skipped.append((game_name, str(error)))

    return TransferPreview(
        source_profile,
        source.copied_actions,
        source.skipped_actions,
        tuple(targets),
        tuple(skipped),
    )
