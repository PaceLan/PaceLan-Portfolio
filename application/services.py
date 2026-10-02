"""Application-layer services for product-facing orchestration."""

from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, RLock

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.agent_service import AgentService
from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.core_interfaces import (
    Execution,
    Project,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_readiness import ExecutionReadiness
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.risk_approval import RiskApprovalAwareness
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult

from .runtime_control import (
    ApplicationRuntimeControlService,
    RuntimeControlState,
)

from .models import (
    ApplicationExecutionModel,
    ExecutionModel,
    PlanModel,
    ProjectGoal,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)


class ProjectService:
    """Application boundary for project identity."""

    @staticmethod
    def from_core(project: Project) -> ProjectModel:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project")

        return ProjectModel(
            project_id=project.project_id,
        )

    @staticmethod
    def create(
        project_id: str,
        *,
        goal: str = "",
    ) -> ProjectModel:
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")

        return ProjectModel(
            project_id=project_id,
            goal=ProjectGoal(text=ProjectService._validate_goal(goal)),
        )

    @staticmethod
    def get_goal(project: ProjectModel) -> ProjectGoal:
        if not isinstance(project, ProjectModel):
            raise TypeError("project must be a ProjectModel")

        return project.goal

    @staticmethod
    def update_goal(
        project: ProjectModel,
        goal: str,
    ) -> ProjectModel:
        if not isinstance(project, ProjectModel):
            raise TypeError("project must be a ProjectModel")

        return ProjectModel(
            project_id=project.project_id,
            goal=ProjectGoal(
                text=ProjectService._validate_goal(goal),
            ),
        )

    @staticmethod
    def _validate_goal(goal: str) -> str:
        if not isinstance(goal, str):
            raise TypeError("goal must be a string")
        return goal.strip()


class TaskService:
    """Application boundary for task identity and task context."""

    @staticmethod
    def from_core(
        task: Task,
        *,
        description: str = "",
        context: str = "",
    ) -> TaskModel:
        if not isinstance(task, Task):
            raise TypeError("task must be a Task")

        return TaskModel(
            task_id=task.task_id,
            project_id=task.project_id,
            description=description,
            context=context,
        )

    @staticmethod
    def create(
        task_id: str,
        project_id: str,
        *,
        description: str = "",
        context: str = "",
    ) -> TaskModel:
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")

        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")

        return TaskModel(
            task_id=task_id,
            project_id=project_id,
            description=description,
            context=context,
        )

    @staticmethod
    def to_core(task: TaskModel) -> Task:
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        return Task(
            task_id=task.task_id,
            project_id=task.project_id,
        )

    @staticmethod
    def to_workflow(task: TaskModel) -> WorkflowTask:
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        return WorkflowTask(
            task_id=task.task_id,
            description=task.description,
            context=task.context,
            project_id=task.project_id,
        )


class PlanningService:
    """Application boundary for deterministic workflow planning."""

    def __init__(
        self,
        project_context_agent,
    ) -> None:
        if not isinstance(
            project_context_agent,
            ProjectContextAgentInterface,
        ):
            raise TypeError(
                "project_context_agent must be a "
                "ProjectContextAgentInterface"
            )

        self._planner = AgentProjectPlanner(
            project_context_agent,
        )

    def plan(
        self,
        task: TaskModel,
        steps: Iterable[WorkflowStep] = (),
    ) -> PlanModel:
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        workflow_task = TaskService.to_workflow(task)

        workflow_plan = self._planner.build(
            workflow_task,
            steps,
        )

        return self._to_model(workflow_plan)

    def plan_from_context(
        self,
        task: TaskModel,
        context: ContextUnderstandingResult,
        steps: Iterable[WorkflowStep] = (),
    ) -> PlanModel:
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        if not isinstance(
            context,
            ContextUnderstandingResult,
        ):
            raise TypeError(
                "context must be a ContextUnderstandingResult"
            )

        workflow_task = TaskService.to_workflow(task)

        workflow_plan = self._planner.build_from_context(
            workflow_task,
            context,
            steps,
        )

        return self._to_model(workflow_plan)

    @staticmethod
    def _to_model(plan: WorkflowPlan) -> PlanModel:
        if not isinstance(plan, WorkflowPlan):
            raise TypeError("plan must be a WorkflowPlan")

        assessments = RiskApprovalAwareness.assess_plan(plan.steps)
        readiness = ExecutionReadiness().check(plan)

        return PlanModel(
            task_id=plan.task.task_id,
            project_id=plan.task.project_id,
            steps=tuple(
                StepModel(
                    step_id=step.step_id,
                    operation=step.operation,
                    risk=(
                        step.risk.value
                        if hasattr(step.risk, "value")
                        else str(step.risk)
                    ),
                    approval=(
                        step.approval.value
                        if hasattr(step.approval, "value")
                        else str(step.approval)
                    ),
                    target=step.target,
                    context=step.context,
                    readiness=assessment.readiness.value,
                    reason=assessment.reason,
                    ready=assessment.is_ready,
                )
                for step, assessment in zip(plan.steps, assessments)
            ),
            ready=readiness.ready and all(
                assessment.is_ready for assessment in assessments
            ),
            issues=readiness.issues,
            warnings=readiness.warnings,
        )


class RunService:
    """Application boundary for execution-run identity."""

    @staticmethod
    def from_core(run: Run) -> RunModel:
        if not isinstance(run, Run):
            raise TypeError("run must be a Run")

        return RunModel(
            run_id=run.run_id,
            task_id=run.task_id,
        )


class ExecutionService:
    """Application boundary for execution state."""

    @staticmethod
    def from_core(execution: Execution) -> ExecutionModel:
        if not isinstance(execution, Execution):
            raise TypeError("execution must be an Execution")

        status = (
            execution.status.value
            if hasattr(execution.status, "value")
            else str(execution.status)
        )

        return ExecutionModel(
            run_id=execution.run_id,
            status=status,
        )


class ResultService:
    """Application boundary for execution-result observations."""

    @staticmethod
    def from_core(result: Result) -> ResultModel:
        if not isinstance(result, Result):
            raise TypeError("result must be a Result")

        status = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        )

        return ResultModel(
            run_id=result.run_id,
            status=status,
        )

    @staticmethod
    def from_workflow_result(
        result: WorkflowResult,
    ) -> ResultModel:
        if not isinstance(result, WorkflowResult):
            raise TypeError(
                "result must be a WorkflowResult"
            )

        status = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        )

        return ResultModel(
            run_id=result.run_id,
            status=status,
            total_steps=result.total_steps,
            successful_steps=result.successful_steps,
            failed_steps=result.failed_steps,
            blocked_steps=result.blocked_steps,
            completed_successfully=result.completed_successfully,
            failure_index=result.failure_index,
        )


class SnapshotService:
    """Application boundary for immutable execution snapshots."""

    @staticmethod
    def from_core(
        snapshot: ExecutionSnapshot,
    ) -> SnapshotModel:
        if not isinstance(snapshot, ExecutionSnapshot):
            raise TypeError(
                "snapshot must be an ExecutionSnapshot"
            )

        step_states = {
            step_id: (
                state.value
                if hasattr(state, "value")
                else str(state)
            )
            for step_id, state in snapshot.step_states.items()
        }

        run_status = (
            snapshot.run_status.value
            if hasattr(snapshot.run_status, "value")
            else str(snapshot.run_status)
        )

        return SnapshotModel(
            run_id=snapshot.run_id,
            task_id=snapshot.task_id,
            run_status=run_status,
            step_states=step_states,
            current_step=snapshot.current_step,
            started_at=snapshot.started_at,
            finished_at=snapshot.finished_at,
        )


class ApplicationExecutionService:
    """Application facade for complete agent execution."""

    def __init__(
        self,
        agent_service: AgentService,
    ) -> None:
        if not isinstance(agent_service, AgentService):
            raise TypeError(
                "agent_service must be an AgentService"
            )

        self._agent_service = agent_service
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="pacepilot-agent",
        )
        self._active_future: Future | None = None
        self._runtime_lock = RLock()
        self._resume_gate = Event()
        self._resume_gate.set()
        self._terminate_requested = Event()
        self._runtime_state = RuntimeControlState.IDLE
        self.runtime_control = ApplicationRuntimeControlService(
            self,
        )

    def start(
        self,
        task: TaskModel,
        steps: Iterable[WorkflowStep] = (),
    ) -> Future:
        """Start Agent execution without blocking the UI caller."""
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        if (
            self._active_future is not None
            and not self._active_future.done()
        ):
            raise RuntimeError("agent execution is already active")

        self._begin_runtime()
        try:
            self._active_future = self._executor.submit(
                self.run,
                task,
                steps,
            )
        except Exception:
            self._finish_runtime()
            raise
        return self._active_future

    def pause(self):
        return self.runtime_control.pause()

    def resume(self):
        return self.runtime_control.resume()

    def terminate(self):
        return self.runtime_control.terminate()

    def runtime_status(self):
        return self.runtime_control.status()

    def pause_runtime(self) -> None:
        with self._runtime_lock:
            if self._runtime_state is not RuntimeControlState.RUNNING:
                raise RuntimeError("agent execution is not running")
            self._runtime_state = RuntimeControlState.PAUSED
            self._resume_gate.clear()

    def resume_runtime(self) -> None:
        with self._runtime_lock:
            if self._runtime_state is not RuntimeControlState.PAUSED:
                raise RuntimeError("agent execution is not paused")
            self._runtime_state = RuntimeControlState.RUNNING
            self._resume_gate.set()

    def terminate_runtime(self) -> None:
        with self._runtime_lock:
            if self._runtime_state not in {
                RuntimeControlState.RUNNING,
                RuntimeControlState.PAUSED,
            }:
                raise RuntimeError("agent execution is not active")
            self._terminate_requested.set()
            self._runtime_state = RuntimeControlState.TERMINATED
            self._resume_gate.set()

    def runtime_state(self) -> str:
        with self._runtime_lock:
            return self._runtime_state.value

    def _begin_runtime(self) -> None:
        with self._runtime_lock:
            self._terminate_requested.clear()
            self._resume_gate.set()
            self._runtime_state = RuntimeControlState.RUNNING

    def _finish_runtime(self) -> None:
        with self._runtime_lock:
            self._runtime_state = (
                RuntimeControlState.TERMINATED
                if self._terminate_requested.is_set()
                else RuntimeControlState.IDLE
            )
            self._resume_gate.set()

    def _controlled_step(self, step: WorkflowStep) -> WorkflowStep:
        def action() -> str:
            self._resume_gate.wait()
            if self._terminate_requested.is_set():
                raise RuntimeError("agent execution was stopped")
            return step.action()

        return WorkflowStep(
            operation=step.operation,
            action=action,
            risk=step.risk,
            approval=step.approval,
            target=step.target,
            context=step.context,
            step_id=step.step_id,
        )

    def run(
        self,
        task: TaskModel,
        steps: Iterable[WorkflowStep] = (),
    ) -> ApplicationExecutionModel:
        if not isinstance(task, TaskModel):
            raise TypeError("task must be a TaskModel")

        with self._runtime_lock:
            runtime_started = self._runtime_state in {
                RuntimeControlState.RUNNING,
                RuntimeControlState.PAUSED,
            }
        if not runtime_started:
            self._begin_runtime()

        workflow_task = TaskService.to_workflow(task)
        controlled_steps = tuple(
            self._controlled_step(step)
            for step in steps
        )

        try:
            execution = self._agent_service.run(
                workflow_task,
                controlled_steps,
            )
        finally:
            self._finish_runtime()

        application_task = TaskModel(
            task_id=execution.task.task_id,
            project_id=execution.task.project_id,
            description=execution.task.description,
            context=execution.task.context,
        )

        application_plan = PlanningService._to_model(
            execution.plan,
        )

        application_run = RunModel(
            run_id=execution.run_context.run_id,
            task_id=execution.run_context.task_id,
        )

        application_result = ResultService.from_workflow_result(
            execution.result,
        )

        application_snapshot = SnapshotService.from_core(
            execution.snapshot,
        )

        return ApplicationExecutionModel(
            task=application_task,
            plan=application_plan,
            run=application_run,
            result=application_result,
            snapshot=application_snapshot,
        )