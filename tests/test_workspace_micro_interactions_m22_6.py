import unittest

from ui.animation import AnimationKind
from ui.workspace_interactions import (
    WorkspaceInteraction,
    WorkspaceInteractionMapper,
)


class WorkspaceMicroInteractionsM226Tests(unittest.TestCase):

    def test_selection_has_active_feedback(self):
        effect = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.SELECT
        )
        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "active")
        self.assertEqual(effect.animation.kind, AnimationKind.FADE)

    def test_deselection_returns_to_neutral(self):
        effect = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.DESELECT
        )
        self.assertEqual(effect.semantic, "neutral")

    def test_expand_and_collapse_have_distinct_effects(self):
        expand = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.EXPAND
        )
        collapse = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.COLLAPSE
        )
        self.assertEqual(expand.animation.kind, AnimationKind.SLIDE)
        self.assertEqual(collapse.animation.kind, AnimationKind.SLIDE)
        self.assertNotEqual(
            expand.animation.duration_ms,
            collapse.animation.duration_ms,
        )

    def test_focus_is_informative(self):
        effect = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.FOCUS
        )
        self.assertEqual(effect.semantic, "informative")

    def test_empty_transition_is_visualized(self):
        self.assertTrue(
            WorkspaceInteractionMapper.has_effect(
                WorkspaceInteraction.ENTER_EMPTY
            )
        )
        self.assertTrue(
            WorkspaceInteractionMapper.has_effect(
                WorkspaceInteraction.EXIT_EMPTY
            )
        )

    def test_all_workspace_interactions_are_mapped(self):
        self.assertEqual(
            len(WorkspaceInteractionMapper.effects()),
            len(WorkspaceInteraction),
        )

    def test_effect_is_immutable(self):
        effect = WorkspaceInteractionMapper.effect(
            WorkspaceInteraction.ACTIVATE
        )
        with self.assertRaises(AttributeError):
            effect.semantic = "error"

    def test_unknown_transition_returns_none(self):
        self.assertIsNone(
            WorkspaceInteractionMapper.effect("unknown")
        )


if __name__ == "__main__":
    unittest.main()
