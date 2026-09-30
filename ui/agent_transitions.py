"""Agent workflow state transitions for the presentation layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .animation import AnimationKind, AnimationRequest, AnimationSpec


class AgentVisualState(str, Enum):
    """Stable presentation states for the Agent workflow."""

    IDLE = "idle"
    PROCESSING = "processing"
    UNDERSTANDING_READY = "understanding_ready"
    PLAN_READY = "plan_ready"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass(frozen=True)
class AgentTransitionRule:
    """Presentation rule describing one Agent state transition."""

    source: AgentVisualState
    target: AgentVisualState
    animation: AnimationRequest
    semantic: str


class AgentStateTransitionMapper:
    """Map real Agent workflow state changes to presentation transitions."""

    _RULES = {
        (
            AgentVisualState.IDLE,
            AgentVisualState.PROCESSING,
        ): AgentTransitionRule(
            source=AgentVisualState.IDLE,
            target=AgentVisualState.PROCESSING,
            animation=AnimationRequest(
                source=AgentVisualState.IDLE.value,
                target=AgentVisualState.PROCESSING.value,
                spec=AnimationSpec(
                    kind=AnimationKind.PULSE,
                    duration_ms=240,
                    steps=2,
                ),
            ),
            semantic="active",
        ),
        (
            AgentVisualState.PROCESSING,
            AgentVisualState.UNDERSTANDING_READY,
        ): AgentTransitionRule(
            source=AgentVisualState.PROCESSING,
            target=AgentVisualState.UNDERSTANDING_READY,
            animation=AnimationRequest(
                source=AgentVisualState.PROCESSING.value,
                target=AgentVisualState.UNDERSTANDING_READY.value,
                spec=AnimationSpec(
                    kind=AnimationKind.FADE,
                    duration_ms=180,
                    steps=2,
                ),
            ),
            semantic="informative",
        ),
        (
            AgentVisualState.UNDERSTANDING_READY,
            AgentVisualState.PLAN_READY,
        ): AgentTransitionRule(
            source=AgentVisualState.UNDERSTANDING_READY,
            target=AgentVisualState.PLAN_READY,
            animation=AnimationRequest(
                source=AgentVisualState.UNDERSTANDING_READY.value,
                target=AgentVisualState.PLAN_READY.value,
                spec=AnimationSpec(
                    kind=AnimationKind.FADE,
                    duration_ms=180,
                    steps=2,
                ),
            ),
            semantic="informative",
        ),
        (
            AgentVisualState.PLAN_READY,
            AgentVisualState.WAITING_APPROVAL,
        ): AgentTransitionRule(
            source=AgentVisualState.PLAN_READY,
            target=AgentVisualState.WAITING_APPROVAL,
            animation=AnimationRequest(
                source=AgentVisualState.PLAN_READY.value,
                target=AgentVisualState.WAITING_APPROVAL.value,
                spec=AnimationSpec(
                    kind=AnimationKind.PULSE,
                    duration_ms=300,
                    steps=2,
                ),
            ),
            semantic="pending",
        ),
        (
            AgentVisualState.WAITING_APPROVAL,
            AgentVisualState.EXECUTING,
        ): AgentTransitionRule(
            source=AgentVisualState.WAITING_APPROVAL,
            target=AgentVisualState.EXECUTING,
            animation=AnimationRequest(
                source=AgentVisualState.WAITING_APPROVAL.value,
                target=AgentVisualState.EXECUTING.value,
                spec=AnimationSpec(
                    kind=AnimationKind.PULSE,
                    duration_ms=240,
                    steps=2,
                ),
            ),
            semantic="active",
        ),
        (
            AgentVisualState.EXECUTING,
            AgentVisualState.COMPLETED,
        ): AgentTransitionRule(
            source=AgentVisualState.EXECUTING,
            target=AgentVisualState.COMPLETED,
            animation=AnimationRequest(
                source=AgentVisualState.EXECUTING.value,
                target=AgentVisualState.COMPLETED.value,
                spec=AnimationSpec(
                    kind=AnimationKind.FADE,
                    duration_ms=220,
                    steps=2,
                ),
            ),
            semantic="positive",
        ),
        (
            AgentVisualState.EXECUTING,
            AgentVisualState.FAILED,
        ): AgentTransitionRule(
            source=AgentVisualState.EXECUTING,
            target=AgentVisualState.FAILED,
            animation=AnimationRequest(
                source=AgentVisualState.EXECUTING.value,
                target=AgentVisualState.FAILED.value,
                spec=AnimationSpec(
                    kind=AnimationKind.FADE,
                    duration_ms=220,
                    steps=2,
                ),
            ),
            semantic="negative",
        ),
        (
            AgentVisualState.PLAN_READY,
            AgentVisualState.WARNING,
        ): AgentTransitionRule(
            source=AgentVisualState.PLAN_READY,
            target=AgentVisualState.WARNING,
            animation=AnimationRequest(
                source=AgentVisualState.PLAN_READY.value,
                target=AgentVisualState.WARNING.value,
                spec=AnimationSpec(
                    kind=AnimationKind.PULSE,
                    duration_ms=260,
                    steps=2,
                ),
            ),
            semantic="caution",
        ),
    }

    @classmethod
    def transition(
        cls,
        source: AgentVisualState,
        target: AgentVisualState,
    ) -> AgentTransitionRule | None:
        """Return the presentation rule for a known state transition."""
        return cls._RULES.get((source, target))

    @classmethod
    def has_transition(
        cls,
        source: AgentVisualState,
        target: AgentVisualState,
    ) -> bool:
        return (source, target) in cls._RULES

    @classmethod
    def transitions(cls) -> tuple[AgentTransitionRule, ...]:
        return tuple(cls._RULES.values())


__all__ = [
    "AgentVisualState",
    "AgentTransitionRule",
    "AgentStateTransitionMapper",
]
