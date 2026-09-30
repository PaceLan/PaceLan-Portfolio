import unittest

from agent_workflow.execution_tracking import RunStatus, StepStatus


class ExecutionTrackingEnumTests(unittest.TestCase):
    def test_run_status_members(self):
        self.assertEqual(
            [status.name for status in RunStatus],
            ["CREATED", "RUNNING", "COMPLETED", "FAILED"],
        )

    def test_run_status_values(self):
        self.assertEqual(RunStatus.CREATED.value, "CREATED")
        self.assertEqual(RunStatus.RUNNING.value, "RUNNING")
        self.assertEqual(RunStatus.COMPLETED.value, "COMPLETED")
        self.assertEqual(RunStatus.FAILED.value, "FAILED")

    def test_step_status_members(self):
        self.assertEqual(
            [status.name for status in StepStatus],
            ["PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED"],
        )

    def test_step_status_values(self):
        self.assertEqual(StepStatus.PENDING.value, "PENDING")
        self.assertEqual(StepStatus.RUNNING.value, "RUNNING")
        self.assertEqual(StepStatus.SUCCESS.value, "SUCCESS")
        self.assertEqual(StepStatus.FAILED.value, "FAILED")
        self.assertEqual(StepStatus.SKIPPED.value, "SKIPPED")

    def test_run_status_is_enum(self):
        self.assertTrue(issubclass(RunStatus, __import__("enum").Enum))

    def test_step_status_is_enum(self):
        self.assertTrue(issubclass(StepStatus, __import__("enum").Enum))


if __name__ == "__main__":
    unittest.main()
