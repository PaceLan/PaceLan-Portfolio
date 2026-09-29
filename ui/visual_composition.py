"""Immutable UX composition contracts for the UI design system."""

from dataclasses import dataclass

from .visual_components import Navigation, Panel, State, Workspace
from .visual_interaction import VisualInteractionState
from .visual_layout import WorkspaceLayout
from .visual_semantics import VisualSemantic
from .visual_tokens import VisualTokens, DEFAULT_VISUAL_TOKENS


@dataclass(frozen=True)
class UXComposition:
    """Immutable composition of the M19 visual design-system contracts."""

    tokens: VisualTokens = DEFAULT_VISUAL_TOKENS
    panel: Panel = Panel()
    navigation: Navigation = Navigation()
    workspace: Workspace = Workspace()
    state: State = State()
    layout: WorkspaceLayout = WorkspaceLayout()
    interaction: VisualInteractionState = VisualInteractionState()
    semantics: VisualSemantic = VisualSemantic()


DEFAULT_UX_COMPOSITION = UXComposition()
