"""Unified animation integration for the M22 presentation layer."""

from __future__ import annotations

from dataclasses import dataclass

from ui.animation import (
    AnimationController,
    AnimationKind,
    AnimationRequest,
    AnimationSpec,
)


@dataclass(frozen=True)
class AnimationIntegrationState:
    """Immutable snapshot of the unified animation integration."""

    active: AnimationRequest | None = None
    channel: str | None = None

    @property
    def running(self) -> bool:
        return self.active is not None


class AnimationIntegration:
    """Coordinate animation requests across M22 UI effect channels."""

    def __init__(self, controller: AnimationController | None = None) -> None:
        self.controller = controller or AnimationController()
        self._channel: str | None = None

    @property
    def state(self) -> AnimationIntegrationState:
        return AnimationIntegrationState(
            active=self.controller.active,
            channel=self._channel,
        )

    def start(
        self,
        *,
        channel: str,
        source: str,
        target: str,
        kind: AnimationKind = AnimationKind.FADE,
        duration_ms: int = 180,
        steps: int = 12,
    ) -> AnimationIntegrationState:
        """Start one animation on a named presentation channel."""
        if not channel:
            raise ValueError("channel must not be empty")

        request = AnimationRequest(
            source=source,
            target=target,
            spec=AnimationSpec(
                kind=kind,
                duration_ms=duration_ms,
                steps=steps,
            ),
        )

        self.controller.start(request)
        self._channel = channel
        return self.state

    def stop(self) -> AnimationIntegrationState:
        """Stop the active animation."""
        self.controller.stop()
        self._channel = None
        return self.state

    def reset(self) -> AnimationIntegrationState:
        """Reset the integration to its initial state."""
        self.controller.reset()
        self._channel = None
        return self.state


__all__ = [
    "AnimationIntegration",
    "AnimationIntegrationState",
]
