import tempfile
import unittest
from pathlib import Path

from application.bootstrap import ApplicationBootstrap
from application.models import ProjectGoal
from application.autonomous_development import AutonomousDevelopmentRequest
from application.history_storage import AgentHistoryStorage


class AutonomousDevelopmentC653Tests(unittest.TestCase):
    def test_bootstrap_runtime_runs_complete_autonomous_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample.py").write_text(
                "def sample():\n    return True\n",
                encoding="utf-8",
            )

            runtime = ApplicationBootstrap.create(root)

            runtime.goal_authority.set_goal(
                ProjectGoal("Build the requested feature")
            )
            runtime.goal_authority.confirm()

            result = runtime.autonomous_development_service.run(
                AutonomousDevelopmentRequest(
                    project_id="project-c6-5-3",
                    title="Implement feature",
                    description="Implement the requested feature",
                )
            )

            tasks = runtime.task_management.list_for_project(
                "project-c6-5-3"
            )

            self.assertEqual(len(tasks), 1)

            task = tasks[0]

            self.assertEqual(task.title, "Implement feature")
            self.assertIsNotNone(task.plan_id)

            self.assertEqual(
                result.task.task_id,
                task.task_id,
            )
            self.assertEqual(
                result.plan.task_id,
                task.task_id,
            )

            workflow_plan = runtime.autonomous_planning._plan_binding.get(
                task.task_id
            )
            self.assertGreater(len(workflow_plan.steps), 0)

            self.assertEqual(
                workflow_plan.task.task_id,
                task.task_id,
            )
            self.assertEqual(
                workflow_plan.task.project_id,
                task.project_id,
            )

            # Assert actual execution, verification, and persisted history.
            self.assertEqual(result.result.status, "COMPLETED")
            self.assertTrue(result.result.completed_successfully)
            self.assertEqual(result.result.total_steps, 1)
            self.assertEqual(result.result.successful_steps, 1)
            self.assertEqual(result.result.failed_steps, 0)
            self.assertEqual(result.result.blocked_steps, 0)
            self.assertTrue(result.verification.verified)
            self.assertEqual(result.verification.status.value, "verified")

            history_file = root / ".pacepilot" / "agent_history.json"
            self.assertTrue(history_file.is_file())

            entries = AgentHistoryStorage().load(root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].project_id, task.project_id)
            self.assertEqual(entries[0].task_id, task.task_id)
            self.assertEqual(entries[0].result_status.value, "completed")
            self.assertEqual(entries[0].verification_status, "verified")


if __name__ == "__main__":
    unittest.main()
