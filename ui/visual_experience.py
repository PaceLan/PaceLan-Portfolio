from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ui.ambient_effects import AmbientFieldController
from ui.ambient_runtime import AmbientRuntime
from ui.daily_greeting import DailyGreetingService, greeting_history_path
from ui.unified_transition import (
    UnifiedTransitionController,
    UnifiedTransitionKind,
    UnifiedTransition,
)
from ui.theme import ThemeState
from ui.transition_runtime import TransitionRuntime


@dataclass
class VisualExperienceSnapshot:
    theme: ThemeState
    ambient: object
    greeting: Optional[str]
    transition_kind: Optional[UnifiedTransitionKind]


class VisualExperienceController:
    """Coordinate PacePilot's global visual experience."""

    def __init__(
        self,
        root,
        *,
        runtime_root: Optional[Path] = None,
        greeting: Optional[str] = None,
        theme_state: Optional[ThemeState] = None,
        ambient: Optional[AmbientFieldController] = None,
        visual_renderer=None,
        composition=None,
    ) -> None:
        self.root = root
        self.visual_renderer = visual_renderer
        self.theme_state = theme_state or ThemeState()
        self.ambient = ambient or AmbientFieldController()

        self.ambient_runtime = AmbientRuntime(
            root,
            ambient=self.ambient,
            theme_state=self.theme_state,
            visual_renderer=visual_renderer,
            composition=composition,
        )
        self.transition_controller = UnifiedTransitionController()
        self.transition_runtime = TransitionRuntime(
            root,
            on_frame=self._render_transition_frame,
            on_complete=self._finish_transition_runtime,
        )
        self._theme_surfaces = []

        self.greeting_service = None
        self.greeting = greeting

        if runtime_root is not None:
            self.greeting_service = DailyGreetingService(
                history_path=greeting_history_path(
                    base_directory=runtime_root
                )
            )

    def register_theme_surface(self, surface) -> None:
        if surface not in self._theme_surfaces:
            self._theme_surfaces.append(surface)

    def toggle_theme(self) -> ThemeState:
        self.transition_controller.start(
            UnifiedTransitionKind.THEME,
            "theme",
        )
        self.transition_controller.enter()

        self.theme_state = self.theme_state.toggled()
        self.ambient_runtime.theme_state = self.theme_state

        if self.visual_renderer is not None:
            self.visual_renderer.apply_theme(self.theme_state)

        for surface in self._theme_surfaces:
            surface.apply_theme(self.theme_state.palette)

        self.transition_controller.complete()
        return self.theme_state

    def register_ambient_surface(self, widget) -> None:
        self.ambient_runtime.register_surface(widget)

    def start_ambient(self):
        self.ambient_runtime.start()
        return self.ambient

    def stop_ambient(self):
        self.ambient_runtime.stop()

    def _render_transition_frame(self, primitive, progress: float) -> None:
        if self.visual_renderer is None:
            return

        intensity = 0.08 * (1.0 - progress)
        if primitive.value == "ambient_shift":
            intensity = 0.18 * (1.0 - progress)
        elif primitive.value == "focus_depth":
            intensity = 0.12 * (1.0 - progress)

        self.visual_renderer.apply_ambient_field(intensity)

    def _finish_transition_runtime(self) -> None:
        self.transition_controller.complete()

    def _start_transition_runtime(self) -> None:
        transition = self.transition_controller.panel_transition
        self.transition_runtime.start(transition.primitive)

    def start_transition(
        self,
        kind: UnifiedTransitionKind,
        target: str,
    ):
        self.transition_controller.cross_fade(kind, target)
        self.transition_controller.enter()
        self._start_transition_runtime()
        return self.transition_controller.current_kind

    def cross_fade(
        self,
        kind: UnifiedTransitionKind,
        target: str,
    ) -> UnifiedTransition:
        transition = self.transition_controller.cross_fade(kind, target)
        self.transition_controller.enter()
        self._start_transition_runtime()
        return transition

    def ambient_shift(
        self,
        kind: UnifiedTransitionKind,
        target: str,
    ) -> UnifiedTransition:
        transition = self.transition_controller.ambient_shift(kind, target)
        self.transition_controller.enter()
        self._start_transition_runtime()
        return transition

    def focus_depth(
        self,
        kind: UnifiedTransitionKind,
        target: str,
    ) -> UnifiedTransition:
        transition = self.transition_controller.focus_depth(kind, target)
        self.transition_controller.enter()
        self._start_transition_runtime()
        return transition

    def complete_transition(self):
        if self.transition_runtime.running:
            return self.transition_controller.panel_transition
        return self.transition_controller.complete()

    def resolve_greeting(self) -> Optional[str]:
        if self.greeting is not None:
            return self.greeting

        if self.greeting_service is None:
            return None

        self.greeting = self.greeting_service.today_text()
        return self.greeting

    def snapshot(self) -> VisualExperienceSnapshot:
        return VisualExperienceSnapshot(
            theme=self.theme_state,
            ambient=self.ambient.snapshot(0.0),
            greeting=self.greeting,
            transition_kind=self.transition_controller.current_kind,
        )


__all__ = [
    "VisualExperienceSnapshot",
    "VisualExperienceController",
]
