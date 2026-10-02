import unittest

from application import ProgressModel


class TestProgressModelA3(unittest.TestCase):
    def test_default_progress_is_empty(self):
        progress = ProgressModel(task_id="task-a3")

        self.assertEqual(progress.completed_steps, 0)
        self.assertEqual(progress.total_steps, 0)
        self.assertIsNone(progress.current_step_id)

    def test_progress_preserves_step_counts(self):
        progress = ProgressModel(
            task_id="task-a3",
            completed_steps=2,
            total_steps=4,
            current_step_id="step-003",
        )

        self.assertEqual(progress.completed_steps, 2)
        self.assertEqual(progress.total_steps, 4)
        self.assertEqual(progress.current_step_id, "step-003")

    def test_progress_rejects_invalid_counts(self):
        with self.assertRaises(ValueError):
            ProgressModel(
                task_id="task-a3",
                completed_steps=5,
                total_steps=4,
            )


if __name__ == "__main__":
    unittest.main()
