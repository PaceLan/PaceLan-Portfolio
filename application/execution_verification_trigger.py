from agent_workflow.workflow_result import WorkflowResult
from application.execution_verification import ExecutionVerificationValidator
from application.models import ResultModel, RunModel
from application.verification import VerificationResult, VerificationService


class ExecutionVerificationTrigger:
    """Triggers verification exactly once for a real workflow result."""

    @staticmethod
    def verify(
        workflow_result: WorkflowResult,
        run: RunModel,
        result: ResultModel,
    ) -> VerificationResult:
        if not isinstance(workflow_result, WorkflowResult):
            raise TypeError("workflow_result must be a WorkflowResult")

        verification = VerificationService.verify(workflow_result)
        ExecutionVerificationValidator.validate(
            run,
            result,
            verification,
        )
        return verification
