import unittest

from sim_controls_manager.adapters.iracing import NativeBinding
from sim_controls_manager.gui import _binding_text


class GuiFormattingTests(unittest.TestCase):
    def test_displays_iracing_zero_based_button_as_user_facing_one_based(self) -> None:
        binding = NativeBinding("button", 6, "instance", "product")
        self.assertEqual(_binding_text(binding), "Button 7")

    def test_formats_non_button_binding(self) -> None:
        binding = NativeBinding("unbound", None, None, None)
        self.assertEqual(_binding_text(binding), "Unbound")


if __name__ == "__main__":
    unittest.main()
