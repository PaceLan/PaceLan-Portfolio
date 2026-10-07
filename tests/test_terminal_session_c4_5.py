import unittest

from application.terminal_session import (
    TerminalSession,
    TerminalSessionState,
)


class TerminalSessionTests(unittest.TestCase):
    def test_default_session_is_created(self):
        session = TerminalSession(
            session_id="terminal-1",
            shell="powershell.exe",
            cwd="C:\\workspace",
        )

        self.assertEqual(session.session_id, "terminal-1")
        self.assertEqual(session.shell, "powershell.exe")
        self.assertEqual(session.cwd, "C:\\workspace")
        self.assertIsNone(session.process_id)
        self.assertIs(session.state, TerminalSessionState.CREATED)

    def test_session_can_reference_process(self):
        session = TerminalSession(
            session_id="terminal-2",
            shell="cmd.exe",
            cwd="C:\\workspace",
            process_id=1234,
            state=TerminalSessionState.RUNNING,
        )

        self.assertEqual(session.process_id, 1234)
        self.assertIs(session.state, TerminalSessionState.RUNNING)

    def test_all_terminal_states_are_defined(self):
        self.assertEqual(
            {state.value for state in TerminalSessionState},
            {
                "CREATED",
                "RUNNING",
                "CLOSED",
                "FAILED",
                "DISCONNECTED",
            },
        )

    def test_invalid_session_id_is_rejected(self):
        with self.assertRaises(ValueError):
            TerminalSession("", "powershell.exe", "C:\\workspace")

    def test_invalid_shell_is_rejected(self):
        with self.assertRaises(ValueError):
            TerminalSession("terminal-1", "", "C:\\workspace")

    def test_invalid_process_id_is_rejected(self):
        with self.assertRaises(ValueError):
            TerminalSession(
                "terminal-1",
                "powershell.exe",
                "C:\\workspace",
                process_id=0,
            )


if __name__ == "__main__":
    unittest.main()
