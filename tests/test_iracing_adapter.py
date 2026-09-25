import struct
import tempfile
import unittest
from pathlib import Path

from sim_controls_manager.adapters.iracing import (
    IRacingFormatError,
    ProfileCandidate,
    build_gfcc,
    control_profile_in_text,
    discover,
    inspect_profile,
    parse_gfcc,
)


def synthetic_controls() -> bytes:
    zero = b"\x00" * 16
    instance = bytes.fromhex("E0E54DD97662F1118001444553540000")
    product = bytes.fromhex("4FC20D04760000000000504944564944")
    document = {
        "header": {"version": 2},
        "global_config": bytes.fromhex("deadbeef" * 4),
        "controls": {
            "version": 1,
            "entries": [
                {
                    "name": "PitSpeedLimiter",
                    "unknown": 0,
                    "flags": 6,
                    "binding_type": 2,
                    "value": 1 << 6,
                    "modifiers": 0,
                    "slots": (zero, instance, product),
                },
                {
                    "name": "TractionControlInc",
                    "unknown": 0,
                    "flags": 6,
                    "binding_type": 0,
                    "value": 0,
                    "modifiers": 0,
                    "slots": (zero, zero, zero),
                },
                {
                    "name": "TractionControlDec",
                    "unknown": 0,
                    "flags": 6,
                    "binding_type": 4,
                    "value": 84,
                    "modifiers": 0,
                    "slots": (zero, zero, zero),
                },
            ],
        },
        "trailer": b"  ",
    }
    return build_gfcc(document)


class IRacingAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-iracing-")
        self.root = Path(self.temporary_directory.name) / "iRacing"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_active_profile_parser_ignores_other_sections_and_comments(self) -> None:
        text = (
            "[Misc]\nGlobal=ignore\n\n[ControlProfiles]\n"
            "Global=Oval  \t; active profile\n"
        )
        self.assertEqual(control_profile_in_text(text), "Oval")

    def test_discovers_current_profiles_and_ignores_stale_legacy_file(self) -> None:
        (self.root / "app.ini").write_text(
            "[ControlProfiles]\nGlobal=Oval\n", encoding="utf-8"
        )
        for name in ("Road", "Oval"):
            directory = self.root / "profiles" / "controls" / name
            directory.mkdir(parents=True)
            (directory / "controls.cfg").write_bytes(synthetic_controls())
        (self.root / "controls.cfg").write_bytes(b"stale")

        result = discover(self.root)

        self.assertEqual([profile.name for profile in result.profiles], ["Oval", "Road"])
        self.assertEqual([profile.name for profile in result.profiles if profile.active], ["Oval"])
        self.assertTrue(any("stale legacy" in warning for warning in result.warnings))

    def test_discovers_legacy_controls(self) -> None:
        controls = self.root / "controls.cfg"
        controls.write_bytes(synthetic_controls())
        result = discover(self.root)
        self.assertEqual(len(result.profiles), 1)
        self.assertEqual(result.profiles[0].layout, "legacy")
        self.assertTrue(result.profiles[0].active)

    def test_inspects_three_actions_after_lossless_roundtrip(self) -> None:
        controls = self.root / "controls.cfg"
        data = synthetic_controls()
        controls.write_bytes(data)
        profile = ProfileCandidate("Legacy", controls, True, "legacy")

        inspection = inspect_profile(profile)

        self.assertTrue(inspection.roundtrip_verified)
        self.assertEqual(build_gfcc(parse_gfcc(data)), data)
        actions = {action.action_id: action for action in inspection.actions}
        pit = actions["pit_limiter"]
        self.assertEqual(pit.native_action, "PitSpeedLimiter")
        self.assertEqual(pit.binding.binding_type, "button")
        self.assertEqual(pit.binding.native_button_index, 6)
        self.assertEqual(actions["tc_increase"].binding.binding_type, "unbound")
        self.assertEqual(actions["tc_decrease"].binding.binding_type, "key")

    def test_rejects_corrupt_size(self) -> None:
        data = synthetic_controls()[:-1]
        with self.assertRaisesRegex(IRacingFormatError, "size mismatch"):
            parse_gfcc(data)

    def test_rejects_truncated_lrtc_header(self) -> None:
        payload = b"prefixLRTC"
        data = b"GFCC" + struct.pack("<II", 2, len(payload)) + payload
        with self.assertRaisesRegex(IRacingFormatError, "truncated LRTC"):
            parse_gfcc(data)


if __name__ == "__main__":
    unittest.main()
