import json
import tempfile
import unittest
from pathlib import Path

from sim_controls_manager import simhub


def settings(buttons=None):
    return {
        "OutputMode": 0,
        "VJoyMapping": {"TargetVJoyId": 1},
        "OutputMapping": {
            "ControllerMapping": {
                "Buttons": buttons
                if buttons is not None
                else [
                    {"ButtonId": 19, "TargetRole": "PitLimiter"},
                    {"ButtonId": 7, "TargetRole": "TractionControl+"},
                    {"ButtonId": 6, "TargetRole": "TractionControl-"},
                    {"ButtonId": 100, "TargetRole": "UnrelatedRole"},
                ]
            }
        },
    }


class SimHubTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "settings.json"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def test_reads_three_roles_and_converts_zero_based_button_ids(self):
        self.write(settings())

        result = simhub.inspect_control_mapper(self.path)

        self.assertEqual(result.output_mode, 0)
        self.assertEqual(result.target_vjoy_id, 1)
        self.assertEqual(
            [(binding.action_id, binding.virtual_button) for binding in result.bindings],
            [("pit_limiter", 20), ("tc_increase", 8), ("tc_decrease", 7)],
        )
        self.assertEqual(result.missing_actions, ())

    def test_reports_missing_core_role(self):
        self.write(settings([{"ButtonId": 19, "TargetRole": "PitLimiter"}]))

        result = simhub.inspect_control_mapper(self.path)

        self.assertEqual(
            result.missing_actions, ("tc_increase", "tc_decrease")
        )

    def test_rejects_duplicate_core_role(self):
        self.write(
            settings(
                [
                    {"ButtonId": 1, "TargetRole": "PitLimiter"},
                    {"ButtonId": 2, "TargetRole": "PitLimiter"},
                ]
            )
        )

        with self.assertRaisesRegex(ValueError, "mapped more than once"):
            simhub.inspect_control_mapper(self.path)

    def test_rejects_invalid_button_id(self):
        self.write(settings([{"ButtonId": True, "TargetRole": "PitLimiter"}]))

        with self.assertRaisesRegex(ValueError, "invalid ButtonId"):
            simhub.inspect_control_mapper(self.path)

    def test_reports_unreadable_or_malformed_settings(self):
        with self.assertRaisesRegex(ValueError, "could not read SimHub settings"):
            simhub.inspect_control_mapper(self.path)

        self.path.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "could not read SimHub settings"):
            simhub.inspect_control_mapper(self.path)


if __name__ == "__main__":
    unittest.main()
