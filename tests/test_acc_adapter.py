import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager.adapters.acc import (
    ACCFormatError,
    ProfileCandidate,
    discover,
    inspect_profile,
    is_acc_running,
    plan_bindings,
    validate_controls_bytes,
)
from sim_controls_manager.catalog import validate_catalog


def _button(action: str, index: int) -> dict:
    return {
        "buttonIndex": index,
        "powIndex": -1,
        "powValue": 0,
        "keyName": "None",
        "gamepadButtonName": "None",
        "instantActionCode": action,
        "extendedActionCode": "None",
        "extendedTime": 2,
        "pinkieInstanceActionCode": "None",
        "pinkieExtendedActionCode": "None",
    }


def synthetic_controls(
    *,
    virtual_buttons: list[dict] | None = None,
    virtual_is_pedals: int = 0,
) -> bytes:
    value = {
        "version": 0,
        "enableManufacturerExtras": 1,
        "configurationName": "Test",
        "commandDevices": [
            {
                "version": 0,
                "productName": "Pedals",
                "productId": "pedals-product",
                "instanceGuid": "{AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA}",
                "isGamePad": 0,
                "isPedals": 1,
                "uICommandButtonList": [],
                "raceCommandButtonList": [],
                "raceCommandAxisList": [{"axisIndex": 0, "actionCode": "Gas"}],
                "unknownSetting": 73,
            },
            {
                "version": 0,
                "productName": "SimHub Virtual Controller",
                "productId": "virtual-product",
                "instanceGuid": "{11111111-1111-1111-1111-111111111111}",
                "isGamePad": 0,
                "isPedals": virtual_is_pedals,
                "uICommandButtonList": [],
                "raceCommandButtonList": virtual_buttons or [],
                "raceCommandAxisList": [],
                "unknownSetting": 99,
            },
        ],
        "gamepadSettings": {"raceCommandButtonList": []},
        "keyboardSettings": {"raceCommandButtonList": []},
        "comment": "preserve me",
    }
    # Match the game's CRLF/tab layout closely enough to exercise textual patching.
    return json.dumps(value, ensure_ascii=False, indent="\t").replace("\n", "\r\n").encode("utf-8")


def selected_catalog(*, with_guid: bool = True):
    device = {
        "provider": "simhub-control-mapper",
        "identity": "SimHub Virtual Controller",
    }
    if with_guid:
        device.update(
            {
                "instanceGuid": "11111111-1111-1111-1111-111111111111",
                "productGuid": "22222222-2222-2222-2222-222222222222",
            }
        )
    return validate_catalog(
        {
            "schemaVersion": 1,
            "virtualDevice": device,
            "bindings": [
                {"actionId": "pit_limiter", "virtualButton": 7},
                {"actionId": "tc_increase", "virtualButton": 8},
                {"actionId": "tc_decrease", "virtualButton": 9},
            ],
        }
    )


class ACCAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-acc-")
        self.root = Path(self.temporary_directory.name) / "Assetto Corsa Competizione"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _profile(self, data: bytes | None = None) -> ProfileCandidate:
        path = self.root / "Config" / "controls.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if data is not None else synthetic_controls())
        return ProfileCandidate("Live", path, True, "live")

    def test_discovers_live_profile(self) -> None:
        self._profile()
        result = discover(self.root)
        self.assertEqual(len(result.profiles), 1)
        self.assertEqual(result.profiles[0].name, "Live")
        self.assertTrue(result.profiles[0].active)

    def test_inspection_reports_missing_shortcuts_as_supported_and_unbound(self) -> None:
        inspection = inspect_profile(self._profile())
        self.assertTrue(inspection.source_verified)
        self.assertEqual(inspection.version, 0)
        self.assertTrue(all(action.status == "supported" for action in inspection.actions))
        self.assertTrue(
            all(action.binding.binding_type == "unbound" for action in inspection.actions)
        )

    def test_adds_only_shortcut_buttons_and_is_idempotent(self) -> None:
        profile = self._profile()
        source = profile.controls_path.read_bytes()
        plan = plan_bindings(profile, selected_catalog())

        self.assertEqual(len(plan.changes), 3)
        self.assertNotEqual(plan.next_bytes, source)
        self.assertTrue(validate_controls_bytes(plan.next_bytes))
        next_value = json.loads(plan.next_bytes)
        virtual = next_value["commandDevices"][1]
        self.assertEqual(virtual["raceCommandAxisList"], [])
        self.assertEqual(virtual["unknownSetting"], 99)
        self.assertEqual(next_value["commandDevices"][0]["raceCommandAxisList"][0]["actionCode"], "Gas")
        by_action = {
            item["instantActionCode"]: item
            for item in virtual["raceCommandButtonList"]
        }
        self.assertEqual(by_action["PitLimiter"]["buttonIndex"], 6)
        self.assertEqual(by_action["IncreaseTC"]["buttonIndex"], 7)
        self.assertEqual(by_action["DecreaseTC"]["buttonIndex"], 8)

        profile.controls_path.write_bytes(plan.next_bytes)
        second = plan_bindings(profile, selected_catalog())
        self.assertEqual(second.changes, ())
        self.assertEqual(second.next_bytes, plan.next_bytes)

    def test_updates_existing_action_without_rewriting_unrelated_json(self) -> None:
        original_entry = _button("IncreaseTC", 2)
        data = synthetic_controls(virtual_buttons=[original_entry])
        profile = self._profile(data)
        plan = plan_bindings(profile, selected_catalog())
        self.assertIn(b'"comment": "preserve me"', plan.next_bytes)
        self.assertIn(b'"unknownSetting": 99', plan.next_bytes)
        self.assertEqual(json.loads(plan.next_bytes)["commandDevices"][1]["raceCommandButtonList"][1]["instantActionCode"], "PitLimiter")

    def test_matches_device_by_name_without_guids(self) -> None:
        plan = plan_bindings(self._profile(), selected_catalog(with_guid=False))
        self.assertTrue(plan.changes)
        self.assertTrue(all(change.after.device_index == 1 for change in plan.changes))

    def test_rejects_pedals_and_existing_button_conflict(self) -> None:
        pedal_profile = self._profile(synthetic_controls(virtual_is_pedals=1))
        with self.assertRaisesRegex(ValueError, "marked as pedals"):
            plan_bindings(pedal_profile, selected_catalog())

        conflict_profile = self._profile(
            synthetic_controls(virtual_buttons=[_button("ShiftUp", 6)])
        )
        with self.assertRaisesRegex(ValueError, "ShiftUp"):
            plan_bindings(conflict_profile, selected_catalog())

    def test_rejects_unknown_version(self) -> None:
        data = synthetic_controls().replace(b'"version": 0', b'"version": 9', 1)
        with self.assertRaisesRegex(ACCFormatError, "version"):
            inspect_profile(self._profile(data))

    @mock.patch("sim_controls_manager.adapters.acc.subprocess.run")
    def test_process_guard_blocks_shipping_executable(self, run) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = '"AC2-Win64-Shipping.exe","123"\n'
        self.assertTrue(is_acc_running())


if __name__ == "__main__":
    unittest.main()
