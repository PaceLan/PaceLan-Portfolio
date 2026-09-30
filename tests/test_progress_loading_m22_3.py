import unittest

from ui.agent_state import AgentExecutionState
from ui.progress import ProgressMapper, ProgressMode, ProgressState


class M223ProgressLoadingTests(unittest.TestCase):

    def test_progress_state_is_immutable_and_validated(self):
        state = ProgressState(
            mode=ProgressMode.PROCESSING,
            progress=40,
            current_step="step-002",
            completed_steps=2,
            total_steps=5,
        )
        self.assertEqual(state.progress, 40)
        with self.assertRaises(ValueError):
            ProgressState(progress=101)
        with self.assertRaises(ValueError):
            ProgressState(completed_steps=4, total_steps=3)

    def test_none_execution_is_idle(self):
        state = ProgressMapper.from_execution(None)
        self.assertEqual(state.mode, ProgressMode.IDLE)
        self.assertEqual(state.progress, 0)

    def test_processing_uses_real_execution_progress(self):
        execution = AgentExecutionState(
            status="IN_PROGRESS",
            current_step="step-002",
            step_states=("SUCCESS", "IN_PROGRESS", "PENDING"),
            progress=33,
        )
        state = ProgressMapper.from_execution(execution)

        self.assertEqual(state.mode, ProgressMode.PROCESSING)
        self.assertEqual(state.progress, 33)
        self.assertEqual(state.current_step, "step-002")
        self.assertEqual(state.completed_steps, 1)
        self.assertEqual(state.total_steps, 3)

    def test_completed_forces_terminal_progress(self):
        execution = AgentExecutionState(
            status="SUCCESS",
            progress=72,
            step_states=("SUCCESS", "SUCCESS"),
        )
        state = ProgressMapper.from_execution(execution)

        self.assertEqual(state.mode, ProgressMode.COMPLETE)
        self.assertEqual(state.progress, 100)

    def test_failed_state_is_not_presented_as_processing(self):
        execution = AgentExecutionState(
            status="FAILED",
            progress=50,
            failure_reason="execution failed",
        )
        state = ProgressMapper.from_execution(execution)
        self.assertEqual(state.mode, ProgressMode.FAILED)

    def test_progress_is_clamped_to_presentation_bounds(self):
        execution = AgentExecutionState(
            status="IN_PROGRESS",
            progress=150,
        )
        state = ProgressMapper.from_execution(execution)
        self.assertEqual(state.progress, 100)


if __name__ == "__main__":
    unittest.main()