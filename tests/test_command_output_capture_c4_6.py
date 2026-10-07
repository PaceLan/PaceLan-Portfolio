import unittest

from application.command_executor import (
    CommandExecutionResult,
    CommandExecutor,
    ProcessCommand,
)
from application.process_lifecycle import ProcessLifecycleState


class CommandExecutorC46Tests(unittest.TestCase):
    def test_captures_process_identity_and_state(self):
        result = CommandExecutor().execute(
            ProcessCommand(
                "python",
                ("-c", "print('hello')"),
            )
        )

        self.assertIsInstance(result, CommandExecutionResult)
        self.assertIsInstance(result.process_id, int)
        self.assertGreater(result.process_id, 0)
        self.assertEqual(
            result.process_state,
            ProcessLifecycleState.EXITED,
        )

    def test_captures_execution_metadata(self):
        command = ProcessCommand(
            "python",
            ("-c", "print('metadata')"),
        )

        result = CommandExecutor().execute(command)

        self.assertEqual(
            result.execution_metadata["executable"],
            "python",
        )
        self.assertEqual(
            result.execution_metadata["argv"],
            command.argv,
        )
        self.assertIsNotNone(
            result.execution_metadata["started_at"]
        )
        self.assertIsNotNone(
            result.execution_metadata["finished_at"]
        )

    def test_nonzero_exit_maps_to_failed_process_state(self):
        result = CommandExecutor().execute(
            ProcessCommand(
                "python",
                ("-c", "import sys; sys.exit(4)"),
            )
        )

        self.assertEqual(result.exit_code, 4)
        self.assertEqual(
            result.process_state,
            ProcessLifecycleState.FAILED,
        )
        self.assertFalse(result.succeeded)

    def test_captures_stdout_and_stderr_together(self):
        result = CommandExecutor().execute(
            ProcessCommand(
                "python",
                (
                    "-c",
                    (
                        "import sys; "
                        "print('out'); "
                        "print('err', file=sys.stderr)"
                    ),
                ),
            )
        )

        self.assertEqual(result.stdout.strip(), "out")
        self.assertEqual(result.stderr.strip(), "err")

    def test_duration_is_non_negative(self):
        result = CommandExecutor().execute(
            ProcessCommand(
                "python",
                ("-c", "print('timed')"),
            )
        )

        self.assertGreaterEqual(result.duration_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
