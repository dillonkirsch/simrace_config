"""Versioned, app-owned action catalog validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CATALOG_SCHEMA_VERSION = 1
SIMHUB_PROVIDER = "simhub-control-mapper"

ACTIONS = {
    "pit_limiter": "Pit Limiter",
    "tc_increase": "Traction Control Increase",
    "tc_decrease": "Traction Control Decrease",
}
ACTION_IDS = tuple(ACTIONS)

_TOP_LEVEL_KEYS = frozenset(("schemaVersion", "virtualDevice", "bindings"))
_DEVICE_KEYS = frozenset(("provider", "identity"))
_BINDING_KEYS = frozenset(("actionId", "virtualButton"))


class CatalogValidationError(ValueError):
    """One or more independent catalog validation failures."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = tuple(issues)
        super().__init__("Invalid action catalog:\n- " + "\n- ".join(issues))


@dataclass(frozen=True, slots=True)
class VirtualDevice:
    provider: str
    identity: str


@dataclass(frozen=True, slots=True)
class Binding:
    action_id: str
    virtual_button: int


@dataclass(frozen=True, slots=True)
class Catalog:
    schema_version: int
    virtual_device: VirtualDevice
    bindings: tuple[Binding, ...]


def validate_catalog(value: Any) -> Catalog:
    """Validate and normalize a decoded JSON catalog.

    ``virtualButton`` is the positive, one-based number displayed by SimHub.
    Each game adapter owns conversion to its verified native convention.
    """
    if not isinstance(value, dict):
        raise CatalogValidationError(["catalog must be a JSON object"])

    issues: list[str] = []
    _reject_unknown_keys(value, _TOP_LEVEL_KEYS, "catalog", issues)

    if value.get("schemaVersion") != CATALOG_SCHEMA_VERSION:
        issues.append(
            f"schemaVersion must be {CATALOG_SCHEMA_VERSION}; "
            f"received {value.get('schemaVersion')!r}"
        )

    device = value.get("virtualDevice")
    valid_device = isinstance(device, dict)
    if not valid_device:
        issues.append("virtualDevice must be an object")
    else:
        _reject_unknown_keys(device, _DEVICE_KEYS, "virtualDevice", issues)
        if device.get("provider") != SIMHUB_PROVIDER:
            issues.append(f"virtualDevice.provider must be {SIMHUB_PROVIDER!r}")
        identity = device.get("identity")
        if not isinstance(identity, str) or not identity.strip():
            issues.append("virtualDevice.identity must be a non-empty string")

    bindings_value = value.get("bindings")
    if not isinstance(bindings_value, list):
        issues.append("bindings must be an array")
        bindings_value = []

    seen_actions: dict[str, str] = {}
    seen_buttons: dict[int, str] = {}
    normalized_bindings: list[Binding] = []

    for index, binding in enumerate(bindings_value):
        location = f"bindings[{index}]"
        if not isinstance(binding, dict):
            issues.append(f"{location} must be an object")
            continue

        _reject_unknown_keys(binding, _BINDING_KEYS, location, issues)
        action_id = binding.get("actionId")
        virtual_button = binding.get("virtualButton")

        valid_action = isinstance(action_id, str) and action_id in ACTIONS
        if not valid_action:
            issues.append(
                f"{location}.actionId must be one of: {', '.join(ACTION_IDS)}"
            )
        elif action_id in seen_actions:
            issues.append(
                f"{location}.actionId duplicates "
                f"{seen_actions[action_id]} ({action_id})"
            )
        else:
            seen_actions[action_id] = location

        valid_button = (
            isinstance(virtual_button, int)
            and not isinstance(virtual_button, bool)
            and virtual_button >= 1
        )
        if not valid_button:
            issues.append(f"{location}.virtualButton must be a positive integer")
        elif virtual_button in seen_buttons:
            issues.append(
                f"{location}.virtualButton duplicates "
                f"{seen_buttons[virtual_button]} (button {virtual_button})"
            )
        else:
            seen_buttons[virtual_button] = location

        if valid_action and valid_button:
            normalized_bindings.append(Binding(action_id, virtual_button))

    if issues:
        raise CatalogValidationError(issues)

    assert isinstance(device, dict)
    return Catalog(
        schema_version=CATALOG_SCHEMA_VERSION,
        virtual_device=VirtualDevice(
            provider=device["provider"],
            identity=device["identity"].strip(),
        ),
        bindings=tuple(normalized_bindings),
    )


def _reject_unknown_keys(
    value: dict[str, Any],
    allowed_keys: frozenset[str],
    location: str,
    issues: list[str],
) -> None:
    for key in value:
        if key not in allowed_keys:
            issues.append(f"{location}.{key} is not supported by this schema version")
