"""Command-line interface used by both Python and the packaged executable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sim_controls_manager import updater
from sim_controls_manager.adapters import iracing
from sim_controls_manager.catalog import CatalogValidationError, validate_catalog


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "catalog" and args.catalog_command == "validate":
        return _validate_catalog(args.path)
    if args.command == "update" and args.update_command == "check":
        return _check_update(args.as_json)
    if args.command == "update" and args.update_command == "install":
        return _install_update(args.as_json)
    if args.command == "iracing" and args.iracing_command == "discover":
        return _discover_iracing(args.root)
    if args.command == "iracing" and args.iracing_command == "inspect":
        return _inspect_iracing(args.root, args.profile)

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
            print("Run the packaged SimControlsManager.exe to install it automatically.")
        else:
            print("Run 'SimControlsManager.exe update install' to install and relaunch.")
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


if __name__ == "__main__":
    raise SystemExit(main())
