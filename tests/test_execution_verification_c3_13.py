from __future__ import annotations

import unittest

from application.execution_verification import ExecutionVerificationValidator
from application.models import ResultModel, RunModel
from application.verification import VerificationResult, VerificationStatus


class ExecutionVerificationC313Tests(unittest.TestCase):
    def make_values(self):
        run = RunModel(run_id="run-1", task_id="task-1")
        result = ResultModel(
            run_id="run-1",
            status="COMPLETED",
            total_steps=2,
            successful_steps=2,
            failed_steps=0,
            blocked_steps=0,
            completed_successfully=True,
        )
        verification = VerificationResult(
            run_id="run-1",
            status=VerificationStatus.VERIFIED,
            verified=True,
            reason="execution completed successfully",
            checked_steps=2,
            successful_steps=2,
            failed_steps=0,
            blocked_steps=0,
        )
        return run, result, verification

    def test_consistent_execution_passes(self):
        run, result, verification = self.make_values()
        ExecutionVerificationValidator.validate(run, result, verification)

    def test_run_id_mismatch_is_rejected(self):
        run, result, verification = self.make_values()
        result = ResultModel(
            run_id="run-2",
            status=result.status,
            total_steps=result.total_steps,
            successful_steps=result.successful_steps,
            failed_steps=result.failed_steps,
            blocked_steps=result.blocked_steps,
            completed_successfully=result.completed_successfully,
        )
        with self.assertRaises(ValueError):
            ExecutionVerificationValidator.validate(run, result, verification)

    def test_step_count_mismatch_is_rejected(self):
        run, result, verification = self.make_values()
        verification = VerificationResult(
            run_id=verification.run_id,
            status=verification.status,
            verified=verification.verified,
            reason=verification.reason,
            checked_steps=1,
            successful_steps=2,
            failed_steps=0,
            blocked_steps=0,
        )
        with self.assertRaises(ValueError):
            ExecutionVerificationValidator.validate(run, result, verification)

    def test_status_mismatch_is_rejected(self):
        run, result, verification = self.make_values()
        verification = VerificationResult(
            run_id=verification.run_id,
            status=VerificationStatus.NOT_VERIFIED,
            verified=False,
            reason="failed",
            checked_steps=2,
            successful_steps=2,
            failed_steps=0,
            blocked_steps=0,
        )
        with self.assertRaises(ValueError):
            ExecutionVerificationValidator.validate(run, result, verification)

    def test_invalid_types_are_rejected(self):
        run, result, verification = self.make_values()
        with self.assertRaises(TypeError):
            ExecutionVerificationValidator.validate(None, result, verification)
