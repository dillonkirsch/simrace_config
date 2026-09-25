import codecs
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim_controls_manager.adapters.assetto_corsa import (
    AssettoCorsaFormatError,
    ProfileCandidate,
    build_controls,
    discover,
    inspect_profile,
    is_assetto_corsa_running,
    parse_controls,
    plan_bindings,
)
from sim_controls_manager.catalog import validate_catalog


def synthetic_controls(*, conflict_button: int = -1) -> bytes:
    text = (
        "[HEADER]\r\n"
        "INPUT_METHOD=WHEEL\r\n"
        "\r\n"
        "[CONTROLLERS]\r\n"
        "CON0=Pedals\r\n"
        "PGUID0=AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA\r\n"
        "CON1=SimHub Virtual Controller\r\n"
        "PGUID1=22222222-2222-2222-2222-222222222222\r\n"
        "\r\n"
        "[GEARUP]\r\n"
        "JOY=1\r\n"
        f"BUTTON={conflict_button}\r\n"
        "KEY=-1\r\n"
        "XBOXBUTTON=-1\r\n"
        "\r\n"
        "[TCUP]\r\n"
        "JOY=-1\r\n"
        "BUTTON=-1\r\n"
        "XBOXBUTTON=-1\r\n"
        "KEY=0x54; T\r\n"
        "\r\n"
        "[TCDN]\r\n"
        "JOY=0\r\n"
        "BUTTON=2\r\n"
        "XBOXBUTTON=-1\r\n"
        "KEY=-1\r\n"
        "\r\n"
        "[SHIFTER]\r\n"
        "ACTIVE=1\r\n"
        "JOY=0\r\n"
        "GEAR_1=8\r\n"
        "GEAR_R=14\r\n"
    )
    return codecs.BOM_UTF8 + text.encode("utf-8")


def selected_catalog(*, include_pit: bool = True, with_guid: bool = True):
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
    bindings = [
        {"actionId": "tc_increase", "virtualButton": 8},
        {"actionId": "tc_decrease", "virtualButton": 9},
    ]
    if include_pit:
        bindings.insert(0, {"actionId": "pit_limiter", "virtualButton": 7})
    return validate_catalog(
        {
            "schemaVersion": 1,
            "virtualDevice": device,
            "bindings": bindings,
        }
    )


class AssettoCorsaAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="sim-controls-ac-")
        self.root = Path(self.temporary_directory.name) / "Assetto Corsa"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _profile(self, data: bytes | None = None) -> ProfileCandidate:
        controls = self.root / "cfg" / "controls.ini"
        controls.parent.mkdir(parents=True, exist_ok=True)
        controls.write_bytes(data if data is not None else synthetic_controls())
        return ProfileCandidate("Live", controls, True, "live")

    def test_discovers_live_controls_and_presets(self) -> None:
        self._profile()
        presets = self.root / "cfg" / "controllers" / "presets"
        presets.mkdir(parents=True)
        (presets / "Wheel.ini").write_bytes(synthetic_controls())

        result = discover(self.root)

        self.assertEqual([profile.name for profile in result.profiles], ["Live", "Wheel"])
        self.assertTrue(result.profiles[0].active)
        self.assertFalse(result.profiles[1].active)

    def test_parser_round_trips_bom_crlf_and_unknown_sections(self) -> None:
        source = synthetic_controls()
        document = parse_controls(source)
        self.assertEqual(document.encoding, "utf-8")
        self.assertEqual(document.bom, codecs.BOM_UTF8)
        self.assertEqual(build_controls(document), source)

    def test_rejects_duplicate_sections_and_missing_controllers(self) -> None:
        with self.assertRaisesRegex(AssettoCorsaFormatError, "duplicate"):
            parse_controls(b"[CONTROLLERS]\n[CONTROLLERS]\n")
        with self.assertRaisesRegex(AssettoCorsaFormatError, "CONTROLLERS"):
            parse_controls(b"[TCUP]\nJOY=-1\n")

    def test_inspects_supported_and_unsupported_actions(self) -> None:
        profile = self._profile()
        inspection = inspect_profile(profile)
        actions = {action.action_id: action for action in inspection.actions}

        self.assertTrue(inspection.roundtrip_verified)
        self.assertEqual(actions["pit_limiter"].status, "unsupported")
        self.assertEqual(actions["tc_increase"].binding.binding_type, "key")
        self.assertEqual(actions["tc_decrease"].binding.binding_type, "button")
        self.assertEqual(actions["tc_decrease"].binding.joy_index, 0)
        self.assertEqual(actions["tc_decrease"].binding.native_button_index, 2)

    def test_plans_supported_bindings_and_reports_pit_limiter(self) -> None:
        profile = self._profile()
        source = profile.controls_path.read_bytes()

        plan = plan_bindings(profile, selected_catalog())

        self.assertEqual(plan.unsupported_actions, ("pit_limiter",))
        self.assertEqual(
            [change.action_id for change in plan.changes],
            ["tc_increase", "tc_decrease"],
        )
        self.assertNotEqual(plan.next_bytes, source)
        text = plan.next_bytes.decode("utf-8-sig")
        self.assertIn("[TCUP]\r\nJOY=1\r\nBUTTON=7", text)
        self.assertIn("[TCDN]\r\nJOY=1\r\nBUTTON=8", text)
        self.assertNotIn("KEY=0x54; T", text)
        self.assertEqual(build_controls(parse_controls(plan.next_bytes)), plan.next_bytes)

        profile.controls_path.write_bytes(plan.next_bytes)
        second = plan_bindings(profile, selected_catalog())
        self.assertEqual(second.changes, ())
        self.assertEqual(second.next_bytes, plan.next_bytes)

    def test_matches_controller_by_name_when_catalog_has_no_guids(self) -> None:
        profile = self._profile()
        plan = plan_bindings(profile, selected_catalog(with_guid=False))
        self.assertTrue(plan.changes)
        self.assertTrue(all(change.after.joy_index == 1 for change in plan.changes))

    def test_refuses_directinput_write_for_keyboard_profile(self) -> None:
        profile = self._profile(
            synthetic_controls().replace(b"INPUT_METHOD=WHEEL", b"INPUT_METHOD=KEYBOARD")
        )
        with self.assertRaisesRegex(ValueError, "select Wheel controls"):
            plan_bindings(profile, selected_catalog())

    def test_rejects_missing_controller_and_existing_button_conflict(self) -> None:
        profile = self._profile(synthetic_controls(conflict_button=7))
        with self.assertRaisesRegex(ValueError, "GEARUP"):
            plan_bindings(profile, selected_catalog())

        missing = validate_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "Missing controller",
                },
                "bindings": [{"actionId": "tc_increase", "virtualButton": 8}],
            }
        )
        with self.assertRaisesRegex(ValueError, r"not in \[CONTROLLERS\]"):
            plan_bindings(profile, missing)

    def test_pit_only_catalog_is_a_noop_with_explicit_unsupported_result(self) -> None:
        profile = self._profile()
        catalog = validate_catalog(
            {
                "schemaVersion": 1,
                "virtualDevice": {
                    "provider": "simhub-control-mapper",
                    "identity": "Anything",
                },
                "bindings": [{"actionId": "pit_limiter", "virtualButton": 7}],
            }
        )
        plan = plan_bindings(profile, catalog)
        self.assertEqual(plan.changes, ())
        self.assertEqual(plan.unsupported_actions, ("pit_limiter",))

    @mock.patch("sim_controls_manager.adapters.assetto_corsa.subprocess.run")
    def test_process_guard_blocks_game_and_fails_closed(self, run) -> None:
        run.return_value.returncode = 0
        run.return_value.stdout = '"acs.exe","123"\n'
        self.assertTrue(is_assetto_corsa_running())
        run.return_value.returncode = 1
        run.return_value.stdout = ""
        self.assertTrue(is_assetto_corsa_running())


if __name__ == "__main__":
    unittest.main()
