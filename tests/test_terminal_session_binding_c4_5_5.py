import unittest

from application.terminal_session import (
    TerminalSession,
    TerminalSessionState,
)
from application.terminal_session_binding import (
    TerminalSessionBinding,
    create_terminal_session_binding,
)
from application.vscode_control_channel import TerminalControlResult


class FakeChannel:
    def __init__(self):
        self.calls = []

    def create(self, cwd, name, session_id):
        self.calls.append(("create", cwd, name, session_id))
        return TerminalControlResult(
            operation="create",
            terminal_id="terminal-1",
            session_id=session_id,
            state="RUNNING",
        )

    def send(self, terminal_id, command, session_id):
        self.calls.append(
            ("send", terminal_id, command, session_id)
        )
        return TerminalControlResult(
            operation="send",
            terminal_id=terminal_id,
            session_id=session_id,
            state="RUNNING",
        )

    def status(self, terminal_id, session_id):
        self.calls.append(
            ("status", terminal_id, session_id)
        )
        return TerminalControlResult(
            operation="status",
            terminal_id=terminal_id,
            session_id=session_id,
            state="RUNNING",
        )

    def close(self, terminal_id, session_id):
        self.calls.append(
            ("close", terminal_id, session_id)
        )
        return TerminalControlResult(
            operation="close",
            terminal_id=terminal_id,
            session_id=session_id,
            state="CLOSED",
        )


class TerminalSessionBindingC455Tests(unittest.TestCase):
    def setUp(self):
        self.session = TerminalSession(
            session_id="session-1",
            shell="powershell.exe",
            cwd="C:\\workspace",
        )
        self.channel = FakeChannel()

    def test_create_binds_session_and_terminal(self):
        binding = create_terminal_session_binding(
            self.channel,
            self.session,
        )

        self.assertEqual(binding.session_id, "session-1")
        self.assertEqual(binding.terminal_id, "terminal-1")
        self.assertEqual(
            binding.state,
            TerminalSessionState.RUNNING,
        )
        self.assertEqual(
            self.channel.calls,
            [(
                "create",
                "C:\\workspace",
                "PacePilot",
                "session-1",
            )],
        )

    def test_send_preserves_binding(self):
        binding = create_terminal_session_binding(
            self.channel,
            self.session,
        )

        updated = binding.send(
            self.channel,
            "echo hello",
        )

        self.assertEqual(updated.session_id, "session-1")
        self.assertEqual(updated.terminal_id, "terminal-1")
        self.assertEqual(
            updated.state,
            TerminalSessionState.RUNNING,
        )

    def test_close_updates_terminal_session_state(self):
        binding = create_terminal_session_binding(
            self.channel,
            self.session,
        )

        updated = binding.close(self.channel)

        self.assertEqual(
            updated.state,
            TerminalSessionState.CLOSED,
        )

    def test_rejects_session_mismatch(self):
        result = TerminalControlResult(
            operation="create",
            terminal_id="terminal-1",
            session_id="other-session",
            state="RUNNING",
        )

        with self.assertRaises(ValueError):
            TerminalSessionBinding.from_result(
                self.session,
                result,
            )

    def test_rejects_terminal_mismatch(self):
        binding = TerminalSessionBinding(
            session=TerminalSession(
                session_id="session-1",
                shell="powershell.exe",
                cwd="C:\\workspace",
                state=TerminalSessionState.RUNNING,
            ),
            terminal_id="terminal-1",
        )

        result = TerminalControlResult(
            operation="status",
            terminal_id="terminal-2",
            session_id="session-1",
            state="RUNNING",
        )

        with self.assertRaises(ValueError):
            binding.apply_result(result)


if __name__ == "__main__":
    unittest.main()
