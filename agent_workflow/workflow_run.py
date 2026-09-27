from dataclasses import dataclass
from uuid import uuid4

from agent_workflow.workflow_core import WorkflowTask


@dataclass(frozen=True)
class WorkflowRunContext:
    run_id: str
    task_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id:
            raise ValueError("run_id must be a non-empty string")

        if not isinstance(self.task_id, str) or not self.task_id:
            raise ValueError("task_id must be a non-empty string")

    @classmethod
    def create(cls, task: WorkflowTask) -> "WorkflowRunContext":
        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        return cls(
            run_id=str(uuid4()),
            task_id=task.task_id,
        )