import unittest
from ui.ambient_effects import AmbientFieldController, AmbientLayer

class M262AmbientFieldTests(unittest.TestCase):
    def test_default_field_has_multiple_layers(self):
        field = AmbientFieldController().snapshot(0.0)
        self.assertGreaterEqual(len(field.layers), 3)

    def test_layers_are_soft_and_slow(self):
        field = AmbientFieldController().snapshot(0.0)
        self.assertTrue(all(layer.opacity <= 0.2 for layer in field.layers))
        self.assertTrue(all(layer.cycle_ms >= 20000 for layer in field.layers))

    def test_snapshot_is_deterministic(self):
        controller = AmbientFieldController()
        first = controller.snapshot(0.25)
        second = controller.snapshot(0.25)
        self.assertEqual(first, second)

    def test_intensity_changes_field(self):
        controller = AmbientFieldController()
        controller.set_intensity(0.5)
        state = controller.snapshot(0.0)
        self.assertEqual(state.intensity, 0.5)

if __name__ == "__main__":
    unittest.main()
