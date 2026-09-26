import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from sim_controls_manager import cli
from sim_controls_manager.adapters.automobilista_2 import (
    Automobilista2FormatError,
    ProfileCandidate,
    analyze_container,
    discover,
    inspect_profile,
    plan_bindings,
    validate_controls_bytes,
)
from sim_controls_manager.catalog import validate_catalog


def synthetic_save(declared_length=36, blocks=None):
    blocks = blocks or (b"A" * 16, b"B" * 16, b"A" * 16)
    payload = b"".join(blocks)
    return struct.pack("<II", 0xC12C3429, declared_length) + payload


class Automobilista2AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-ams2-")
        self.root = Path(self.temporary_directory.name) / "Automobilista 2"
        self.profiles = (
            self.root / "savegame" / "123456" / "automobilista 2" / "profiles"
        )
        self.profiles.mkdir(parents=True)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _profile(self):
        path = self.profiles / "default.controllersettings.v1.03.sav"
        path.write_bytes(synthetic_save())
        return ProfileCandidate(
            "123456/default", path, False, "twofish-save", "123456", "1.03"
        )

    def test_discovers_account_and_format_version(self):
        self._profile()
        result = discover(self.root)
        self.assertEqual(result.automobilista_2_directory, self.root.resolve())
        self.assertEqual(len(result.profiles), 1)
        self.assertEqual(result.profiles[0].name, "123456/default")
        self.assertEqual(result.profiles[0].format_version, "1.03")
        self.assertFalse(result.profiles[0].active)
        self.assertIn("read-only", result.warnings[0])

    def test_ignores_unrelated_saves(self):
        (self.profiles / "default.sav").write_bytes(b"unrelated")
        result = discover(self.root)
        self.assertEqual(result.profiles, ())

    def test_validates_container_and_counts_repeated_blocks(self):
        info = analyze_container(synthetic_save())
        self.assertEqual(info.header_word, 0xC12C3429)
        self.assertEqual(info.declared_length, 36)
        self.assertEqual(info.encrypted_length, 48)
        self.assertEqual(info.padding_length, 12)
        self.assertEqual(info.encrypted_blocks, 3)
        self.assertEqual(info.repeated_blocks, 1)
        self.assertTrue(validate_controls_bytes(synthetic_save()))

    def test_rejects_misaligned_or_impossible_payload_lengths(self):
        self.assertFalse(validate_controls_bytes(b"short"))
        self.assertFalse(validate_controls_bytes(struct.pack("<II", 0, 16) + b"x" * 17))
        self.assertFalse(validate_controls_bytes(synthetic_save(declared_length=12)))
        with self.assertRaisesRegex(Automobilista2FormatError, "inconsistent"):
            analyze_container(synthetic_save(declared_length=48))

    def test_inspection_reports_explicit_write_gate(self):
        inspection = inspect_profile(self._profile())
        self.assertFalse(inspection.source_verified)
        self.assertFalse(inspection.write_supported)
        self.assertEqual(
            [action.status for action in inspection.actions],
            ["format_locked", "format_locked", "format_locked"],
        )
        self.assertEqual(
            inspection.actions[0].native_action, "Toggle Pit Speed Limiter"
        )

    def test_plan_refuses_to_guess_at_encrypted_payload(self):
        catalog = validate_catalog(
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
        with self.assertRaisesRegex(Automobilista2FormatError, "writes are locked"):
            plan_bindings(self._profile(), catalog)

    def test_cli_discovers_and_inspects_without_write_commands(self):
        self._profile()
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(cli.main(["ams2", "discover", "--root", str(self.root)]), 0)
            self.assertEqual(cli.main(["ams2", "inspect", "--root", str(self.root)]), 0)
        text = output.getvalue()
        self.assertIn("123456/default", text)
        self.assertIn("Twofish-encrypted SAV container v1.03", text)
        self.assertIn("writes stay disabled", text)
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["ams2", "apply"])


if __name__ == "__main__":
    unittest.main()
