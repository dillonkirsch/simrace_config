"""Command-line interface used by both Python and the packaged executable."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sim_controls_manager import simhub, updater
from sim_controls_manager.adapters import acc, assetto_corsa, iracing
from sim_controls_manager.catalog import CatalogValidationError, validate_catalog
from sim_controls_manager.file_change import (
    FileChangeError,
    apply_file_change,
    plan_file_change,
    restore_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simcontrols",
        description="Safely manage simulator button-binding catalogs.",
    )
    parser.add_argument("--version", action="version", version=updater.current_version())
    commands = parser.add_subparsers(dest="command")

    catalog = commands.add_parser("catalog", help="Manage the action catalog")
    catalog_commands = catalog.add_subparsers(dest="catalog_command")
    validate = catalog_commands.add_parser(
        "validate", help="Validate a catalog without changing it"
    )
    validate.add_argument("path", type=Path)

    simhub_parser = commands.add_parser(
        "simhub", help="Read SimHub Control Mapper settings"
    )
    simhub_commands = simhub_parser.add_subparsers(dest="simhub_command")
    simhub_inspect = simhub_commands.add_parser(
        "inspect", help="Inspect the three core role-to-button mappings"
    )
    simhub_inspect.add_argument(
        "--settings", type=Path, help="Exact Control Mapper settings JSON path"
    )

    update = commands.add_parser("update", help="Check for or install app updates")
    update_commands = update.add_subparsers(dest="update_command")
    check = update_commands.add_parser("check", help="Check GitHub Releases")
    check.add_argument("--json", action="store_true", dest="as_json")
    install = update_commands.add_parser(
        "install", help="Download, verify, install, and relaunch the latest release"
    )
    install.add_argument("--json", action="store_true", dest="as_json")

    iracing_parser = commands.add_parser(
        "iracing", help="Read-only iRacing controls discovery and inspection"
    )
    iracing_commands = iracing_parser.add_subparsers(dest="iracing_command")
    discover = iracing_commands.add_parser(
        "discover", help="List controls profiles without changing them"
    )
    discover.add_argument("--root", type=Path, help="Exact Documents\\iRacing path")
    inspect = iracing_commands.add_parser(
        "inspect", help="Inspect the three initial actions in a controls profile"
    )
    inspect.add_argument("--root", type=Path, help="Exact Documents\\iRacing path")
    inspect.add_argument("--profile", help="Profile name; defaults to the active profile")
    iracing_commands.add_parser(
        "devices", help="List attached DirectInput devices and exact GUIDs"
    )
    plan = iracing_commands.add_parser(
        "plan", help="Preview three-action changes without writing"
    )
    _add_iracing_binding_arguments(plan)
    apply = iracing_commands.add_parser(
        "apply", help="Preview, back up, and apply three-action changes"
    )
    _add_iracing_binding_arguments(apply)
    apply.add_argument(
        "--yes", action="store_true", help="Confirm the previewed write"
    )
    apply.add_argument(
        "--allow-active-profile",
        action="store_true",
        help="Permit writing the profile currently selected by iRacing",
    )
    restore = iracing_commands.add_parser(
        "restore", help="Restore an iRacing backup receipt"
    )
    restore.add_argument("receipt", type=Path)
    restore.add_argument(
        "--force",
        action="store_true",
        help="Overwrite a target changed since apply after reviewing it",
    )

    ac_parser = commands.add_parser(
        "assetto-corsa",
        help="Discover, inspect, preview, and safely update Assetto Corsa controls",
    )
    ac_commands = ac_parser.add_subparsers(dest="assetto_corsa_command")
    ac_discover = ac_commands.add_parser(
        "discover", help="List live controls and saved presets without changing them"
    )
    ac_discover.add_argument(
        "--root", type=Path, help="Exact Documents\\Assetto Corsa path"
    )
    ac_inspect = ac_commands.add_parser(
        "inspect", help="Inspect supported actions in a controls profile"
    )
    ac_inspect.add_argument(
        "--root", type=Path, help="Exact Documents\\Assetto Corsa path"
    )
    ac_inspect.add_argument(
        "--profile", help="Profile name; defaults to the live controls file"
    )
    ac_plan = ac_commands.add_parser(
        "plan", help="Preview supported control changes without writing"
    )
    _add_assetto_corsa_binding_arguments(ac_plan)
    ac_apply = ac_commands.add_parser(
        "apply", help="Preview, back up, and apply supported control changes"
    )
    _add_assetto_corsa_binding_arguments(ac_apply)
    ac_apply.add_argument(
        "--yes", action="store_true", help="Confirm the previewed write"
    )
    ac_apply.add_argument(
        "--allow-active-profile",
        action="store_true",
        help="Permit writing Assetto Corsa's live controls file",
    )
    ac_restore = ac_commands.add_parser(
        "restore", help="Restore an Assetto Corsa backup receipt"
    )
    ac_restore.add_argument("receipt", type=Path)
    ac_restore.add_argument(
        "--force",
        action="store_true",
        help="Overwrite a target changed since apply after reviewing it",
    )

    acc_parser = commands.add_parser(
        "acc",
        help="Discover, inspect, preview, and safely update ACC shortcuts",
    )
    acc_commands = acc_parser.add_subparsers(dest="acc_command")
    acc_discover = acc_commands.add_parser(
        "discover", help="Find ACC's live controls file without changing it"
    )
    acc_discover.add_argument(
        "--root",
        type=Path,
        help="Exact Documents\\Assetto Corsa Competizione path",
    )
    acc_inspect = acc_commands.add_parser(
        "inspect", help="Inspect supported shortcut actions"
    )
    acc_inspect.add_argument(
        "--root",
        type=Path,
        help="Exact Documents\\Assetto Corsa Competizione path",
    )
    acc_plan = acc_commands.add_parser(
        "plan", help="Preview shortcut changes without writing"
    )
    _add_acc_binding_arguments(acc_plan)
    acc_apply = acc_commands.add_parser(
        "apply", help="Preview, back up, and apply shortcut changes"
    )
    _add_acc_binding_arguments(acc_apply)
    acc_apply.add_argument("--yes", action="store_true", help="Confirm the previewed write")
    acc_apply.add_argument(
        "--allow-active-profile",
        action="store_true",
        help="Permit writing ACC's live controls file",
    )
    acc_restore = acc_commands.add_parser("restore", help="Restore an ACC backup receipt")
    acc_restore.add_argument("receipt", type=Path)
    acc_restore.add_argument(
        "--force",
        action="store_true",
        help="Overwrite a target changed since apply after reviewing it",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "catalog" and args.catalog_command == "validate":
        return _validate_catalog(args.path)
    if args.command == "simhub" and args.simhub_command == "inspect":
        return _inspect_simhub(args.settings)
    if args.command == "update" and args.update_command == "check":
        return _check_update(args.as_json)
    if args.command == "update" and args.update_command == "install":
        return _install_update(args.as_json)
    if args.command == "iracing" and args.iracing_command == "discover":
        return _discover_iracing(args.root)
    if args.command == "iracing" and args.iracing_command == "inspect":
        return _inspect_iracing(args.root, args.profile)
    if args.command == "iracing" and args.iracing_command == "devices":
        return _list_iracing_devices()
    if args.command == "iracing" and args.iracing_command == "plan":
        return _plan_iracing(args.root, args.profile, args.catalog)
    if args.command == "iracing" and args.iracing_command == "apply":
        return _apply_iracing(
            args.root,
            args.profile,
            args.catalog,
            args.yes,
            args.allow_active_profile,
        )
    if args.command == "iracing" and args.iracing_command == "restore":
        return _restore_iracing(args.receipt, args.force)
    if args.command == "assetto-corsa" and args.assetto_corsa_command == "discover":
        return _discover_assetto_corsa(args.root)
    if args.command == "assetto-corsa" and args.assetto_corsa_command == "inspect":
        return _inspect_assetto_corsa(args.root, args.profile)
    if args.command == "assetto-corsa" and args.assetto_corsa_command == "plan":
        return _plan_assetto_corsa(args.root, args.profile, args.catalog)
    if args.command == "assetto-corsa" and args.assetto_corsa_command == "apply":
        return _apply_assetto_corsa(
            args.root,
            args.profile,
            args.catalog,
            args.yes,
            args.allow_active_profile,
        )
    if args.command == "assetto-corsa" and args.assetto_corsa_command == "restore":
        return _restore_assetto_corsa(args.receipt, args.force)
    if args.command == "acc" and args.acc_command == "discover":
        return _discover_acc(args.root)
    if args.command == "acc" and args.acc_command == "inspect":
        return _inspect_acc(args.root)
    if args.command == "acc" and args.acc_command == "plan":
        return _plan_acc(args.root, args.catalog)
    if args.command == "acc" and args.acc_command == "apply":
        return _apply_acc(
            args.root, args.catalog, args.yes, args.allow_active_profile
        )
    if args.command == "acc" and args.acc_command == "restore":
        return _restore_acc(args.receipt, args.force)

    parser.error("a subcommand is required")
    return 2


def _validate_catalog(path: Path) -> int:
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Could not read catalog: {error}", file=sys.stderr)
        return 1

    try:
        catalog = validate_catalog(value)
    except CatalogValidationError as error:
        print(error, file=sys.stderr)
        return 1

    print("Catalog is valid.")
    print(f"Device: {catalog.virtual_device.identity}")
    print(f"Bindings: {len(catalog.bindings)}")
    for binding in catalog.bindings:
        print(f"- {binding.action_id}: SimHub button {binding.virtual_button}")
    return 0


def _inspect_simhub(settings: Path | None) -> int:
    try:
        inspection = simhub.inspect_control_mapper(settings)
    except ValueError as error:
        print(f"SimHub inspection failed: {error}", file=sys.stderr)
        return 1

    print(f"Settings: {inspection.settings_path}")
    print(f"Output mode: {inspection.output_mode if inspection.output_mode is not None else 'not set'}")
    print(
        "Target vJoy device: "
        f"{inspection.target_vjoy_id if inspection.target_vjoy_id is not None else 'not set'}"
    )
    for binding in inspection.bindings:
        print(
            f"- {binding.action_id} -> {binding.role}: "
            f"SimHub button {binding.virtual_button}"
        )
    for action_id in inspection.missing_actions:
        print(f"- {action_id}: not mapped")
    print("Read-only inspection complete; no SimHub settings were changed.")
    return 0


def _check_update(as_json: bool) -> int:
    result = updater.check_for_update()
    if as_json:
        print(json.dumps(result, indent=2))
    elif not result.get("ok"):
        print(f"Update check failed: {result.get('error', 'unknown error')}", file=sys.stderr)
    elif result.get("update_available"):
        print(
            f"Update available: {result.get('latest')} "
            f"(current: {result.get('current')})"
        )
        if not result.get("assets_valid"):
            print("The release cannot be installed automatically because an asset is missing.")
        elif not result.get("can_apply"):
            print("Run the packaged SimControlsManagerCLI.exe to install it automatically.")
        else:
            print("Run 'SimControlsManagerCLI.exe update install' to install and relaunch.")
    else:
        print(f"Already up to date ({result.get('current')}).")
    return 0 if result.get("ok") else 1


def _install_update(as_json: bool) -> int:
    result = updater.apply_latest_update()
    if as_json:
        print(json.dumps(result, indent=2))
    elif not result.get("ok"):
        print(f"Update failed: {result.get('error', 'unknown error')}", file=sys.stderr)
    elif result.get("restarting"):
        print("Update verified and staged. The app will close, replace itself, and reopen.")
    else:
        print(result.get("message", "No update was installed."))
    return 0 if result.get("ok") else 1


def _discover_iracing(root: Path | None) -> int:
    try:
        result = iracing.discover(root)
    except OSError as error:
        print(f"iRacing discovery failed: {error}", file=sys.stderr)
        return 1
    print(f"iRacing directory: {result.iracing_directory}")
    print(f"Active profile: {result.active_profile or 'Legacy / not declared'}")
    if result.profiles:
        print("Profiles:")
        for profile in result.profiles:
            marker = " (active)" if profile.active else ""
            print(f"- {profile.name}{marker}: {profile.controls_path}")
    else:
        print("Profiles: none")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    print("Read-only discovery complete; no files were changed.")
    return 0


def _inspect_iracing(root: Path | None, requested_profile: str | None) -> int:
    try:
        discovery = iracing.discover(root)
        profile = _select_iracing_profile(discovery, requested_profile)
        inspection = iracing.inspect_profile(profile)
    except (OSError, ValueError) as error:
        print(f"iRacing inspection failed: {error}", file=sys.stderr)
        return 1

    print(f"Profile: {profile.name}{' (active)' if profile.active else ''}")
    print(f"File: {profile.controls_path}")
    print(
        f"Format: GFCC {inspection.gfcc_version}, "
        f"controls {inspection.controls_version}; byte-exact round trip verified"
    )
    for action in inspection.actions:
        if action.status != "supported" or action.binding is None:
            print(f"- {action.action_id} -> {action.native_action}: {action.status}")
            continue
        binding = action.binding
        detail = binding.binding_type
        if binding.native_button_index is not None:
            detail += f" Btn {binding.native_button_index}"
        if binding.instance_guid:
            detail += f" instance {binding.instance_guid}"
        print(f"- {action.action_id} -> {action.native_action}: {detail}")
    print("Read-only inspection complete; no files were changed.")
    return 0


def _select_iracing_profile(
    discovery: iracing.DiscoveryResult, requested_profile: str | None
) -> iracing.ProfileCandidate:
    if requested_profile:
        matches = [
            profile
            for profile in discovery.profiles
            if profile.name.casefold() == requested_profile.casefold()
        ]
        if len(matches) != 1:
            raise ValueError(f"profile {requested_profile!r} was not found")
        return matches[0]
    active = [profile for profile in discovery.profiles if profile.active]
    if len(active) == 1:
        return active[0]
    if len(discovery.profiles) == 1:
        return discovery.profiles[0]
    raise ValueError("active profile is ambiguous; pass --profile with an exact name")


def _add_iracing_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, help="Exact Documents\\iRacing path")
    parser.add_argument("--profile", required=True, help="Exact profile name")
    parser.add_argument("--catalog", required=True, type=Path)


def _list_iracing_devices() -> int:
    devices, error = iracing.enumerate_connected_devices()
    if error:
        print(f"DirectInput warning: {error}", file=sys.stderr)
    if not devices:
        print("No attached DirectInput controllers were found.")
        try:
            configured = simhub.inspect_control_mapper()
        except ValueError:
            configured = None
        if configured and configured.target_vjoy_id is not None:
            print(
                f"SimHub targets vJoy device {configured.target_vjoy_id}, but Windows "
                "is not exposing that device. Install or enable vJoy, then restart "
                "SimHub and run this command again."
            )
        else:
            print("Start SimHub and enable its virtual output, then run this command again.")
        return 1 if error else 0
    for device in devices:
        print(device.name)
        print(f"  instanceGuid: {device.instance_guid}")
        print(f"  productGuid:  {device.product_guid}")
    return 0


def _load_catalog(path: Path):
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read catalog: {error}") from error
    return validate_catalog(value)


def _build_iracing_plan(root: Path | None, profile_name: str, catalog_path: Path):
    discovery = iracing.discover(root)
    profile = _select_iracing_profile(discovery, profile_name)
    catalog = _load_catalog(catalog_path)
    return iracing.plan_bindings(profile, catalog)


def _print_iracing_plan(plan: iracing.BindingPlan) -> None:
    print(f"Profile: {plan.profile.name}{' (active)' if plan.profile.active else ''}")
    print(f"File: {plan.profile.controls_path}")
    print(f"Source SHA-256: {plan.source_hash}")
    if not plan.changes:
        print("No changes: all requested bindings already match.")
        return
    print("Proposed changes:")
    for change in plan.changes:
        print(
            f"- {change.action_id} -> {change.native_action}: "
            f"{_format_native_binding(change.before)} -> "
            f"{_format_native_binding(change.after)}"
        )


def _format_native_binding(binding: iracing.NativeBinding) -> str:
    if binding.binding_type == "button" and binding.native_button_index is not None:
        return f"button Btn {binding.native_button_index} on {binding.instance_guid}"
    return binding.binding_type


def _plan_iracing(root: Path | None, profile_name: str, catalog_path: Path) -> int:
    try:
        plan = _build_iracing_plan(root, profile_name, catalog_path)
    except (OSError, ValueError, CatalogValidationError) as error:
        print(f"iRacing plan failed: {error}", file=sys.stderr)
        return 1
    _print_iracing_plan(plan)
    print("Preview only; no files were changed.")
    return 0


def _apply_iracing(
    root: Path | None,
    profile_name: str,
    catalog_path: Path,
    confirmed: bool,
    allow_active_profile: bool,
) -> int:
    try:
        binding_plan = _build_iracing_plan(root, profile_name, catalog_path)
        _print_iracing_plan(binding_plan)
        if not binding_plan.changes:
            return 0
        if binding_plan.profile.active and not allow_active_profile:
            raise ValueError(
                "refusing to write the active profile; select a test profile or pass "
                "--allow-active-profile after reviewing the preview"
            )
        if not confirmed:
            print("Preview only. Re-run with --yes to back up and apply these changes.")
            return 0
        file_plan = plan_file_change(
            binding_plan.profile.controls_path, binding_plan.next_bytes
        )
        if file_plan.source_hash != binding_plan.source_hash:
            raise FileChangeError(
                "SOURCE_CHANGED", "controls.cfg changed while the plan was being prepared"
            )
        result = apply_file_change(
            file_plan,
            _iracing_backup_directory(binding_plan.profile.name),
            validate=_validate_iracing_bytes,
            is_target_in_use=iracing.is_iracing_running,
        )
    except (OSError, ValueError, CatalogValidationError, FileChangeError) as error:
        print(f"iRacing apply failed: {error}", file=sys.stderr)
        return 1
    print(f"Applied with verified backup. Restore receipt: {result.receipt_path}")
    return 0


def _restore_iracing(receipt_path: Path, force: bool) -> int:
    try:
        result = restore_file(
            receipt_path,
            allow_changed_target=force,
            is_target_in_use=iracing.is_iracing_running,
            validate=_validate_iracing_bytes,
        )
    except (OSError, ValueError, FileChangeError) as error:
        print(f"iRacing restore failed: {error}", file=sys.stderr)
        return 1
    print(f"Restore status: {result.status}")
    return 0


def _validate_iracing_bytes(data: bytes) -> bool:
    return iracing.build_gfcc(iracing.parse_gfcc(data)) == data


def _iracing_backup_directory(profile_name: str) -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    safe_profile = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in profile_name
    )
    return base / "sim-controls-manager" / "backups" / "iracing" / safe_profile


def _discover_assetto_corsa(root: Path | None) -> int:
    try:
        result = assetto_corsa.discover(root)
    except OSError as error:
        print(f"Assetto Corsa discovery failed: {error}", file=sys.stderr)
        return 1
    print(f"Assetto Corsa directory: {result.assetto_corsa_directory}")
    if result.profiles:
        print("Profiles:")
        for profile in result.profiles:
            marker = " (live)" if profile.active else ""
            print(f"- {profile.name}{marker}: {profile.controls_path}")
    else:
        print("Profiles: none")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    print("Read-only discovery complete; no files were changed.")
    return 0


def _select_assetto_corsa_profile(
    discovery: assetto_corsa.DiscoveryResult, requested_profile: str | None
) -> assetto_corsa.ProfileCandidate:
    requested = requested_profile or "Live"
    matches = [
        profile
        for profile in discovery.profiles
        if profile.name.casefold() == requested.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(f"profile {requested!r} was not found or is ambiguous")
    return matches[0]


def _inspect_assetto_corsa(root: Path | None, requested_profile: str | None) -> int:
    try:
        discovery = assetto_corsa.discover(root)
        profile = _select_assetto_corsa_profile(discovery, requested_profile)
        inspection = assetto_corsa.inspect_profile(profile)
    except (OSError, ValueError) as error:
        print(f"Assetto Corsa inspection failed: {error}", file=sys.stderr)
        return 1

    print(f"Profile: {profile.name}{' (live)' if profile.active else ''}")
    print(f"File: {profile.controls_path}")
    print(f"Format: INI ({inspection.encoding}); byte-exact round trip verified")
    for action in inspection.actions:
        if action.status != "supported" or action.binding is None:
            native = f"[{action.native_action}]" if action.native_action else "not exposed"
            print(f"- {action.action_id} -> {native}: {action.status}")
            continue
        print(
            f"- {action.action_id} -> [{action.native_action}]: "
            f"{_format_assetto_corsa_binding(action.binding)}"
        )
    print("Read-only inspection complete; no files were changed.")
    return 0


def _add_assetto_corsa_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root", type=Path, help="Exact Documents\\Assetto Corsa path"
    )
    parser.add_argument(
        "--profile", default="Live", help="Exact profile name (default: Live)"
    )
    parser.add_argument("--catalog", required=True, type=Path)


def _build_assetto_corsa_plan(
    root: Path | None, profile_name: str, catalog_path: Path
):
    discovery = assetto_corsa.discover(root)
    profile = _select_assetto_corsa_profile(discovery, profile_name)
    catalog = _load_catalog(catalog_path)
    return assetto_corsa.plan_bindings(profile, catalog)


def _print_assetto_corsa_plan(plan: assetto_corsa.BindingPlan) -> None:
    print(f"Profile: {plan.profile.name}{' (live)' if plan.profile.active else ''}")
    print(f"File: {plan.profile.controls_path}")
    print(f"Source SHA-256: {plan.source_hash}")
    for action_id in plan.unsupported_actions:
        print(f"Unavailable: {action_id} is not exposed by Assetto Corsa")
    if not plan.changes:
        print("No supported changes: all requested bindings already match.")
        return
    print("Proposed changes:")
    for change in plan.changes:
        print(
            f"- {change.action_id} -> [{change.native_action}]: "
            f"{_format_assetto_corsa_binding(change.before)} -> "
            f"{_format_assetto_corsa_binding(change.after)}"
        )


def _format_assetto_corsa_binding(binding: assetto_corsa.NativeBinding) -> str:
    if (
        binding.binding_type == "button"
        and binding.joy_index is not None
        and binding.native_button_index is not None
    ):
        return (
            f"controller {binding.joy_index}, button {binding.native_button_index + 1} "
            f"(native {binding.native_button_index})"
        )
    if binding.binding_type == "key" and binding.key:
        return f"key {binding.key}"
    if binding.binding_type == "xbox_button" and binding.xbox_button:
        return f"Xbox button {binding.xbox_button}"
    return binding.binding_type


def _plan_assetto_corsa(
    root: Path | None, profile_name: str, catalog_path: Path
) -> int:
    try:
        plan = _build_assetto_corsa_plan(root, profile_name, catalog_path)
    except (OSError, ValueError, CatalogValidationError) as error:
        print(f"Assetto Corsa plan failed: {error}", file=sys.stderr)
        return 1
    _print_assetto_corsa_plan(plan)
    print("Preview only; no files were changed.")
    return 0


def _apply_assetto_corsa(
    root: Path | None,
    profile_name: str,
    catalog_path: Path,
    confirmed: bool,
    allow_active_profile: bool,
) -> int:
    try:
        binding_plan = _build_assetto_corsa_plan(root, profile_name, catalog_path)
        _print_assetto_corsa_plan(binding_plan)
        if not binding_plan.changes:
            return 0
        if binding_plan.profile.active and not allow_active_profile:
            raise ValueError(
                "refusing to write the live controls file; select a saved test preset "
                "or pass --allow-active-profile after reviewing the preview"
            )
        if not confirmed:
            print("Preview only. Re-run with --yes to back up and apply these changes.")
            return 0
        file_plan = plan_file_change(
            binding_plan.profile.controls_path, binding_plan.next_bytes
        )
        if file_plan.source_hash != binding_plan.source_hash:
            raise FileChangeError(
                "SOURCE_CHANGED", "controls.ini changed while the plan was being prepared"
            )
        result = apply_file_change(
            file_plan,
            _assetto_corsa_backup_directory(binding_plan.profile.name),
            validate=assetto_corsa.validate_controls_bytes,
            is_target_in_use=assetto_corsa.is_assetto_corsa_running,
        )
    except (OSError, ValueError, CatalogValidationError, FileChangeError) as error:
        print(f"Assetto Corsa apply failed: {error}", file=sys.stderr)
        return 1
    print(f"Applied with verified backup. Restore receipt: {result.receipt_path}")
    return 0


def _restore_assetto_corsa(receipt_path: Path, force: bool) -> int:
    try:
        result = restore_file(
            receipt_path,
            allow_changed_target=force,
            is_target_in_use=assetto_corsa.is_assetto_corsa_running,
            validate=assetto_corsa.validate_controls_bytes,
        )
    except (OSError, ValueError, FileChangeError) as error:
        print(f"Assetto Corsa restore failed: {error}", file=sys.stderr)
        return 1
    print(f"Restore status: {result.status}")
    return 0


def _assetto_corsa_backup_directory(profile_name: str) -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    safe_profile = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in profile_name
    )
    return (
        base
        / "sim-controls-manager"
        / "backups"
        / "assetto-corsa"
        / safe_profile
    )


def _discover_acc(root: Path | None) -> int:
    try:
        result = acc.discover(root)
    except OSError as error:
        print(f"ACC discovery failed: {error}", file=sys.stderr)
        return 1
    print(f"ACC directory: {result.acc_directory}")
    if result.profiles:
        for profile in result.profiles:
            print(f"Profile: {profile.name} (live): {profile.controls_path}")
    else:
        print("Profiles: none")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    print("Read-only discovery complete; no files were changed.")
    return 0


def _acc_profile(root: Path | None) -> acc.ProfileCandidate:
    discovery = acc.discover(root)
    if len(discovery.profiles) != 1:
        raise ValueError("ACC's live controls profile was not found")
    return discovery.profiles[0]


def _inspect_acc(root: Path | None) -> int:
    try:
        profile = _acc_profile(root)
        inspection = acc.inspect_profile(profile)
    except (OSError, ValueError) as error:
        print(f"ACC inspection failed: {error}", file=sys.stderr)
        return 1
    print(f"Profile: {profile.name} (live)")
    print(f"File: {profile.controls_path}")
    print(f"Format: ACC controls JSON version {inspection.version}; source verified")
    for action in inspection.actions:
        print(
            f"- {action.action_id} -> {action.native_action}: "
            f"{_format_acc_binding(action.binding)}"
        )
    print("Read-only inspection complete; no files were changed.")
    return 0


def _add_acc_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        help="Exact Documents\\Assetto Corsa Competizione path",
    )
    parser.add_argument("--catalog", required=True, type=Path)


def _build_acc_plan(root: Path | None, catalog_path: Path) -> acc.BindingPlan:
    return acc.plan_bindings(_acc_profile(root), _load_catalog(catalog_path))


def _print_acc_plan(plan: acc.BindingPlan) -> None:
    print("Profile: Live (live)")
    print(f"File: {plan.profile.controls_path}")
    print(f"Source SHA-256: {plan.source_hash}")
    if not plan.changes:
        print("No changes: all requested shortcuts already match.")
        return
    print("Proposed shortcut changes:")
    for change in plan.changes:
        print(
            f"- {change.action_id} -> {change.native_action}: "
            f"{_format_acc_binding(change.before)} -> "
            f"{_format_acc_binding(change.after)}"
        )


def _format_acc_binding(binding: acc.NativeBinding) -> str:
    if binding.binding_type == "button" and binding.native_button_index is not None:
        return (
            f"button {binding.native_button_index + 1} "
            f"(native {binding.native_button_index}) on device {binding.device_index}"
        )
    return binding.binding_type


def _plan_acc(root: Path | None, catalog_path: Path) -> int:
    try:
        plan = _build_acc_plan(root, catalog_path)
    except (OSError, ValueError, CatalogValidationError) as error:
        print(f"ACC plan failed: {error}", file=sys.stderr)
        return 1
    _print_acc_plan(plan)
    print("Preview only; no files were changed.")
    return 0


def _apply_acc(
    root: Path | None,
    catalog_path: Path,
    confirmed: bool,
    allow_active_profile: bool,
) -> int:
    try:
        binding_plan = _build_acc_plan(root, catalog_path)
        _print_acc_plan(binding_plan)
        if not binding_plan.changes:
            return 0
        if not allow_active_profile:
            raise ValueError(
                "refusing to write ACC's live controls file; pass "
                "--allow-active-profile after reviewing the preview"
            )
        if not confirmed:
            print("Preview only. Re-run with --yes to back up and apply these changes.")
            return 0
        file_plan = plan_file_change(
            binding_plan.profile.controls_path, binding_plan.next_bytes
        )
        if file_plan.source_hash != binding_plan.source_hash:
            raise FileChangeError(
                "SOURCE_CHANGED", "controls.json changed while the plan was being prepared"
            )
        result = apply_file_change(
            file_plan,
            _acc_backup_directory(),
            validate=acc.validate_controls_bytes,
            is_target_in_use=acc.is_acc_running,
        )
    except (OSError, ValueError, CatalogValidationError, FileChangeError) as error:
        print(f"ACC apply failed: {error}", file=sys.stderr)
        return 1
    print(f"Applied with verified backup. Restore receipt: {result.receipt_path}")
    return 0


def _restore_acc(receipt_path: Path, force: bool) -> int:
    try:
        result = restore_file(
            receipt_path,
            allow_changed_target=force,
            is_target_in_use=acc.is_acc_running,
            validate=acc.validate_controls_bytes,
        )
    except (OSError, ValueError, FileChangeError) as error:
        print(f"ACC restore failed: {error}", file=sys.stderr)
        return 1
    print(f"Restore status: {result.status}")
    return 0


def _acc_backup_directory() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "sim-controls-manager" / "backups" / "acc" / "Live"


if __name__ == "__main__":
    raise SystemExit(main())
