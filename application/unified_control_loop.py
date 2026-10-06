from __future__ import annotations

from concurrent.futures import Future
from typing import Iterable

from application.models import ApplicationExecutionModel, TaskModel
from application.runtime_authority import RuntimeAuthority
from application.services import ApplicationExecutionService
from agent_workflow.workflow_plan import WorkflowStep


class UnifiedControlLoop:
    """Single application-facing control loop for task execution."""

    def __init__(
        self,
        execution_service: ApplicationExecutionService,
        runtime_authority: RuntimeAuthority,
    ) -> None:
        if not isinstance(
            execution_service,
            ApplicationExecutionService,
        ):
            raise TypeError(
                "execution_service must be an ApplicationExecutionService"
            )

        if not isinstance(runtime_authority, RuntimeAuthority):
            raise TypeError(
                "runtime_authority must be a RuntimeAuthority"
            )

        if execution_service.runtime_authority is not runtime_authority:
            raise ValueError(
                "execution_service and runtime_authority must share "
                "the same RuntimeAuthority"
            )

        self._execution_service = execution_service
        self._runtime_authority = runtime_authority

    @property
    def execution_service(self) -> ApplicationExecutionService:
        return self._execution_service

    @property
    def runtime_authority(self) -> RuntimeAuthority:
        return self._runtime_authority

    def start(
        self,
        task: TaskModel,
        steps: Iterable[WorkflowStep] = (),
    ) -> Future:
        return self._execution_service.start(task, steps)

    def pause(self):
        return self._execution_service.pause()

    def resume(self):
        return self._execution_service.resume()

    def stop(self):
        return self._execution_service.terminate()

    def inspect(self):
        return self._execution_service.runtime_status()

    def wait(self, future: Future) -> ApplicationExecutionModel:
        if not isinstance(future, Future):
            raise TypeError("future must be a Future")
        return future.result()


__all__ = ["UnifiedControlLoop"]
