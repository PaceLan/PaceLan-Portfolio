import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner

from application.autonomous_planning import (
    AutonomousPlanningRequest,
    AutonomousPlanningService,
)
from application.goal_authority import GoalAuthority
from application.models import ProjectGoal
from application.services import PlanningService
from application.task_management import TaskManagementService


class AutonomousPlanningServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        (root / "sample.py").write_text(
            "def sample():\n    return True\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)
        agent = ProjectContextAgentInterface(context)

        self.goal_authority = GoalAuthority()
        self.goal_authority.set_goal(
            ProjectGoal("Build the requested feature")
        )
        self.goal_authority.confirm()

        self.tasks = TaskManagementService()
        self.product_task = self.tasks.create(
            "project-1",
            "Implement feature",
            "Implement the requested feature",
        )

        self.planning = PlanningService(agent)
        self.service = AutonomousPlanningService(
            self.goal_authority,
            self.planning,
            self.tasks,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_creates_plan_and_binds_task(self):
        result = self.service.create_from_task(
            AutonomousPlanningRequest(
                project_id="project-1",
                task_id=self.product_task.task_id,
            )
        )

        self.assertEqual(result.plan.task_id, self.product_task.task_id)
        self.assertEqual(result.plan.project_id, "project-1")
        self.assertEqual(result.task.task_id, self.product_task.task_id)
        self.assertEqual(result.task.plan_id, result.plan.task_id)

    def test_requires_confirmed_goal(self):
        authority = GoalAuthority()
        service = AutonomousPlanningService(
            authority,
            self.planning,
            self.tasks,
        )

        with self.assertRaises(ValueError):
            service.create_from_task(
                AutonomousPlanningRequest(
                    project_id="project-1",
                    task_id=self.product_task.task_id,
                )
            )

    def test_rejects_project_mismatch(self):
        with self.assertRaises(ValueError):
            self.service.create_from_task(
                AutonomousPlanningRequest(
                    project_id="project-2",
                    task_id=self.product_task.task_id,
                )
            )

        self.assertIsNone(
            self.tasks.get(self.product_task.task_id).plan_id
        )

    def test_does_not_execute_workflow(self):
        result = self.service.create_from_task(
            AutonomousPlanningRequest(
                project_id="project-1",
                task_id=self.product_task.task_id,
            )
        )

        self.assertEqual(result.task.plan_id, result.plan.task_id)


if __name__ == "__main__":
    unittest.main()
