import unittest

from application.autonomous_progress import AutonomousProgressService
from application.models import PlanModel, SnapshotModel, StepModel


class AutonomousProgressServiceTests(unittest.TestCase):
    def test_from_plan_delegates_to_existing_progress_contract(self):
        plan = PlanModel(
            task_id="task-c6-3",
            project_id="project-c6-3",
            steps=(
                StepModel(step_id="step-1", operation="inspect"),
                StepModel(step_id="step-2", operation="verify"),
            ),
        )

        progress = AutonomousProgressService.from_plan(plan)

        self.assertEqual(progress.task_id, "task-c6-3")
        self.assertEqual(progress.completed_steps, 0)
        self.assertEqual(progress.total_steps, 2)
        self.assertEqual(progress.current_step_id, "step-1")

    def test_from_snapshot_delegates_to_existing_progress_contract(self):
        snapshot = SnapshotModel(
            run_id="run-c6-3",
            task_id="task-c6-3",
            run_status="running",
            step_states={
                "step-1": "success",
                "step-2": "running",
                "step-3": "pending",
            },
            current_step="step-2",
        )

        progress = AutonomousProgressService.from_snapshot(snapshot)

        self.assertEqual(progress.task_id, "task-c6-3")
        self.assertEqual(progress.completed_steps, 1)
        self.assertEqual(progress.total_steps, 3)
        self.assertEqual(progress.current_step_id, "step-2")

    def test_invalid_plan_is_rejected_by_existing_contract(self):
        with self.assertRaises(TypeError):
            AutonomousProgressService.from_plan("invalid")

    def test_invalid_snapshot_is_rejected_by_existing_contract(self):
        with self.assertRaises(TypeError):
            AutonomousProgressService.from_snapshot("invalid")


if __name__ == "__main__":
    unittest.main()
