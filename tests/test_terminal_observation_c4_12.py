import unittest

from application.observation_event import ObservationEvent
from application.terminal_observation import TerminalObservation


class TerminalObservationTests(unittest.TestCase):
    def setUp(self):
        self.observer = TerminalObservation()

    def test_created(self):
        event = self.observer.created(
            terminal_id="terminal-1",
            session_id="session-1",
            cwd="C:/project",
        )
        self.assertIsInstance(event, ObservationEvent)
        self.assertEqual(event.source, "terminal")
        self.assertEqual(event.event_type, "terminal")
        self.assertEqual(event.observed_state, "CREATED")
        self.assertEqual(event.payload["terminal_id"], "terminal-1")

    def test_opened(self):
        event = self.observer.opened(
            terminal_id="terminal-1",
            session_id="session-1",
        )
        self.assertEqual(event.observed_state, "OPEN")
        self.assertEqual(event.payload["session_id"], "session-1")

    def test_output(self):
        event = self.observer.output(
            terminal_id="terminal-1",
            output="pytest passed",
        )
        self.assertEqual(event.observed_state, "OUTPUT")
        self.assertEqual(event.payload["output"], "pytest passed")

    def test_exit(self):
        event = self.observer.exited(
            terminal_id="terminal-1",
            exit_code=0,
        )
        self.assertEqual(event.observed_state, "EXITED")
        self.assertEqual(event.payload["exit_code"], 0)

    def test_closed(self):
        event = self.observer.closed(
            terminal_id="terminal-1",
            session_id="session-1",
        )
        self.assertEqual(event.observed_state, "CLOSED")

    def test_state(self):
        event = self.observer.state(
            terminal_id="terminal-1",
            state="RUNNING",
        )
        self.assertEqual(event.observed_state, "RUNNING")


if __name__ == "__main__":
    unittest.main()
