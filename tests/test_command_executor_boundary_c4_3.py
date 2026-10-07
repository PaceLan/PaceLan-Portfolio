import unittest
from pathlib import Path

from application.command_executor import CommandExecutor, ProcessCommand


class CommandExecutorBoundaryC43Tests(unittest.TestCase):
    def test_argv_order_is_preserved(self):
        command = ProcessCommand(
            "python",
            ("-c", "import sys; print('|'.join(sys.argv[1:]))", "one", "two"),
        )
        result = CommandExecutor().execute(command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "one|two")

    def test_cwd_is_applied(self):
        command = ProcessCommand(
            "python",
            ("-c", "import os; print(os.path.basename(os.getcwd()))"),
            cwd=Path.cwd(),
        )
        result = CommandExecutor().execute(command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), Path.cwd().name)

    def test_environment_is_applied(self):
        command = ProcessCommand(
            "python",
            ("-c", "import os; print(os.environ['PACEPILOT_C43'])"),
            env={"PACEPILOT_C43": "verified"},
        )
        result = CommandExecutor().execute(command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "verified")

    def test_missing_executable_is_not_reported_as_success(self):
        command = ProcessCommand(
            "pacepilot-command-that-does-not-exist-c43",
        )
        with self.assertRaises(FileNotFoundError):
            CommandExecutor().execute(command)


if __name__ == "__main__":
    unittest.main()
