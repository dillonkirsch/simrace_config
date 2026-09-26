import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from sim_controls_manager.adapters.assetto_corsa import NativeBinding as ACNativeBinding
from sim_controls_manager.adapters.acc import NativeBinding as ACCNativeBinding
from sim_controls_manager.adapters.assetto_corsa_evo import (
    NativeBinding as EVONativeBinding,
)
from sim_controls_manager.adapters.iracing import DeviceInfo, NativeBinding
from sim_controls_manager.adapters.le_mans_ultimate import NativeBinding as LMUNativeBinding
from sim_controls_manager import gui
from sim_controls_manager.control_names import NativeControlName
from sim_controls_manager.gui import (
    _binding_text,
    _assetto_corsa_binding_text,
    _acc_binding_text,
    _assetto_corsa_evo_binding_text,
    _lmu_binding_text,
    _matching_control_ids,
    _matching_tablet_shortcut_ids,
    _native_control_text,
    _source_signature,
)


class GuiFormattingTests(unittest.TestCase):
    def test_formats_evo_button_as_user_facing_one_based(self) -> None:
        binding = EVONativeBinding("button", 6, 1, "instance", "SimHub", None)
        self.assertEqual(
            _assetto_corsa_evo_binding_text(binding), "Button 7 • SimHub"
        )

    def test_formats_lmu_button_as_simhub_one_based(self) -> None:
        binding = LMUNativeBinding("button", 38, 7, "virtual-key", "SimHub")
        self.assertEqual(_lmu_binding_text(binding), "Button 7 • SimHub")

    def test_formats_acc_button_as_user_facing_one_based(self) -> None:
        binding = ACCNativeBinding("button", 6, 2, "instance", "SimHub")
        self.assertEqual(_acc_binding_text(binding), "Button 7 • Device 2")

    def test_formats_assetto_corsa_button_as_user_facing_one_based(self) -> None:
        binding = ACNativeBinding("button", 1, 6, None, None)
        self.assertEqual(
            _assetto_corsa_binding_text(binding),
            "Button 7 • Controller 1",
        )

    def test_formats_native_control_names_and_mapping_statuses(self) -> None:
        self.assertEqual(_native_control_text(NativeControlName(("Throttle",))), "Throttle")
        self.assertEqual(
            _native_control_text(NativeControlName(("Cycle TC",), "compound")),
            "Cycle TC (combined)",
        )
        self.assertEqual(
            _native_control_text(NativeControlName(status="not_exposed")),
            "Not exposed",
        )
        self.assertEqual(
            _native_control_text(NativeControlName(status="not_observed")),
            "Not observed",
        )

    def test_control_search_matches_central_and_native_names(self) -> None:
        self.assertIn("accelerator", _matching_control_ids("throttle"))
        self.assertIn("pit_limiter", _matching_control_ids("pit speed limiter"))
        self.assertIn("tc_increase", _matching_control_ids("TractionControlInc"))
        self.assertEqual(_matching_control_ids("not-a-real-control-name"), ())

    def test_tablet_shortcuts_exclude_driving_inputs_and_shifting(self) -> None:
        shortcuts = _matching_tablet_shortcut_ids("")
        for excluded in (
            "steering",
            "accelerator",
            "brake",
            "clutch",
            "handbrake",
            "shift_up",
            "shift_down",
            "gear_1",
            "reverse_gear",
        ):
            self.assertNotIn(excluded, shortcuts)
        self.assertIn("pit_limiter", shortcuts)
        self.assertIn("tc_increase", shortcuts)
        self.assertIn("headlights", shortcuts)

    def test_displays_iracing_zero_based_button_as_user_facing_one_based(self) -> None:
        binding = NativeBinding("button", 6, "instance", "product")
        self.assertEqual(_binding_text(binding), "Button 7")

    def test_formats_non_button_binding(self) -> None:
        binding = NativeBinding("unbound", None, None, None)
        self.assertEqual(_binding_text(binding), "Unbound")

    def test_live_signature_changes_with_profiles_settings_and_devices(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            profiles = root / "profiles" / "controls" / "Road"
            profiles.mkdir(parents=True)
            controls = profiles / "controls.cfg"
            controls.write_bytes(b"first")
            settings = root / "simhub.json"
            settings.write_text("{}", encoding="utf-8")

            original = _source_signature(root, settings, ())
            controls.write_bytes(b"second and larger")
            changed_file = _source_signature(root, settings, ())
            self.assertNotEqual(original, changed_file)

            with_device = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
            )
            self.assertNotEqual(changed_file, with_device)

            ac_root = root / "Assetto Corsa"
            ac_controls = ac_root / "cfg" / "controls.ini"
            ac_controls.parent.mkdir(parents=True)
            ac_controls.write_text("[CONTROLLERS]\n", encoding="utf-8")
            with_ac = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
                ac_root,
            )
            self.assertNotEqual(with_device, with_ac)

            acc_root = root / "Assetto Corsa Competizione"
            acc_controls = acc_root / "Config" / "controls.json"
            acc_controls.parent.mkdir(parents=True)
            acc_controls.write_text("{}", encoding="utf-8")
            with_acc = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
                ac_root,
                acc_root,
            )
            self.assertNotEqual(with_ac, with_acc)

            lmu_root = root / "Le Mans Ultimate"
            lmu_preset = lmu_root / "UserData" / "Controller" / "Presets" / "Tablet.json"
            lmu_preset.parent.mkdir(parents=True)
            lmu_preset.write_text("{}", encoding="utf-8")
            with_lmu = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
                ac_root,
                acc_root,
                lmu_root,
            )
            self.assertNotEqual(with_acc, with_lmu)

            evo_root = root / "ACE"
            evo_root.mkdir()
            (evo_root / "input_devices.inputdeviceconfiguration").write_bytes(b"test")
            with_evo = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
                ac_root,
                acc_root,
                lmu_root,
                evo_root,
            )
            self.assertNotEqual(with_lmu, with_evo)

            ams2_root = root / "Automobilista 2"
            ams2_controls = (
                ams2_root
                / "savegame"
                / "123456"
                / "automobilista 2"
                / "profiles"
                / "default.controllersettings.v1.03.sav"
            )
            ams2_controls.parent.mkdir(parents=True)
            ams2_controls.write_bytes(b"encrypted")
            with_ams2 = _source_signature(
                root,
                settings,
                (DeviceInfo("instance", "product", "SimHub vJoy"),),
                ac_root,
                acc_root,
                lmu_root,
                evo_root,
                ams2_root,
            )
            self.assertNotEqual(with_evo, with_ams2)

    def test_smoke_mode_builds_and_closes_without_starting_event_loop(self) -> None:
        with mock.patch.object(gui, "SimControlsApp") as app_type:
            app = app_type.return_value
            self.assertEqual(gui.main(smoke_test=True), 0)
        app.withdraw.assert_called_once_with()
        app.update_idletasks.assert_called_once_with()
        app._close.assert_called_once_with()
        app.mainloop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
