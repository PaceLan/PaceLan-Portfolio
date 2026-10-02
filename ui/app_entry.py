import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Union

from application.bootstrap import ApplicationBootstrap, ApplicationRuntime
from ui.app import CodingAssistantApp, create_app as _create_app
from ui.startup import StartupCoordinator
from ui.daily_greeting import DailyGreetingService, greeting_history_path
from ui.opening_experience import OpeningConfig



def resolve_daily_greeting(runtime_root):
    greeting_service = DailyGreetingService(
        greeting_history_path(runtime_root)
    )
    daily_greeting = greeting_service.today_text()
    # M26.5 opening contract: config=OpeningConfig(greeting=daily_greeting)
    config = OpeningConfig(greeting=daily_greeting)
    return config.greeting

def create_runtime(
    project_root: Union[str, Path],
    *,
    agent_service=None,
) -> ApplicationRuntime:
    return ApplicationBootstrap.create(
        project_root,
        agent_service=agent_service,
    )


def create_app(
    root: tk.Tk,
    project_root: Optional[Union[str, Path]] = None,
    controller=None,
    agent_service=None,
) -> CodingAssistantApp:
    runtime = None

    if project_root is not None and controller is None:
        runtime = create_runtime(
            project_root,
            agent_service=agent_service,
        )

    resolved_agent_service = (
        runtime.agent_service
        if runtime is not None
        else agent_service
    )

    return _create_app(
        root,
        project_root=project_root,
        controller=controller,
        agent_service=resolved_agent_service,
    )


def main() -> None:
    root = None
    try:
        root = tk.Tk()
        root.report_callback_exception = lambda error_type, error, trace: (
            messagebox.showerror(
                "PacePilot error",
                str(error),
                parent=root,
            )
        )

        runtime_root = Path(
            os.environ.get(
                "LOCALAPPDATA",
                str(Path.home() / "AppData" / "Local"),
            )
        ) / "PacePilot" / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)

        coordinator = StartupCoordinator(
            root,
            runtime_root=runtime_root,
            greeting_resolver=resolve_daily_greeting,
        )
        coordinator.start()

        root.mainloop()

    except Exception as error:
        if root is None:
            raise SystemExit(f"PacePilot could not start: {error}") from error
        try:
            messagebox.showerror(
                "PacePilot could not start",
                str(error),
                parent=root,
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    main()
