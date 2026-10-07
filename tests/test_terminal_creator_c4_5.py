import os
import unittest

from application.terminal_creator import TerminalCreator
from application.terminal_session import TerminalSessionState


@unittest.skipUnless(os.name == "nt", "C4.5.4 requires Windows")
class TerminalCreatorTests(unittest.TestCase):
    def test_create_starts_real_terminal_process(self):
        creator = TerminalCreator()

        session = creator.create(
            "terminal-test-1",
            os.getcwd(),
            "cmd.exe",
        )

        try:
            self.assertEqual(
                session.state,
                TerminalSessionState.RUNNING,
            )
            self.assertIsInstance(session.process_id, int)
            self.assertGreater(session.process_id, 0)
            self.assertEqual(session.shell, "cmd.exe")
        finally:
            creator.terminate()

    def test_create_uses_explicit_shell_path(self):
        creator = TerminalCreator()

        shell = os.environ.get("COMSPEC", "cmd.exe")
        session = creator.create(
            "terminal-test-2",
            os.getcwd(),
            shell,
        )

        try:
            self.assertEqual(
                session.state,
                TerminalSessionState.RUNNING,
            )
            self.assertEqual(session.shell, shell)
        finally:
            creator.terminate()

    def test_invalid_shell_is_rejected(self):
        creator = TerminalCreator()

        with self.assertRaises(ValueError):
            creator.create(
                "terminal-test-3",
                os.getcwd(),
                "not-a-real-shell.exe",
            )

    def test_missing_working_directory_marks_creation_failed(self):
        creator = TerminalCreator()

        session = creator.create(
            "terminal-test-4",
            os.path.join(os.getcwd(), "__missing_terminal_cwd__"),
            "cmd.exe",
        )

        self.assertEqual(
            session.state,
            TerminalSessionState.FAILED,
        )
        self.assertIsNone(session.process_id)


if __name__ == "__main__":
    unittest.main()
