"""Application-level coordination for the Coding Assistant UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from application.models import TaskModel
from application.multi_project_workspace import MultiProjectWorkspaceService
from application.services import ApplicationExecutionService
from application.workspace import (
    ApplicationTreeNode,
    ProjectTreeProvider,
    FileReaderProvider,
    ProjectWorkspaceService,
)
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)
from ui.agent_adapter import AgentUIAdapter
from ui.agent_state import AgentInteractionState


@dataclass(frozen=True)
class ProjectContext:
    """Read-only project state prepared for presentation by the UI."""

    name: Optional[str]
    path: Optional[Path]
    exists: bool
    is_directory: bool


@dataclass(frozen=True)
class FileLoadResult:
    """Safe result returned when the controller loads a project file."""

    path: str
    success: bool
    contents: str = ""
    error: Optional[str] = None


class ApplicationController:
    """UI adapter over the Application workspace boundary."""

    def __init__(
        self,
        project_manager=None,
        tree_provider: Optional[ProjectTreeProvider] = None,
        file_reader: Optional[FileReaderProvider] = None,
        workspace: Optional[ProjectWorkspaceService] = None,
        agent_service=None,
        execution_service=None,
    ) -> None:
        base_workspace = workspace or ProjectWorkspaceService(
            project_manager=project_manager,
            tree_provider=tree_provider,
            file_reader=file_reader,
        )
        self.multi_project_workspace = MultiProjectWorkspaceService(
            workspace=base_workspace,
        )
        self.workspace = self.multi_project_workspace.workspace
        self._project_context = ProjectContext(None, None, False, False)
        self.agent_service = agent_service
        self.application_execution_service = (
            execution_service
            if execution_service is not None
            else (
                ApplicationExecutionService(agent_service)
                if agent_service is not None
                else None
            )
        )
        self.agent_state = AgentInteractionState()
        self._agent_history = ()

    @property
    def project_context(self) -> ProjectContext:
        return self._project_context

    @property
    def agent_history(self):
        return self.agent_state.history

    @property
    def active_project(self):
        return self.multi_project_workspace.active_project

    def list_projects(self):
        return self.multi_project_workspace.registry.list_projects()

    def switch_project(self, project_id: str) -> ProjectContext:
        info = self.multi_project_workspace.switch_project(project_id)
        self._project_context = ProjectContext(
            name=info["project_name"],
            path=info["project_path"],
            exists=bool(info["exists"]),
            is_directory=bool(info["is_directory"]),
        )
        return self._project_context

    def open_project(self, path: Union[str, Path]) -> ProjectContext:
        project_path = Path(path).resolve()
        project_id = project_path.name or str(project_path)

        existing = {
            project.project_id: project
            for project in self.multi_project_workspace.registry.list_projects()
        }

        if project_id in existing and existing[project_id].path != project_path:
            project_id = str(project_path)

        if project_id not in existing:
            self.multi_project_workspace.register_project(
                project_id,
                project_path,
            )

        info = self.multi_project_workspace.open_project(project_id)

        self._project_context = ProjectContext(
            name=info["project_name"],
            path=info["project_path"],
            exists=bool(info["exists"]),
            is_directory=bool(info["is_directory"]),
        )

        return self._project_context

    def get_project_tree(self) -> ApplicationTreeNode:
        return self.workspace.build_tree_model()

    def get_project_goal(self):
        return self.workspace.project_goal

    def update_project_goal(self, goal: str):
        return self.workspace.update_project_goal(goal)

    def close_project(self) -> None:
        self.workspace.close_project()
        self._project_context = ProjectContext(None, None, False, False)

    def persist_project(self):
        return self.workspace.persist_project()

    def reopen_project(self) -> ProjectContext:
        info = self.workspace.reopen_project()
        self._project_context = ProjectContext(
            name=info["project_name"],
            path=info["project_path"],
            exists=bool(info["exists"]),
            is_directory=bool(info["is_directory"]),
        )
        return self._project_context

    def select_file(
        self,
        relative_path: Union[str, Path],
    ) -> FileLoadResult:
        display_path = Path(relative_path).as_posix()

        try:
            contents = self.workspace.read_file(relative_path)
        except (
            FileNotFoundError,
            IsADirectoryError,
            UnicodeDecodeError,
            ValueError,
        ) as error:
            return FileLoadResult(
                display_path,
                False,
                error=str(error),
            )

        return FileLoadResult(
            display_path,
            True,
            contents=contents,
        )

    def run_agent_task(
        self,
        task,
        steps=(),
    ) -> AgentInteractionState:
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )

        application_task = TaskModel(
            task_id=task.task_id,
            project_id=task.project_id,
            description=task.description,
            context=task.context,
        )

        execution = self.application_execution_service.run(
            application_task,
            steps,
        )

        entry = AgentUIAdapter.history_entry(execution)

        self._agent_history = (
            *self._agent_history,
            entry,
        )

        self.agent_state = AgentUIAdapter.from_execution(execution)

        self.agent_state = self._with_history(
            self.agent_state,
            selected_run_id=entry.run_id,
        )

        return self.agent_state

    def start_agent_task(
        self,
        task,
        steps=(),
    ):
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )

        application_task = TaskModel(
            task_id=task.task_id,
            project_id=task.project_id,
            description=task.description,
            context=task.context,
        )

        return self.application_execution_service.start(
            application_task,
            steps,
        )

    def pause_agent(self):
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )
        return self.application_execution_service.pause()

    def resume_agent(self):
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )
        return self.application_execution_service.resume()

    def terminate_agent(self):
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )
        return self.application_execution_service.terminate()

    def agent_runtime_status(self):
        if self.application_execution_service is None:
            raise RuntimeError(
                "ApplicationExecutionService is not configured"
            )
        return self.application_execution_service.runtime_status()


    def select_agent_history(
        self,
        run_id: str,
    ) -> AgentInteractionState:
        history = self.agent_state.history

        entry = next(
            (
                item
                for item in history.entries
                if item.run_id == run_id
            ),
            None,
        )

        if entry is None:
            raise ValueError(
                f"Unknown Agent history run: {run_id}"
            )

        historical_state = AgentUIAdapter.from_history_entry(entry)

        self.agent_state = self._with_history(
            historical_state,
            selected_run_id=run_id,
        )

        return self.agent_state

    def _with_history(
        self,
        state: AgentInteractionState,
        selected_run_id: str | None,
    ) -> AgentInteractionState:
        history = AgentUIAdapter.history_state(
            self._agent_history,
            selected_run_id=selected_run_id,
        )

        return AgentInteractionState(
            task=state.task,
            plan=state.plan,
            understanding=state.understanding,
            risk_approval=state.risk_approval,
            execution=state.execution,
            result=state.result,
            history=history,
        )

    def initial_state(self) -> WorkspaceState:
        return WorkspaceState(
            project=self._project_context,
            tree=TreeState(),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Ready",
        )


__all__ = [
    "ProjectContext",
    "FileLoadResult",
    "ApplicationController",
]
