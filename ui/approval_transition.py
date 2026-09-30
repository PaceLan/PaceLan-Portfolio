"""Presentation-layer approval transition mapping for M22.4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ui.animation import AnimationKind, AnimationSpec


class ApprovalVisualState(str, Enum):
    PLAN_READY = "plan_ready"
    RISK_DETECTED = "risk_detected"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"


@dataclass(frozen=True)
class ApprovalTransition:
    source: ApprovalVisualState
    target: ApprovalVisualState
    animation: AnimationSpec
    semantic: str

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("approval transition source and target must differ")


class ApprovalTransitionMapper:
    """Maps approval workflow state changes to presentation transitions."""

    _TRANSITIONS = {
        (
            ApprovalVisualState.PLAN_READY,
            ApprovalVisualState.RISK_DETECTED,
        ): ApprovalTransition(
            ApprovalVisualState.PLAN_READY,
            ApprovalVisualState.RISK_DETECTED,
            AnimationSpec(AnimationKind.PULSE, 260, 2),
            "caution",
        ),
        (
            ApprovalVisualState.RISK_DETECTED,
            ApprovalVisualState.WAITING_APPROVAL,
        ): ApprovalTransition(
            ApprovalVisualState.RISK_DETECTED,
            ApprovalVisualState.WAITING_APPROVAL,
            AnimationSpec(AnimationKind.PULSE, 300, 2),
            "pending",
        ),
        (
            ApprovalVisualState.PLAN_READY,
            ApprovalVisualState.WAITING_APPROVAL,
        ): ApprovalTransition(
            ApprovalVisualState.PLAN_READY,
            ApprovalVisualState.WAITING_APPROVAL,
            AnimationSpec(AnimationKind.PULSE, 300, 2),
            "pending",
        ),
        (
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.APPROVED,
        ): ApprovalTransition(
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.APPROVED,
            AnimationSpec(AnimationKind.FADE, 180, 1),
            "positive",
        ),
        (
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.REJECTED,
        ): ApprovalTransition(
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.REJECTED,
            AnimationSpec(AnimationKind.FADE, 180, 1),
            "negative",
        ),
        (
            ApprovalVisualState.APPROVED,
            ApprovalVisualState.EXECUTING,
        ): ApprovalTransition(
            ApprovalVisualState.APPROVED,
            ApprovalVisualState.EXECUTING,
            AnimationSpec(AnimationKind.PULSE, 240, 2),
            "active",
        ),
    }

    @classmethod
    def transition(
        cls,
        source: ApprovalVisualState,
        target: ApprovalVisualState,
    ) -> ApprovalTransition | None:
        return cls._TRANSITIONS.get((source, target))

    @classmethod
    def has_transition(
        cls,
        source: ApprovalVisualState,
        target: ApprovalVisualState,
    ) -> bool:
        return (source, target) in cls._TRANSITIONS

    @classmethod
    def transitions(cls) -> tuple[ApprovalTransition, ...]:
        return tuple(cls._TRANSITIONS.values())


__all__ = [
    "ApprovalVisualState",
    "ApprovalTransition",
    "ApprovalTransitionMapper",
]