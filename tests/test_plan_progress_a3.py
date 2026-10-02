import unittest

from application import PlanModel, PlanningService, ProgressModel, ProgressService, SnapshotModel, StepModel


class _ContextAgent:
    pass


class TestPlanningServiceA3(unittest.TestCase):
    def test_application_exports_plan_contract(self):
        self.assertIs(PlanningService, __import__("application").PlanningService)
        self.assertIs(PlanModel, __import__("application").PlanModel)

    def test_progress_from_plan(self):
        plan = PlanModel(
            task_id="task-a3",
            project_id="project-a3",
        )

        progress = ProgressService.from_plan(plan)

        self.assertIsInstance(progress, ProgressModel)
        self.assertEqual(progress.task_id, "task-a3")
        self.assertEqual(progress.completed_steps, 0)
        self.assertEqual(progress.total_steps, 0)
        self.assertIsNone(progress.current_step_id)

    def test_progress_from_snapshot(self):
        snapshot = SnapshotModel(
            run_id="run-a3",
            task_id="task-a3",
            run_status="running",
            step_states={
                "step-001": "success",
                "step-002": "success",
                "step-003": "running",
                "step-004": "pending",
            },
            current_step="step-003",
        )

        progress = ProgressService.from_snapshot(snapshot)

        self.assertEqual(progress.task_id, "task-a3")
        self.assertEqual(progress.completed_steps, 2)
        self.assertEqual(progress.total_steps, 4)
        self.assertEqual(progress.current_step_id, "step-003")

    def test_progress_from_plan_with_steps(self):
        plan = PlanModel(
            task_id="task-a3",
            project_id="project-a3",
            steps=(
                StepModel(step_id="step-001", operation="inspect"),
                StepModel(step_id="step-002", operation="build"),
                StepModel(step_id="step-003", operation="verify"),
            ),
        )

        progress = ProgressService.from_plan(plan)

        self.assertEqual(progress.task_id, "task-a3")
        self.assertEqual(progress.completed_steps, 0)
        self.assertEqual(progress.total_steps, 3)
        self.assertEqual(progress.current_step_id, "step-001")


if __name__ == "__main__":
    unittest.main()
