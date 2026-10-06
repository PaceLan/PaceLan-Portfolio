import unittest

from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.runtime_authority import RuntimeAuthority
from application.unified_control_validator import UnifiedControlValidator
from application.verification import VerificationResult, VerificationStatus


class UnifiedControlValidatorC3134Tests(unittest.TestCase):
    def _execution(self, status="COMPLETED"):
        task = TaskModel("task-1", "project-1", "test")
        return ApplicationExecutionModel(
            task=task,
            plan=PlanModel("task-1", "project-1"),
            run=RunModel("run-1", "task-1"),
            result=ResultModel(
                "run-1",
                status,
            ),
            snapshot=SnapshotModel(
                "run-1",
                "task-1",
                status,
            ),
            verification=VerificationResult(
                "run-1",
                VerificationStatus.VERIFIED
                if status == "COMPLETED"
                else VerificationStatus.NOT_VERIFIED,
                status == "COMPLETED",
                "",
                0,
                0,
                0,
                0,
            ),
        )

    def test_consistent_chain_passes(self):
        authority = RuntimeAuthority()
        UnifiedControlValidator.validate(
            self._execution(),
            authority,
        )

    def test_task_run_identity_is_required(self):
        execution = self._execution()
        execution = ApplicationExecutionModel(
            execution.task,
            execution.plan,
            RunModel("run-1", "other-task"),
            execution.result,
            execution.snapshot,
            execution.verification,
        )
        with self.assertRaises(ValueError):
            UnifiedControlValidator.validate(
                execution,
                RuntimeAuthority(),
            )

    def test_result_verification_identity_is_required(self):
        execution = self._execution()
        execution = ApplicationExecutionModel(
            execution.task,
            execution.plan,
            execution.run,
            execution.result,
            execution.snapshot,
            VerificationResult(
                "other-run",
                VerificationStatus.VERIFIED,
                True,
                "",
                0,
                0,
                0,
                0,
            ),
        )
        with self.assertRaises(ValueError):
            UnifiedControlValidator.validate(
                execution,
                RuntimeAuthority(),
            )

    def test_active_runtime_rejects_terminal_result(self):
        authority = RuntimeAuthority()
        authority.start()
        with self.assertRaises(ValueError):
            UnifiedControlValidator.validate(
                self._execution(),
                authority,
            )

    def test_failed_result_requires_failed_verification(self):
        execution = self._execution("FAILED")
        bad_verification = VerificationResult(
            "run-1",
            VerificationStatus.VERIFIED,
            True,
            "",
            0,
            0,
            0,
            0,
        )
        execution = ApplicationExecutionModel(
            execution.task,
            execution.plan,
            execution.run,
            execution.result,
            execution.snapshot,
            bad_verification,
        )
        with self.assertRaises(ValueError):
            UnifiedControlValidator.validate(
                execution,
                RuntimeAuthority(),
            )


if __name__ == "__main__":
    unittest.main()
