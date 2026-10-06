from dataclasses import dataclass

@dataclass(frozen=True)
class TaskContext:
    project_id: str
    task_id: str
    workflow_id: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if self.workflow_id is not None and not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")
