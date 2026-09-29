"""Semantic mapping between visual interaction states and visual semantics."""

from .visual_interaction import VisualInteractionState
from .visual_semantics import VisualSemantic


class VisualSemanticMapper:
    """Map interaction states to stable visual semantic categories."""

    def __init__(
        self,
        interaction_state: VisualInteractionState | None = None,
        semantic: VisualSemantic | None = None,
    ) -> None:
        self.interaction_state = interaction_state or VisualInteractionState()
        self.semantic = semantic or VisualSemantic()

        self._state_to_semantic = {
            self.interaction_state.idle: self.semantic.neutral,
            self.interaction_state.ready: self.semantic.informative,
            self.interaction_state.running: self.semantic.active,
            self.interaction_state.waiting: self.semantic.pending,
            self.interaction_state.success: self.semantic.positive,
            self.interaction_state.warning: self.semantic.caution,
            self.interaction_state.error: self.semantic.negative,
        }

        self._semantic_to_color_token = {
            self.semantic.neutral: "text_secondary",
            self.semantic.informative: "info",
            self.semantic.active: "agent_running",
            self.semantic.pending: "warning",
            self.semantic.positive: "success",
            self.semantic.caution: "warning",
            self.semantic.negative: "error",
        }

    def semantic_for(self, state: str) -> str:
        """Return the semantic category associated with an interaction state."""
        return self._state_to_semantic[state]

    def color_token_for(self, semantic: str) -> str:
        """Return the VisualTokens color key associated with a semantic."""
        return self._semantic_to_color_token[semantic]
