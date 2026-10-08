import tempfile
import unittest
from pathlib import Path

from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ProjectGoal,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.project_storage import ProjectStorage
from application.workflow_storage import WorkflowStorage
from application.restore_service import RestoreService


class TestRestoreServiceFullB5(unittest.TestCase):
    def test_restore_full_persisted_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            project = ProjectModel(
                project_id="p-full",
                goal=ProjectGoal(text="full restore"),
            )
            ProjectStorage().save(project, root)

            task = TaskModel(
                task_id="t1",
                project_id="p-full",
                description="restore task",
            )
            plan = PlanModel(
                task_id="t1",
                project_id="p-full",
            )
            run = RunModel(
                run_id="r1",
                task_id="t1",
            )
            result = ResultModel(
                run_id="r1",
                status="completed",
            )
            snapshot = SnapshotModel(
                run_id="run-1",
                task_id="t1",
                run_status="COMPLETED",
            )
            workflow = ApplicationExecutionModel(
                task=task,
                plan=plan,
                run=run,
                result=result,
                snapshot=snapshot,
            )

            WorkflowStorage().save(workflow, root)

            service = RestoreService()
            restored = service.restore(root)

            self.assertEqual(restored.project.project_id, "p-full")
            self.assertIsNotNone(restored.workflow)
            self.assertEqual(restored.workflow.task.task_id, "t1")
            self.assertEqual(restored.workflow.run.run_id, "r1")
            self.assertEqual(restored.workflow.result.status, "completed")

    def test_restore_service_reports_all_existing_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            ProjectStorage().save(
                ProjectModel(
                    project_id="p2",
                    goal=ProjectGoal(text="layers"),
                ),
                root,
            )

            self.assertTrue(RestoreService().has_project(root))
            self.assertFalse(RestoreService().has_workflow(root))


if __name__ == "__main__":
    unittest.main()
