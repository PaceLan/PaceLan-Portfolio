"""Application bootstrap for the PacePilot product shell."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_service import WorkflowService
from application.services import ApplicationExecutionService
from application.workspace import ProjectWorkspaceService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class BootstrapState(str, Enum):
    LAUNCH = "launch"
    INITIALIZE = "initialize"
    CONFIGURATION = "configuration"
    WORKSPACE = "workspace"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True)
class BootstrapError:
    state: BootstrapState
    message: str


@dataclass(frozen=True)
class ApplicationRuntime:
    agent_service: AgentService
    execution_service: ApplicationExecutionService
    workspace_service: ProjectWorkspaceService
    state: BootstrapState
    lifecycle: tuple[BootstrapState, ...]
    error: Optional[BootstrapError] = None


class ApplicationBootstrap:

    @staticmethod
    def bootstrap(
        project_root: Union[str, Path],
        *,
        agent_service: Optional[AgentService] = None,
    ) -> ApplicationRuntime:
        return ApplicationBootstrap.create(
            project_root,
            agent_service=agent_service,
        )

    @staticmethod
    def create(
        project_root: Union[str, Path],
        *,
        agent_service: Optional[AgentService] = None,
    ) -> ApplicationRuntime:
        lifecycle = (
            BootstrapState.LAUNCH,
            BootstrapState.INITIALIZE,
            BootstrapState.CONFIGURATION,
            BootstrapState.WORKSPACE,
        )

        root = Path(project_root).resolve()

        if not root.exists():
            raise ValueError("project_root must exist")
        if not root.is_dir():
            raise ValueError("project_root must be a directory")

        if agent_service is None:
            history_store = HistoryStore(root / "history.json")
            snapshot_store = SnapshotStore(
                root,
                root / "snapshots",
            )
            snapshot_service = SnapshotService(
                root,
                store=snapshot_store,
            )
            workflow = AgentWorkflow(
                history_store=history_store,
                snapshot_service=snapshot_service,
            )
            workflow_service = WorkflowService(workflow)
            agent_service = AgentService(workflow_service)

        if not isinstance(agent_service, AgentService):
            raise TypeError("agent_service must be an AgentService")

        return ApplicationRuntime(
            agent_service=agent_service,
            execution_service=ApplicationExecutionService(agent_service),
            workspace_service=ProjectWorkspaceService(),
            state=BootstrapState.READY,
            lifecycle=lifecycle + (BootstrapState.READY,),
        )
