import tempfile
import unittest
from pathlib import Path

from agent_workflow.dependency_graph import DependencyGraph
from agent_workflow.file_index import FileIndex
from agent_workflow.project_context import ProjectContext
from agent_workflow.project_scanner import (
    ProjectScanResult,
    ProjectScanStatistics,
)

from application.context_persistence import ContextPersistenceService
from application.history import AgentHistoryEntry, AgentHistoryStatus
from application.history_storage import AgentHistoryStorage
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
from application.restore_service import RestoreService
from application.workflow_storage import WorkflowStorage


class TestRestoreServiceCompleteB5(unittest.TestCase):
    def test_complete_persisted_state_restores_together(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            project = ProjectModel(
                project_id="p-b5",
                goal=ProjectGoal(text="restore everything"),
            )
            ProjectStorage().save(project, root)

            task = TaskModel(
                task_id="t-b5",
                project_id="p-b5",
                description="persistent task",
            )
            plan = PlanModel(
                task_id="t-b5",
                project_id="p-b5",
            )
            run = RunModel(
                run_id="r-b5",
                task_id="t-b5",
            )
            result = ResultModel(
                run_id="r-b5",
                status="success",
                completed_successfully=True,
            )
            snapshot = SnapshotModel(
                run_id="run-b5",
                task_id="t-b5",
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

            history_entry = AgentHistoryEntry(
                history_id="h-b5",
                project_id="p-b5",
                task_id="t-b5",
                execution_id="r-b5",
                verification_status="VERIFIED",
                result_status=AgentHistoryStatus.COMPLETED,
                timestamp="2026-01-01T00:00:00+00:00",
            )
            AgentHistoryStorage().save((history_entry,), root)

            resolved_root = root.resolve()
            context = ProjectContext(
                root_path=resolved_root,
                scan_result=ProjectScanResult(
                    root_path=resolved_root,
                    files=(),
                    directories=(),
                    statistics=ProjectScanStatistics(
                        file_count=0,
                        directory_count=0,
                        total_size=0,
                        ignored_count=0,
                    ),
                    errors=(),
                ),
                file_index=FileIndex(
                    root_path=resolved_root,
                    entries=(),
                ),
                python_asts=(),
                python_relationships=(),
                dependency_graph=DependencyGraph(
                    nodes=(),
                    edges=(),
                ),
            )
            ContextPersistenceService().save(context, root)

            restored = RestoreService().restore(root)

            self.assertEqual(restored.project.project_id, "p-b5")
            self.assertIsNotNone(restored.workflow)
            self.assertEqual(restored.workflow.task.task_id, "t-b5")
            self.assertEqual(restored.workflow.run.run_id, "r-b5")
            self.assertEqual(restored.workflow.result.status, "success")
            self.assertEqual(len(restored.history), 1)
            self.assertEqual(restored.history[0].task_id, "t-b5")
            self.assertIsNotNone(restored.context)
            self.assertEqual(
                restored.context.root_path,
                root.resolve(),
            )


if __name__ == "__main__":
    unittest.main()
