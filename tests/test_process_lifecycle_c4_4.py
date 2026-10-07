import unittest

from application.process_lifecycle import (
    ProcessLifecycleState,
    ProcessSnapshot,
    TERMINAL_PROCESS_STATES,
)


class ProcessLifecycleC44Tests(unittest.TestCase):
    def test_all_required_states_exist(self):
        self.assertEqual(
            {state.value for state in ProcessLifecycleState},
            {
                "STARTING",
                "RUNNING",
                "PAUSED",
                "EXITED",
                "FAILED",
                "CRASHED",
                "HUNG",
            },
        )

    def test_snapshot_is_immutable(self):
        snapshot = ProcessSnapshot(
            process_id=1234,
            state=ProcessLifecycleState.RUNNING,
        )
        with self.assertRaises(AttributeError):
            snapshot.state = ProcessLifecycleState.EXITED

    def test_process_id_must_be_positive(self):
        with self.assertRaises(ValueError):
            ProcessSnapshot(
                process_id=0,
                state=ProcessLifecycleState.STARTING,
            )

    def test_invalid_state_is_rejected(self):
        with self.assertRaises(TypeError):
            ProcessSnapshot(
                process_id=1234,
                state="RUNNING",
            )

    def test_terminal_states_are_explicit(self):
        self.assertEqual(
            TERMINAL_PROCESS_STATES,
            {
                ProcessLifecycleState.EXITED,
                ProcessLifecycleState.FAILED,
                ProcessLifecycleState.CRASHED,
            },
        )

    def test_exit_code_is_optional_and_preserved(self):
        snapshot = ProcessSnapshot(
            process_id=1234,
            state=ProcessLifecycleState.EXITED,
            exit_code=3,
        )
        self.assertEqual(snapshot.exit_code, 3)


if __name__ == "__main__":
    unittest.main()
