from pathlib import Path
from typing import Optional

import tkinter as tk

from application.bootstrap import ApplicationBootstrap, ApplicationRuntime
from ui.app import CodingAssistantApp
from ui.daily_greeting import DailyGreetingService, greeting_history_path
from ui.opening_experience import OpeningConfig, OpeningExperience


class StartupCoordinator:
    """Coordinate startup initialization with the product opening experience."""

    def __init__(
        self,
        root,
        *,
        runtime_root,
        agent_service=None,
        greeting_resolver=None,
        opening_config=None,
    ):
        self.root = root
        self.runtime_root = Path(runtime_root)
        self.agent_service = agent_service
        self.greeting_resolver = greeting_resolver
        self.opening_config = opening_config

        self.runtime: Optional[ApplicationRuntime] = None
        self.app: Optional[CodingAssistantApp] = None
        self.opening = None

        self.ready = False
        self.initializing = False
        self.initialization_steps = ()
        self.completed_steps = ()

    def start(self, on_ready=None):
        if self.initializing or self.ready:
            return

        self.ready = False
        self.initializing = True
        self.initialization_steps = (
            "runtime",
            "visual",
            "greeting",
        )
        self.completed_steps = ()

        self.runtime = ApplicationBootstrap.create(
            self.runtime_root,
            agent_service=self.agent_service,
        )

        self.app = CodingAssistantApp(
            self.root,
            agent_service=self.runtime.agent_service,
            execution_service=self.runtime.execution_service,
            runtime_root=self.runtime_root,
        )


        self.app.visual_experience.start_ambient()

        visual_experience = self.app.visual_experience

        self.opening = OpeningExperience(
            self.root,
            ambient=visual_experience.ambient,
            theme_state=visual_experience.theme_state,
            config=self.opening_config,
        )

        self.opening.start()

        self.root.after_idle(
            lambda: self._initialize_greeting(on_ready)
        )



    def _initialize_greeting(self, on_ready=None):
        if self.app is None:
            return

        if self.greeting_resolver is not None:
            greeting = self.greeting_resolver(self.runtime_root)
        else:
            greeting = self.app.visual_experience.resolve_greeting()

        self.app.visual_experience.greeting = greeting
        self.opening.set_greeting(
            greeting
        )

        self.initialization_steps = (
            "runtime",
            "visual",
            "greeting",
        )
        self.completed_steps = (
            "runtime",
            "visual",
            "greeting",
        )

        self.root.after_idle(
            lambda: self._finish(on_ready)
        )

    def _finish(self, on_ready=None):
        self.initializing = False
        self.ready = True

        if self.opening is not None:
            self.opening.complete()

        if on_ready is not None and self.app is not None:
            on_ready(self.app)
