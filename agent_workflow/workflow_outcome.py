from __future__ import annotations

from agent_workflow.workflow_core import WorkflowStatus
from agent_workflow.workflow_result import WorkflowResult


def is_terminal(result: WorkflowResult) -> bool:
    """Return whether the workflow has reached a terminal state."""
    if not isinstance(result, WorkflowResult):
        raise TypeError("result must be a WorkflowResult")
    return result.status in {
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.BLOCKED,
    }


def is_success(result: WorkflowResult) -> bool:
    """Return whether the workflow completed successfully."""
    if not isinstance(result, WorkflowResult):
        raise TypeError("result must be a WorkflowResult")
    return result.status is WorkflowStatus.COMPLETED


def is_failed(result: WorkflowResult) -> bool:
    """Return whether the workflow failed."""
    if not isinstance(result, WorkflowResult):
        raise TypeError("result must be a WorkflowResult")
    return result.status is WorkflowStatus.FAILED


def is_blocked(result: WorkflowResult) -> bool:
    """Return whether the workflow is blocked."""
    if not isinstance(result, WorkflowResult):
        raise TypeError("result must be a WorkflowResult")
    return result.status is WorkflowStatus.BLOCKED


def is_in_progress(result: WorkflowResult) -> bool:
    """Return whether the workflow is currently in progress."""
    if not isinstance(result, WorkflowResult):
        raise TypeError("result must be a WorkflowResult")
    return result.status is WorkflowStatus.IN_PROGRESS
