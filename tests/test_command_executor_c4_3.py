import unittest

from application.command_executor import (
    CommandExecutionResult,
    CommandExecutor,
    ProcessCommand,
)


class CommandExecutorC43Tests(unittest.TestCase):
    def test_explicit_process_command_is_immutable(self):
        command = ProcessCommand("python", ("-c", "print('ok')"))
        with self.assertRaises(Exception):
            command.executable = "other"

    def test_executor_captures_real_output_and_exit_code(self):
        command = ProcessCommand(
            "python",
            ("-c", "print('hello')"),
        )

        result = CommandExecutor().execute(command)

        self.assertIsInstance(result, CommandExecutionResult)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "hello")
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.succeeded)
        self.assertGreaterEqual(result.duration_seconds, 0.0)

    def test_executor_captures_failure_without_faking_success(self):
        command = ProcessCommand(
            "python",
            ("-c", "import sys; print('error', file=sys.stderr); sys.exit(3)"),
        )

        result = CommandExecutor().execute(command)

        self.assertEqual(result.exit_code, 3)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr.strip(), "error")
        self.assertFalse(result.succeeded)

    def test_nonzero_exit_code_is_failure(self):
        command = ProcessCommand(
            "python",
            ("-c", "import sys; sys.exit(7)"),
        )
        result = CommandExecutor().execute(command)
        self.assertEqual(result.exit_code, 7)
        self.assertFalse(result.succeeded)

    def test_os_execution_error_is_propagated(self):
        command = ProcessCommand(
            "pacepilot-command-that-does-not-exist-c43",
        )
        with self.assertRaises(FileNotFoundError):
            CommandExecutor().execute(command)

    def test_invalid_command_is_rejected(self):
        with self.assertRaises(ValueError):
            ProcessCommand("")


if __name__ == "__main__":
    unittest.main()
