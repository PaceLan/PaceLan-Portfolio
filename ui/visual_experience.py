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
)
from ui.theme import ThemeState


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

    def start_ambient(self):
        self.ambient_runtime.start()
        return self.ambient

    def stop_ambient(self):
        self.ambient_runtime.stop()

    def start_transition(
        self,
        kind: UnifiedTransitionKind,
        target: str,
    ):
        self.transition_controller.start(kind, target)
        self.transition_controller.enter()
        return self.transition_controller.current_kind

    def complete_transition(self):
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
