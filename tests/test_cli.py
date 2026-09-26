import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager import cli
from sim_controls_manager.adapters import iracing
from sim_controls_manager.adapters import assetto_corsa_evo as evo


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="sim-controls-cli-"
        )
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_catalog(self, value) -> Path:
        path = self.root / "catalog.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_validates_and_summarizes_manual_catalog_without_writing(self) -> None:
        path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub output",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        before = path.read_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli.main(["catalog", "validate", str(path)])
        self.assertEqual(exit_code, 0)
        self.assertIn("Catalog is valid", output.getvalue())
        self.assertIn("pit_limiter: SimHub button 7", output.getvalue())
        self.assertEqual(path.read_bytes(), before)

    def test_runs_as_real_module_entry_point(self) -> None:
        path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub output",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        environment = os.environ.copy()
        source_root = str(Path(__file__).parents[1] / "src")
        environment["PYTHONPATH"] = source_root + os.pathsep + environment.get(
            "PYTHONPATH", ""
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sim_controls_manager",
                "catalog",
                "validate",
                str(path),
            ],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Catalog is valid", result.stdout)

    def test_reports_malformed_json(self) -> None:
        path = self.root / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            exit_code = cli.main(["catalog", "validate", str(path)])
        self.assertEqual(exit_code, 1)
        self.assertIn("Could not read catalog", errors.getvalue())

    def test_inspects_simhub_settings_without_writing(self) -> None:
        path = self.root / "simhub.json"
        path.write_text(
            json.dumps(
                {
                    "OutputMode": 0,
                    "VJoyMapping": {"TargetVJoyId": 1},
                    "OutputMapping": {
                        "ControllerMapping": {
                            "Buttons": [
                                {"ButtonId": 19, "TargetRole": "PitLimiter"},
                                {"ButtonId": 7, "TargetRole": "TractionControl+"},
                                {"ButtonId": 6, "TargetRole": "TractionControl-"},
                            ]
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        before = path.read_bytes()
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = cli.main(["simhub", "inspect", "--settings", str(path)])

        self.assertEqual(exit_code, 0)
        self.assertIn("pit_limiter -> PitLimiter: SimHub button 20", output.getvalue())
        self.assertEqual(path.read_bytes(), before)

    def test_update_check_output(self) -> None:
        with mock.patch.object(
            cli.updater,
            "check_for_update",
            return_value={
                "ok": True,
                "current": "v0.1.0",
                "latest": "v0.2.0",
                "update_available": True,
                "assets_valid": True,
                "can_apply": True,
            },
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = cli.main(["update", "check"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Update available: v0.2.0", output.getvalue())

    def test_iracing_apply_and_restore_end_to_end_on_test_profile(self) -> None:
        iracing_root = self.root / "iRacing"
        profile_directory = iracing_root / "profiles" / "controls" / "Test"
        profile_directory.mkdir(parents=True)
        controls_path = profile_directory / "controls.cfg"
        original = _minimal_iracing_controls()
        controls_path.write_bytes(original)
        (iracing_root / "app.ini").write_text(
            "[ControlProfiles]\nGlobal=Baseline\n", encoding="utf-8"
        )
        catalog_path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "Test virtual output",
                    "instanceGuid": "11111111-1111-1111-1111-111111111111",
                    "productGuid": "22222222-2222-2222-2222-222222222222",
                },
                "bindings": [
                    {"actionId": "pit_limiter", "virtualButton": 7},
                    {"actionId": "tc_increase", "virtualButton": 8},
                    {"actionId": "tc_decrease", "virtualButton": 9},
                ],
            }
        )
        backups = self.root / "backups"
        output = io.StringIO()
        with (
            mock.patch.object(cli, "_iracing_backup_directory", return_value=backups),
            mock.patch.object(cli.iracing, "is_iracing_running", return_value=False),
            contextlib.redirect_stdout(output),
        ):
            exit_code = cli.main(
                [
                    "iracing",
                    "apply",
                    "--root",
                    str(iracing_root),
                    "--profile",
                    "Test",
                    "--catalog",
                    str(catalog_path),
                    "--yes",
                ]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertNotEqual(controls_path.read_bytes(), original)
        self.assertIn("Applied with verified backup", output.getvalue())
        receipt = next(backups.glob("*-receipt.json"))

        with (
            mock.patch.object(cli.iracing, "is_iracing_running", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            restore_exit = cli.main(["iracing", "restore", str(receipt)])
        self.assertEqual(restore_exit, 0)
        self.assertEqual(controls_path.read_bytes(), original)

    def test_assetto_corsa_apply_and_restore_end_to_end(self) -> None:
        ac_root = self.root / "Assetto Corsa"
        controls_path = ac_root / "cfg" / "controls.ini"
        controls_path.parent.mkdir(parents=True)
        original = _minimal_assetto_corsa_controls()
        controls_path.write_bytes(original)
        catalog_path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub Virtual Controller",
                    "instanceGuid": "11111111-1111-1111-1111-111111111111",
                    "productGuid": "22222222-2222-2222-2222-222222222222",
                },
                "bindings": [
                    {"actionId": "pit_limiter", "virtualButton": 7},
                    {"actionId": "tc_increase", "virtualButton": 8},
                    {"actionId": "tc_decrease", "virtualButton": 9},
                ],
            }
        )
        backups = self.root / "ac-backups"
        output = io.StringIO()
        with (
            mock.patch.object(
                cli, "_assetto_corsa_backup_directory", return_value=backups
            ),
            mock.patch.object(
                cli.assetto_corsa, "is_assetto_corsa_running", return_value=False
            ),
            contextlib.redirect_stdout(output),
        ):
            exit_code = cli.main(
                [
                    "assetto-corsa",
                    "apply",
                    "--root",
                    str(ac_root),
                    "--catalog",
                    str(catalog_path),
                    "--yes",
                    "--allow-active-profile",
                ]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertNotEqual(controls_path.read_bytes(), original)
        self.assertIn("pit_limiter is not exposed", output.getvalue())
        self.assertIn("Applied with verified backup", output.getvalue())
        receipt = next(backups.glob("*-receipt.json"))

        with (
            mock.patch.object(
                cli.assetto_corsa, "is_assetto_corsa_running", return_value=False
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            restore_exit = cli.main(["assetto-corsa", "restore", str(receipt)])
        self.assertEqual(restore_exit, 0)
        self.assertEqual(controls_path.read_bytes(), original)

    def test_acc_apply_and_restore_end_to_end(self) -> None:
        acc_root = self.root / "Assetto Corsa Competizione"
        controls_path = acc_root / "Config" / "controls.json"
        controls_path.parent.mkdir(parents=True)
        original = _minimal_acc_controls()
        controls_path.write_bytes(original)
        catalog_path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub Virtual Controller",
                    "instanceGuid": "11111111-1111-1111-1111-111111111111",
                    "productGuid": "22222222-2222-2222-2222-222222222222",
                },
                "bindings": [
                    {"actionId": "pit_limiter", "virtualButton": 7},
                    {"actionId": "tc_increase", "virtualButton": 8},
                    {"actionId": "tc_decrease", "virtualButton": 9},
                ],
            }
        )
        backups = self.root / "acc-backups"
        output = io.StringIO()
        with (
            mock.patch.object(cli, "_acc_backup_directory", return_value=backups),
            mock.patch.object(cli.acc, "is_acc_running", return_value=False),
            contextlib.redirect_stdout(output),
        ):
            exit_code = cli.main(
                [
                    "acc",
                    "apply",
                    "--root",
                    str(acc_root),
                    "--catalog",
                    str(catalog_path),
                    "--yes",
                    "--allow-active-profile",
                ]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertNotEqual(controls_path.read_bytes(), original)
        self.assertIn("Applied with verified backup", output.getvalue())
        receipt = next(backups.glob("*-receipt.json"))

        with (
            mock.patch.object(cli.acc, "is_acc_running", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            restore_exit = cli.main(["acc", "restore", str(receipt)])
        self.assertEqual(restore_exit, 0)
        self.assertEqual(controls_path.read_bytes(), original)

    def test_lmu_apply_and_restore_end_to_end(self) -> None:
        lmu_root = self.root / "Le Mans Ultimate"
        controls_path = (
            lmu_root / "UserData" / "Controller" / "Presets" / "Tablet.JSON"
        )
        controls_path.parent.mkdir(parents=True)
        original = _minimal_lmu_controls()
        controls_path.write_bytes(original)
        catalog_path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub Virtual Controller",
                },
                "bindings": [
                    {"actionId": "pit_limiter", "virtualButton": 7},
                    {"actionId": "tc_increase", "virtualButton": 8},
                    {"actionId": "tc_decrease", "virtualButton": 9},
                ],
            }
        )
        backups = self.root / "lmu-backups"
        output = io.StringIO()
        with (
            mock.patch.object(cli, "_lmu_backup_directory", return_value=backups),
            mock.patch.object(
                cli.le_mans_ultimate, "is_lmu_running", return_value=False
            ),
            contextlib.redirect_stdout(output),
        ):
            exit_code = cli.main(
                [
                    "lmu",
                    "apply",
                    "--root",
                    str(lmu_root),
                    "--profile",
                    "Tablet",
                    "--catalog",
                    str(catalog_path),
                    "--yes",
                ]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        updated = json.loads(controls_path.read_bytes())
        self.assertEqual(updated["Input"]["Speed Limiter"]["id"], 38)
        self.assertEqual(updated["Input"]["Shift Up"]["id"], 51)
        receipt = next(backups.glob("*-receipt.json"))

        with (
            mock.patch.object(
                cli.le_mans_ultimate, "is_lmu_running", return_value=False
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            restore_exit = cli.main(["lmu", "restore", str(receipt)])
        self.assertEqual(restore_exit, 0)
        self.assertEqual(controls_path.read_bytes(), original)

    def test_assetto_corsa_evo_apply_and_restore_end_to_end(self) -> None:
        evo_root = self.root / "ACE"
        evo_root.mkdir()
        controls_path = evo_root / evo.CONTROLS_FILE
        original = _minimal_evo_controls()
        controls_path.write_bytes(original)
        catalog_path = self._write_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "SimHub Virtual Controller",
                    "instanceGuid": "11111111-1111-1111-1111-111111111111",
                    "productGuid": "22222222-2222-2222-2222-222222222222",
                },
                "bindings": [
                    {"actionId": "pit_limiter", "virtualButton": 7},
                    {"actionId": "tc_increase", "virtualButton": 8},
                    {"actionId": "tc_decrease", "virtualButton": 9},
                ],
            }
        )
        backups = self.root / "evo-backups"
        output = io.StringIO()
        with (
            mock.patch.object(
                cli, "_assetto_corsa_evo_backup_directory", return_value=backups
            ),
            mock.patch.object(
                cli.assetto_corsa_evo,
                "is_assetto_corsa_evo_running",
                return_value=False,
            ),
            contextlib.redirect_stdout(output),
        ):
            exit_code = cli.main(
                [
                    "assetto-corsa-evo",
                    "apply",
                    "--root",
                    str(evo_root),
                    "--catalog",
                    str(catalog_path),
                    "--yes",
                    "--allow-active-profile",
                ]
            )
        self.assertEqual(exit_code, 0, output.getvalue())
        self.assertNotEqual(controls_path.read_bytes(), original)
        inspection = evo.inspect_profile(
            evo.ProfileCandidate("Live", controls_path, True, "protobuf")
        )
        self.assertEqual(inspection.actions[0].binding.native_button_index, 6)
        receipt = next(backups.glob("*-receipt.json"))

        with (
            mock.patch.object(
                cli.assetto_corsa_evo,
                "is_assetto_corsa_evo_running",
                return_value=False,
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            restore_exit = cli.main(["assetto-corsa-evo", "restore", str(receipt)])
        self.assertEqual(restore_exit, 0)
        self.assertEqual(controls_path.read_bytes(), original)


def _minimal_iracing_controls() -> bytes:
    zero = b"\x00" * 16
    entries = []
    for name, binding_type, value in (
        ("PitSpeedLimiter", 4, 80),
        ("TractionControlInc", 0, 0),
        ("TractionControlDec", 0, 0),
    ):
        entries.append(
            {
                "name": name,
                "unknown": 0,
                "flags": 6,
                "binding_type": binding_type,
                "value": value,
                "modifiers": 0,
                "slots": (zero, zero, zero),
            }
        )
    return iracing.build_gfcc(
        {
            "header": {"version": 20},
            "global_config": b"test-global-config",
            "controls": {"version": 8, "entries": entries},
            "trailer": b"  ",
        }
    )


def _minimal_assetto_corsa_controls() -> bytes:
    return (
        "[HEADER]\r\n"
        "INPUT_METHOD=WHEEL\r\n"
        "\r\n"
        "[CONTROLLERS]\r\n"
        "CON0=SimHub Virtual Controller\r\n"
        "PGUID0=22222222-2222-2222-2222-222222222222\r\n"
        "\r\n"
        "[TCUP]\r\n"
        "JOY=-1\r\n"
        "BUTTON=-1\r\n"
        "XBOXBUTTON=-1\r\n"
        "KEY=-1\r\n"
        "\r\n"
        "[TCDN]\r\n"
        "JOY=-1\r\n"
        "BUTTON=-1\r\n"
        "XBOXBUTTON=-1\r\n"
        "KEY=-1\r\n"
    ).encode("utf-8")


def _minimal_acc_controls() -> bytes:
    value = {
        "version": 0,
        "commandDevices": [
            {
                "version": 0,
                "productName": "SimHub Virtual Controller",
                "instanceGuid": "{11111111-1111-1111-1111-111111111111}",
                "isPedals": 0,
                "uICommandButtonList": [],
                "raceCommandButtonList": [],
                "raceCommandAxisList": [],
            }
        ],
        "gamepadSettings": {"raceCommandButtonList": []},
        "keyboardSettings": {"raceCommandButtonList": []},
    }
    return json.dumps(value, indent="\t").replace("\n", "\r\n").encode("utf-8")


def _minimal_lmu_controls() -> bytes:
    value = {
        "Alternative Input": {},
        "Devices": {
            "SimHub Virtual Controller-ABC": {
                "Type": "Wheel",
                "instance name": "SimHub Virtual Controller",
                "layout": {"axes": 0, "buttons": 32, "povs": 0},
            }
        },
        "Input": {
            "Shift Up": {"device": "SimHub Virtual Controller-ABC", "id": 51}
        },
        "Type": "Direct Input",
    }
    return json.dumps(value, indent="\t").replace("\n", "\r\n").encode("utf-8")


def _minimal_evo_controls() -> bytes:
    identity = b"".join(
        (
            evo._encode_length_field(1, b"SimHub Virtual Controller"),
            evo._encode_length_field(2, b"11111111-1111-1111-1111-111111111111"),
            evo._encode_length_field(5, b"22222222-2222-2222-2222-222222222222"),
        )
    )
    controller = evo._encode_length_field(1, identity)
    controller += evo._encode_length_field(2, evo._encode_command(110, 1, 20))
    return evo._encode_length_field(1, controller)


if __name__ == "__main__":
    unittest.main()
