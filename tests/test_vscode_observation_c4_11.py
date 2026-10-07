import unittest

from application.observation_event import ObservationEvent
from application.vscode_observation import VSCodeObservation


class VSCodeObservationTests(unittest.TestCase):
    def test_workspace_observation(self):
        event = VSCodeObservation().workspace(
            root="C:/project",
            state="opened",
        )

        self.assertIsInstance(event, ObservationEvent)
        self.assertEqual(event.source, "vscode")
        self.assertEqual(event.event_type, "workspace")
        self.assertEqual(event.observed_state, "opened")
        self.assertEqual(event.payload["root"], "C:/project")

    def test_problem_observation(self):
        event = VSCodeObservation().problem(
            severity="error",
            message="build failed",
            resource="src/main.py",
        )

        self.assertEqual(event.event_type, "problem")
        self.assertEqual(event.payload["severity"], "error")
        self.assertEqual(event.payload["message"], "build failed")

    def test_extension_observation(self):
        event = VSCodeObservation().extension(
            extension_id="example.extension",
            state="activated",
        )

        self.assertEqual(event.event_type, "extension")
        self.assertEqual(event.payload["extension_id"], "example.extension")

    def test_connection_observation(self):
        event = VSCodeObservation().connection(state="connected")

        self.assertEqual(event.event_type, "connection")
        self.assertEqual(event.observed_state, "connected")

    def test_command_observation(self):
        event = VSCodeObservation().command(
            command="workbench.action.files.openFile",
            state="completed",
        )

        self.assertEqual(event.event_type, "command")
        self.assertEqual(event.payload["command"], "workbench.action.files.openFile")
        self.assertEqual(event.observed_state, "completed")


    def test_error_observation(self):
        event = VSCodeObservation().error(
            message="extension host failed",
            source="vscode",
        )

        self.assertEqual(event.event_type, "error")
        self.assertEqual(event.observed_state, "error")
        self.assertEqual(event.payload["message"], "extension host failed")
        self.assertEqual(event.payload["source"], "vscode")


if __name__ == "__main__":
    unittest.main()
