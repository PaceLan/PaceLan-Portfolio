import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)
from application.verification import VerificationResult, VerificationStatus
from application.workflow_storage import WorkflowStorage


class WorkflowStorageB2Tests(unittest.TestCase):

    def _execution(self):
        return ApplicationExecutionModel(
            task=TaskModel(
                task_id="task-001",
                project_id="project-001",
                description="Implement persistence",
                context="B2",
            ),
            plan=PlanModel(
                task_id="task-001",
                project_id="project-001",
                steps=(
                    StepModel(
                        step_id="step-001",
                        operation="write",
                        risk="SAFE",
                        approval="NOT_REQUESTED",
                        target="application/workflow_storage.py",
                        context="B2",
                        readiness="READY",
                        reason="Ready",
                        ready=True,
                    ),
                ),
                ready=True,
                issues=("none",),
                warnings=("test warning",),
            ),
            run=RunModel(run_id="run-001", task_id="task-001"),
            result=ResultModel(
                run_id="run-001",
                status="completed",
                total_steps=1,
                successful_steps=1,
                completed_successfully=True,
            ),
            snapshot=SnapshotModel(
                run_id="run-001",
                task_id="task-001",
                run_status="completed",
                step_states={"step-001": "success"},
                current_step=None,
                started_at=datetime(
                    2026, 10, 3, 1, 2, 3, tzinfo=timezone.utc
                ),
                finished_at=datetime(
                    2026, 10, 3, 1, 3, 4, tzinfo=timezone.utc
                ),
            ),
            verification=VerificationResult(
                run_id="run-001",
                status=VerificationStatus.VERIFIED,
                verified=True,
                reason="Workflow completed successfully.",
                checked_steps=1,
                successful_steps=1,
                failed_steps=0,
                blocked_steps=0,
            ),
        )

    def test_task_plan_result_survive_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            original = self._execution()

            saved = WorkflowStorage().save(original, path)
            restored = WorkflowStorage().load(path)

            self.assertEqual(
                saved,
                (path / ".pacepilot" / "workflow.json").resolve(),
            )
            self.assertEqual(restored.task, original.task)
            self.assertEqual(restored.plan, original.plan)
            self.assertEqual(restored.run, original.run)
            self.assertEqual(restored.result, original.result)

    def test_snapshot_and_verification_survive_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            original = self._execution()

            WorkflowStorage().save(original, path)
            restored = WorkflowStorage().load(path)

            self.assertEqual(restored.snapshot, original.snapshot)
            self.assertEqual(restored.verification, original.verification)

    def test_missing_and_corrupt_storage_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            storage = WorkflowStorage()

            with self.assertRaises(FileNotFoundError):
                storage.load(path)

            target = (path / ".pacepilot" / "workflow.json").resolve()
            target.parent.mkdir(parents=True)
            target.write_text("{not-json", encoding="utf-8")

            with self.assertRaises(ValueError):
                storage.load(path)

    def test_unsupported_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            target = (path / ".pacepilot" / "workflow.json").resolve()
            target.parent.mkdir(parents=True)
            target.write_text(
                '{"schema_version": 999}',
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                WorkflowStorage().load(path)

    def test_type_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(TypeError):
                WorkflowStorage().save(object(), temp)


if __name__ == "__main__":
    unittest.main()
