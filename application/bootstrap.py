"""Application bootstrap for the PacePilot product shell."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from agent_workflow.agent_service import AgentService
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_service import WorkflowService
from application.runtime_authority import RuntimeAuthority
from application.unified_control_loop import UnifiedControlLoop
from application.services import ApplicationExecutionService, PlanningService
from application.autonomous_development import AutonomousDevelopmentService
from application.autonomous_execution import AutonomousExecutionService
from application.autonomous_planning import AutonomousPlanningService
from application.autonomous_task_creation import AutonomousTaskCreationService
from application.autonomous_plan_binding import AutonomousPlanBindingService
from application.goal_authority import GoalAuthority
from application.task_management import TaskManagementService
from application.workspace import ProjectWorkspaceService
from application.vscode_control_channel import VSCodeControlChannel
from application.vscode_terminal_executor import VSCodeTerminalCommandExecutor
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
    autonomous_execution_service: AutonomousExecutionService
    autonomous_development_service: AutonomousDevelopmentService
    goal_authority: GoalAuthority
    task_management: TaskManagementService
    autonomous_task_creation: AutonomousTaskCreationService
    autonomous_planning: AutonomousPlanningService
    runtime_authority: RuntimeAuthority
    control_loop: UnifiedControlLoop
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

        scan_result = ProjectScanner(root).scan()
        project_context = ProjectContextBuilder().build(scan_result)
        project_context_agent = ProjectContextAgentInterface(project_context)
        goal_authority = GoalAuthority()
        task_management = TaskManagementService()
        planning_service = PlanningService(project_context_agent)

        runtime_authority = RuntimeAuthority()
        execution_service = ApplicationExecutionService(
            agent_service,
            project_path=root,
            runtime_authority=runtime_authority,
            terminal_command_executor=VSCodeTerminalCommandExecutor(
                VSCodeControlChannel("http://127.0.0.1:8766/terminal"),
                str(root),
            ).execute,
        )
        control_loop = UnifiedControlLoop(
            execution_service,
            runtime_authority,
        )
        autonomous_plan_binding = AutonomousPlanBindingService()
        autonomous_task_creation = AutonomousTaskCreationService(
            goal_authority,
            task_management,
        )
        autonomous_planning = AutonomousPlanningService(
            goal_authority,
            planning_service,
            task_management,
            plan_binding=autonomous_plan_binding,
        )
        autonomous_execution_service = AutonomousExecutionService(
            execution_service,
            autonomous_plan_binding,
        )

        autonomous_development_service = AutonomousDevelopmentService(
            autonomous_task_creation,
            autonomous_planning,
            autonomous_execution_service,
        )

        return ApplicationRuntime(
            agent_service=agent_service,
            execution_service=execution_service,
            autonomous_execution_service=autonomous_execution_service,
            autonomous_development_service=autonomous_development_service,
            goal_authority=goal_authority,
            task_management=task_management,
            autonomous_task_creation=autonomous_task_creation,
            autonomous_planning=autonomous_planning,
            runtime_authority=runtime_authority,
            control_loop=control_loop,
            workspace_service=ProjectWorkspaceService(),
            state=BootstrapState.READY,
            lifecycle=lifecycle + (BootstrapState.READY,),
        )
