import unittest


class VisualSemanticM196Tests(unittest.TestCase):
    def test_visual_semantics_module_exists(self):
        from ui.visual_semantics import VisualSemantic

        self.assertIsNotNone(VisualSemantic)

    def test_visual_semantics_are_immutable(self):
        from ui.visual_semantics import VisualSemantic

        semantic = VisualSemantic()

        with self.assertRaises((AttributeError, TypeError)):
            semantic.neutral = "changed"

    def test_required_semantics_are_exposed(self):
        from ui.visual_semantics import VisualSemantic

        semantic = VisualSemantic()

        for name in (
            "neutral",
            "informative",
            "active",
            "pending",
            "positive",
            "caution",
            "negative",
        ):
            self.assertTrue(hasattr(semantic, name), name)

    def test_semantic_identifiers_are_stable(self):
        from ui.visual_semantics import VisualSemantic

        semantic = VisualSemantic()

        self.assertEqual(semantic.neutral, "neutral")
        self.assertEqual(semantic.informative, "informative")
        self.assertEqual(semantic.active, "active")
        self.assertEqual(semantic.pending, "pending")
        self.assertEqual(semantic.positive, "positive")
        self.assertEqual(semantic.caution, "caution")
        self.assertEqual(semantic.negative, "negative")

    def test_semantic_identifiers_are_distinct(self):
        from ui.visual_semantics import VisualSemantic

        semantic = VisualSemantic()

        identifiers = {
            semantic.neutral,
            semantic.informative,
            semantic.active,
            semantic.pending,
            semantic.positive,
            semantic.caution,
            semantic.negative,
        }

        self.assertEqual(len(identifiers), 7)


if __name__ == "__main__":
    unittest.main()
