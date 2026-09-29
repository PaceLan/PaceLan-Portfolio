"""Immutable visual interaction state definitions for the UI layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualInteractionState:
    """Stable visual state used to describe UI interaction semantics."""

    idle: str = "idle"
    ready: str = "ready"
    running: str = "running"
    waiting: str = "waiting"
    success: str = "success"
    warning: str = "warning"
    error: str = "error"