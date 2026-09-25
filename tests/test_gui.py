import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sim_controls_manager.adapters.iracing import DeviceInfo, NativeBinding
from sim_controls_manager.gui import _binding_text, _source_signature


class GuiFormattingTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
