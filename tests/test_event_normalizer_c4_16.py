import unittest

from application.event_normalizer import EventNormalizer
from application.observation_event import ObservationEvent


class EventNormalizerC416Tests(unittest.TestCase):
    def setUp(self):
        self.normalizer = EventNormalizer()

    def test_normalizes_source_event_type_and_state(self):
        event = ObservationEvent.create(
            event_type="terminal",
            source="Terminal",
            observed_state=" RUNNING ",
            payload={"terminal_id": "terminal-1"},
        )

        normalized = self.normalizer.normalize(event)

        self.assertEqual(normalized.source, "terminal")
        self.assertEqual(normalized.event_type, "terminal.terminal")
        self.assertEqual(normalized.observed_state, "running")
        self.assertEqual(normalized.payload["terminal_id"], "terminal-1")
        self.assertEqual(normalized.payload["normalized_source"], "terminal")
        self.assertEqual(normalized.payload["normalized_event_type"], "terminal.terminal")
        self.assertEqual(normalized.payload["normalized_state"], "running")

    def test_existing_prefixed_event_type_is_not_duplicated(self):
        event = ObservationEvent.create(
            event_type="process.exit",
            source="process",
            observed_state="EXITED",
        )

        normalized = self.normalizer.normalize(event)

        self.assertEqual(normalized.event_type, "process.exit")
        self.assertEqual(normalized.observed_state, "exited")

    def test_preserves_event_identity_and_timestamp(self):
        event = ObservationEvent.create(
            event_id="event-1",
            event_type="execution.completed",
            source="execution",
            observed_state="COMPLETED",
            timestamp="2026-10-07T00:00:00+00:00",
        )

        normalized = self.normalizer.normalize(event)

        self.assertEqual(normalized.event_id, event.event_id)
        self.assertEqual(normalized.timestamp, event.timestamp)

    def test_preserves_context_and_correlation(self):
        event = ObservationEvent.create(
            event_type="command",
            source="vscode",
            observed_state="COMPLETED",
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            execution_id="run-1",
            correlation_id="corr-1",
        )

        normalized = self.normalizer.normalize(event)

        self.assertEqual(normalized.project_id, "project-1")
        self.assertEqual(normalized.task_id, "task-1")
        self.assertEqual(normalized.workflow_id, "workflow-1")
        self.assertEqual(normalized.execution_id, "run-1")
        self.assertEqual(normalized.correlation_id, "corr-1")

    def test_does_not_mutate_original_event(self):
        event = ObservationEvent.create(
            event_type="error",
            source="vscode",
            observed_state="ERROR",
            payload={"message": "failed"},
        )

        normalized = self.normalizer.normalize(event)

        self.assertNotIn("normalized_source", event.payload)
        self.assertNotIn("normalized_event_type", event.payload)
        self.assertNotIn("normalized_state", event.payload)
        self.assertIn("normalized_source", normalized.payload)

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(TypeError):
            self.normalizer.normalize(object())


if __name__ == "__main__":
    unittest.main()
