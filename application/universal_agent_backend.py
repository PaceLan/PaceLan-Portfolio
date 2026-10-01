"""Local ApplicationExecutionService adapter for the universal Agent API."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass

from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_plan import WorkflowStep
from application.models import ApplicationExecutionModel, PlanModel, TaskModel
from application.services import ApplicationExecutionService, TaskService
from permissions.reporting import ApprovalStatus, RiskLevel

from .universal_agent_interface import (
    AgentOperationRequest,
    AgentRuntimeState,
    AgentRuntimeView,
    AgentUnderstandingView,
    ApprovalAuthorizer,
    UniversalAgentInterface,
)


@dataclass(frozen=True)
class LocalOperation:
    """A host-registered local operation; never supplied over the Agent API."""

    risk: str
    execute: Callable[[TaskModel, AgentOperationRequest], str]


class AgentServiceUnderstandingProvider:
    """Project existing local Agent understanding into public DTOs."""

    def __init__(self, agent_service: AgentService) -> None:
        if not isinstance(agent_service, AgentService):
            raise TypeError("agent_service must be an AgentService")
        self.agent_service = agent_service

    def inspect(self, task: TaskModel) -> AgentUnderstandingView | None:
        project_agent = self.agent_service.project_context_agent
        if project_agent is None:
            return None
        result = project_agent.context_understanding.understand_task(
            TaskService.to_workflow(task)
        )
        return AgentUnderstandingView(
            task_id=task.task_id,
            summary=result.summary or "Understanding available",
            relevant_files=tuple(str(path) for path in result.relevant_files),
            relevant_symbols=tuple(
                str(symbol) for symbol in result.relevant_symbols
            ),
            relationships=tuple(
                str(relationship) for relationship in result.relationships
            ),
            dependencies=tuple(str(item) for item in result.dependencies),
        )


class ApplicationExecutionBackend:
    """Translate safe Agent requests into the existing workflow service."""

    def __init__(
        self,
        execution_service: ApplicationExecutionService,
        operations: Mapping[str, LocalOperation],
    ) -> None:
        if not isinstance(execution_service, ApplicationExecutionService):
            raise TypeError(
                "execution_service must be an ApplicationExecutionService"
            )
        self.execution_service = execution_service
        self.operations = dict(operations)
        for name, operation in self.operations.items():
            if not name or not callable(operation.execute):
                raise ValueError("local operations require names and handlers")
            RiskLevel(operation.risk)

    def risk_for(self, operation: str) -> str:
        try:
            return self.operations[operation].risk
        except KeyError as error:
            raise ValueError(f"operation is not available: {operation}") from error

    def start(
        self,
        task: TaskModel,
        operations: tuple[AgentOperationRequest, ...],
        plan: PlanModel,
        progress: Callable[[str, str], None],
    ) -> Future[ApplicationExecutionModel]:
        if len(operations) != len(plan.steps):
            raise ValueError("plan does not match submitted operations")

        workflow_steps = []
        for request, step in zip(operations, plan.steps):
            capability = self.operations.get(request.operation)
            if capability is None:
                raise ValueError(
                    f"operation is not available: {request.operation}"
                )
            if step.operation != request.operation:
                raise ValueError("plan operation order does not match request")
            if step.risk != capability.risk:
                raise PermissionError("plan risk does not match local policy")
            if not step.ready:
                raise PermissionError("plan contains a blocked operation")

            risk = RiskLevel(step.risk)
            approval = ApprovalStatus(step.approval)
            if (
                risk is RiskLevel.HIGH_RISK
                and approval is not ApprovalStatus.APPROVED
            ):
                raise PermissionError(
                    "high-risk operation has not been approved"
                )

            def action(
                operation=capability,
                operation_request=request,
                step_id=step.step_id,
            ) -> str:
                progress(step_id, "started")
                try:
                    result = operation.execute(task, operation_request)
                    if not isinstance(result, str):
                        raise TypeError("operation handlers must return strings")
                except Exception:
                    progress(step_id, "failed")
                    raise
                progress(step_id, "completed")
                return result

            workflow_steps.append(
                WorkflowStep(
                    operation=step.operation,
                    action=action,
                    risk=risk,
                    approval=approval,
                    target=step.target,
                    context=step.context,
                    step_id=step.step_id,
                )
            )

        return self.execution_service.start(task, tuple(workflow_steps))

    def pause(self) -> AgentRuntimeView:
        return self._runtime_view(self.execution_service.pause())

    def resume(self) -> AgentRuntimeView:
        return self._runtime_view(self.execution_service.resume())

    def stop(self) -> AgentRuntimeView:
        return self._runtime_view(self.execution_service.terminate())

    def inspect_runtime(self) -> AgentRuntimeView:
        return self._runtime_view(self.execution_service.runtime_status())

    @staticmethod
    def _runtime_view(result) -> AgentRuntimeView:
        raw_state = getattr(result.state, "value", result.state)
        state = (
            AgentRuntimeState.STOPPED
            if str(raw_state).upper() == "TERMINATED"
            else AgentRuntimeState(str(raw_state).upper())
        )
        return AgentRuntimeView(
            state=state,
            accepted=bool(result.accepted),
            message=str(getattr(result, "message", "")),
        )


def create_local_agent_interface(
    execution_service: ApplicationExecutionService,
    agent_service: AgentService,
    operations: Mapping[str, LocalOperation],
    *,
    approval_authorizer: ApprovalAuthorizer | None = None,
) -> UniversalAgentInterface:
    """Create the local transport-neutral Agent interface composition."""
    return UniversalAgentInterface(
        ApplicationExecutionBackend(execution_service, operations),
        approval_authorizer=approval_authorizer,
        understanding_provider=AgentServiceUnderstandingProvider(agent_service),
    )


__all__ = [
    "AgentServiceUnderstandingProvider",
    "ApplicationExecutionBackend",
    "LocalOperation",
    "create_local_agent_interface",
]
