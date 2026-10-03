from __future__ import annotations

import tempfile
import unittest
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
from application.workflow_persistence import WorkflowPersistenceService


class WorkflowPersistenceB2Tests(unittest.TestCase):
    def _execution(self) -> ApplicationExecutionModel:
        step = StepModel(
            step_id="step-1",
            operation="inspect",
            risk="SAFE",
            approval="NOT_REQUESTED",
            target=".",
            context=None,
            readiness="READY",
            reason="",
            ready=True,
        )

        task = TaskModel(
            task_id="task-1",
            project_id="project-1",
            description="Persist workflow",
            context="test context",
        )

        plan = PlanModel(
            task_id="task-1",
            project_id="project-1",
            steps=(step,),
            ready=True,
            issues=(),
            warnings=(),
        )

        run = RunModel(
            run_id="run-1",
            task_id="task-1",
        )

        result = ResultModel(
            run_id="run-1",
            status="SUCCESS",
            total_steps=1,
            successful_steps=1,
            failed_steps=0,
            blocked_steps=0,
            completed_successfully=True,
            failure_index=None,
        )

        snapshot = SnapshotModel(
            run_id="run-1",
            task_id="task-1",
            run_status="completed",
            step_states={"step-1": "success"},
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        return ApplicationExecutionModel(
            task=task,
            plan=plan,
            run=run,
            result=result,
            snapshot=snapshot,
            verification=None,
        )

    def test_exists_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            service = WorkflowPersistenceService()
            execution = self._execution()

            self.assertFalse(service.exists(project))

            saved = service.save(execution, project)

            self.assertTrue(saved.is_file())
            self.assertTrue(service.exists(project))
            self.assertEqual(service.load(project), execution)

    def test_load_missing_storage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = WorkflowPersistenceService()

            with self.assertRaises(FileNotFoundError):
                service.load(Path(directory))

    def test_save_type_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = WorkflowPersistenceService()

            with self.assertRaises(TypeError):
                service.save(object(), Path(directory))


if __name__ == "__main__":
    unittest.main()
