import unittest

from application.execution_context import ExecutionContext
from application.terminal_context_binding import (
    TerminalContextBinding,
    bind_terminal_context,
)
from application.terminal_session import (
    TerminalSession,
    TerminalSessionState,
)
from application.terminal_session_binding import TerminalSessionBinding


class TestTerminalContextBinding(unittest.TestCase):

    def _terminal(self):
        session = TerminalSession(
            session_id="session-1",
            shell="powershell",
            cwd=".",
            state=TerminalSessionState.RUNNING,
        )
        return TerminalSessionBinding(
            session=session,
            terminal_id="terminal-1",
        )

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            terminal_id="terminal-1",
            terminal_session_id="session-1",
            terminal_state=TerminalSessionState.RUNNING.value,
        )

    def test_binding_preserves_terminal_and_context(self):
        terminal = self._terminal()
        context = self._context()

        binding = bind_terminal_context(terminal, context)

        self.assertIs(binding.terminal, terminal)
        self.assertIs(binding.context, context)

    def test_binding_exposes_terminal_identity(self):
        binding = bind_terminal_context(
            self._terminal(),
            self._context(),
        )

        self.assertEqual(binding.terminal_id, "terminal-1")
        self.assertEqual(binding.session_id, "session-1")
        self.assertEqual(
            binding.terminal_state,
            TerminalSessionState.RUNNING.value,
        )
        self.assertEqual(binding.run_id, "run-1")
        self.assertEqual(binding.task_id, "task-1")

    def test_terminal_id_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            terminal_id="terminal-2",
            terminal_session_id="session-1",
            terminal_state=TerminalSessionState.RUNNING.value,
        )

        with self.assertRaises(ValueError):
            TerminalContextBinding(self._terminal(), context)

    def test_session_id_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            terminal_id="terminal-1",
            terminal_session_id="session-2",
            terminal_state=TerminalSessionState.RUNNING.value,
        )

        with self.assertRaises(ValueError):
            TerminalContextBinding(self._terminal(), context)

    def test_terminal_state_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            terminal_id="terminal-1",
            terminal_session_id="session-1",
            terminal_state=TerminalSessionState.CLOSED.value,
        )

        with self.assertRaises(ValueError):
            TerminalContextBinding(self._terminal(), context)

    def test_binding_is_immutable(self):
        binding = bind_terminal_context(
            self._terminal(),
            self._context(),
        )

        with self.assertRaises(AttributeError):
            binding.terminal = self._terminal()


if __name__ == "__main__":
    unittest.main()
