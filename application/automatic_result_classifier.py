from dataclasses import dataclass
from enum import Enum

from agent_workflow.workflow_result import WorkflowResult
from permissions.reporting import ApprovalStatus


class ResultClassification(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class ResultClassificationEvidence:
    approval_statuses: tuple[ApprovalStatus, ...] = ()


class AutomaticResultClassifier:
    """Classify a real workflow result without changing its source status."""

    @staticmethod
    def classify(
        result: WorkflowResult,
        evidence: ResultClassificationEvidence | None = None,
    ) -> ResultClassification:
        if not isinstance(result, WorkflowResult):
            raise TypeError("result must be a WorkflowResult")

        approvals = (
            evidence.approval_statuses
            if evidence is not None
            else ()
        )

        if ApprovalStatus.DENIED in approvals:
            return ResultClassification.DENIED

        status = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        ).upper()

        if status == "COMPLETED":
            return ResultClassification.SUCCESS
        if status == "FAILED":
            return ResultClassification.FAILED
        if status == "BLOCKED":
            return ResultClassification.BLOCKED

        raise ValueError(f"unsupported workflow result status: {status}")
