"""Immutable visual semantic definitions for the UI layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSemantic:
    """Stable semantic categories used by the visual system."""

    neutral: str = "neutral"
    informative: str = "informative"
    active: str = "active"
    pending: str = "pending"
    positive: str = "positive"
    caution: str = "caution"
    negative: str = "negative"
