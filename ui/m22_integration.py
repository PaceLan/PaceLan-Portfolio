"""M22 final animation integration gate."""

from __future__ import annotations

from dataclasses import dataclass

from ui.animation import AnimationController, AnimationRequest
from ui.animation_accessibility import (
    AnimationAccessibility,
    AnimationPerformanceGuard,
    MotionMode,
    PerformanceSnapshot,
)
from ui.animation_integration import AnimationIntegration


@dataclass(frozen=True)
class M22IntegrationState:
    """Final presentation-layer animation integration snapshot."""

    animation: AnimationRequest | None
    channel: str | None
    reduced_motion: bool
    ambient_suppressed: bool

    @property
    def running(self) -> bool:
        return self.animation is not None


class M22IntegrationGate:
    """Coordinate M22 animation infrastructure without owning UI state."""

    def __init__(
        self,
        *,
        controller: AnimationController | None = None,
        accessibility: AnimationAccessibility | None = None,
        performance_guard: AnimationPerformanceGuard | None = None,
    ) -> None:
        self.integration = AnimationIntegration(controller)
        self.accessibility = accessibility or AnimationAccessibility()
        self.performance_guard = (
            performance_guard or AnimationPerformanceGuard()
        )

    @property
    def state(self) -> M22IntegrationState:
        integration_state = self.integration.state
        return M22IntegrationState(
            animation=integration_state.active,
            channel=integration_state.channel,
            reduced_motion=self.accessibility.reduced_motion,
            ambient_suppressed=False,
        )

    def start(
        self,
        *,
        channel: str,
        source: str,
        target: str,
        request: AnimationRequest,
    ) -> M22IntegrationState:
        adapted = self.accessibility.adapt_request(request)

        self.integration.controller.start(adapted)
        self.integration._channel = channel

        return self.state

    def evaluate_performance(
        self,
        snapshot: PerformanceSnapshot,
    ) -> M22IntegrationState:
        normalized = self.performance_guard.normalize(snapshot)
        suppressed = self.performance_guard.should_suppress_ambient(
            normalized
        )

        current = self.state
        return M22IntegrationState(
            animation=current.animation,
            channel=current.channel,
            reduced_motion=current.reduced_motion,
            ambient_suppressed=suppressed,
        )

    def stop(self) -> M22IntegrationState:
        self.integration.stop()
        return self.state

    def reset(self) -> M22IntegrationState:
        self.integration.reset()
        return self.state


__all__ = [
    "M22IntegrationGate",
    "M22IntegrationState",
]
