import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager.adapters.le_mans_ultimate import (
    ProfileCandidate,
    discover,
    inspect_profile,
    is_lmu_running,
    plan_bindings,
    validate_controls_bytes,
)
from sim_controls_manager.catalog import validate_catalog


VIRTUAL_KEY = "SimHub Virtual Controller-ABCDEF"


def synthetic_preset(*, input_entries=None, virtual_type="Wheel", buttons=32, duplicate=False):
    devices = {
        "Pedals-111": {
            "Type": "Pedals",
            "instance name": "Pedals",
            "layout": {"axes": 3, "buttons": 0, "povs": 0},
        },
        VIRTUAL_KEY: {
            "Type": virtual_type,
            "instance name": "SimHub Virtual Controller",
            "layout": {"axes": 0, "buttons": buttons, "povs": 0},
        },
    }
    if duplicate:
        devices["SimHub Virtual Controller-OTHER"] = {
            "Type": "Wheel",
            "instance name": "SimHub Virtual Controller",
            "layout": {"axes": 0, "buttons": 32, "povs": 0},
        }
    value = {
        "Alternative Input": {
            "Speed Limiter": {"device": "Keyboard", "id": 76}
        },
        "Devices": devices,
        "Input": input_entries
        or {
            "Throttle": {"device": "Pedals-111", "id": 0},
            "Shift Up": {"device": VIRTUAL_KEY, "id": 50},
        },
        "Type": "Direct Input",
    }
    return json.dumps(value, ensure_ascii=False, indent=4).replace("\n", "\r\n").encode()


def selected_catalog(identity="SimHub Virtual Controller"):
    return validate_catalog(
        {
            "schemaVersion": 1,
            "virtualDevice": {
                "provider": "simhub-control-mapper",
                "identity": identity,
            },
            "bindings": [
                {"actionId": "pit_limiter", "virtualButton": 7},
                {"actionId": "tc_increase", "virtualButton": 8},
                {"actionId": "tc_decrease", "virtualButton": 9},
            ],
        }
    )


class LeMansUltimateAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-lmu-")
        self.root = Path(self.temporary_directory.name) / "Le Mans Ultimate"
        self.preset_directory = self.root / "UserData" / "Controller" / "Presets"
        self.preset_directory.mkdir(parents=True)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _profile(self, data=None, name="Tablet Shortcuts"):
        path = self.preset_directory / f"{name}.JSON"
        path.write_bytes(data or synthetic_preset())
        return ProfileCandidate(name, path, False, "preset")

    def test_discovers_json_presets(self):
        self._profile()
        result = discover(self.root)
        self.assertEqual(result.lmu_directory, self.root.resolve())
        self.assertEqual([item.name for item in result.profiles], ["Tablet Shortcuts"])
        self.assertFalse(result.profiles[0].active)

    def test_inspection_reports_supported_unbound_shortcuts(self):
        inspection = inspect_profile(self._profile())
        self.assertEqual(inspection.input_type, "Direct Input")
        self.assertTrue(inspection.source_verified)
        self.assertTrue(all(action.status == "supported" for action in inspection.actions))
        self.assertTrue(all(action.binding.binding_type == "unbound" for action in inspection.actions))

    def test_adds_only_shortcuts_and_is_idempotent(self):
        profile = self._profile()
        source = json.loads(profile.controls_path.read_bytes())
        plan = plan_bindings(profile, selected_catalog())
        self.assertEqual(len(plan.changes), 3)
        self.assertTrue(validate_controls_bytes(plan.next_bytes))
        updated = json.loads(plan.next_bytes)
        self.assertEqual(updated["Input"]["Speed Limiter"], {"device": VIRTUAL_KEY, "id": 38})
        self.assertEqual(updated["Input"]["Traction Control Up"]["id"], 39)
        self.assertEqual(updated["Input"]["Traction Control Down"]["id"], 40)
        self.assertEqual(updated["Input"]["Throttle"], source["Input"]["Throttle"])
        self.assertEqual(updated["Input"]["Shift Up"], source["Input"]["Shift Up"])
        self.assertEqual(updated["Devices"], source["Devices"])
        self.assertEqual(updated["Alternative Input"], source["Alternative Input"])

        profile.controls_path.write_bytes(plan.next_bytes)
        second = plan_bindings(profile, selected_catalog())
        self.assertEqual(second.changes, ())
        self.assertEqual(second.next_bytes, plan.next_bytes)

    def test_updates_existing_target_without_touching_other_actions(self):
        inputs = {
            "Speed Limiter": {"device": "Old Wheel", "id": 34},
            "Shift Down": {"device": VIRTUAL_KEY, "id": 55},
        }
        plan = plan_bindings(self._profile(synthetic_preset(input_entries=inputs)), selected_catalog())
        updated = json.loads(plan.next_bytes)
        self.assertEqual(updated["Input"]["Speed Limiter"]["id"], 38)
        self.assertEqual(updated["Input"]["Shift Down"], inputs["Shift Down"])

    def test_rejects_conflict_pedals_ambiguity_and_capacity(self):
        conflict = {"Shift Up": {"device": VIRTUAL_KEY, "id": 38}}
        with self.assertRaisesRegex(ValueError, "Shift Up"):
            plan_bindings(self._profile(synthetic_preset(input_entries=conflict)), selected_catalog())
        with self.assertRaisesRegex(ValueError, "marked as pedals"):
            plan_bindings(self._profile(synthetic_preset(virtual_type="Pedals")), selected_catalog())
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            plan_bindings(self._profile(synthetic_preset(duplicate=True)), selected_catalog())
        with self.assertRaisesRegex(ValueError, "button 9"):
            plan_bindings(self._profile(synthetic_preset(buttons=8)), selected_catalog())

    def test_requires_virtual_controller_to_be_present_in_preset(self):
        with self.assertRaisesRegex(ValueError, "is not in this preset"):
            plan_bindings(self._profile(), selected_catalog("Missing Controller"))

    @mock.patch("sim_controls_manager.adapters.le_mans_ultimate.subprocess.run")
    def test_process_guard_blocks_lmu(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = '"Le Mans Ultimate.exe","123"\n'
        self.assertTrue(is_lmu_running())


if __name__ == "__main__":
    unittest.main()
