import unittest

from application.observation_event import ObservationEvent


class ObservationEventTests(unittest.TestCase):
    def test_create_generates_identity_and_timestamp(self):
        event = ObservationEvent.create(
            event_type="terminal.output",
            source="terminal",
            observed_state="running",
        )

        self.assertTrue(event.event_id)
        self.assertTrue(event.timestamp)
        self.assertEqual(event.event_type, "terminal.output")
        self.assertEqual(event.source, "terminal")
        self.assertEqual(event.observed_state, "running")

    def test_create_preserves_explicit_identity_and_timestamp(self):
        event = ObservationEvent.create(
            event_id="evt-1",
            timestamp="2026-10-07T10:20:30+00:00",
            event_type="process.exit",
            source="process",
            observed_state="exited",
        )

        self.assertEqual(event.event_id, "evt-1")
        self.assertEqual(event.timestamp, "2026-10-07T10:20:30+00:00")

    def test_payload_is_copied(self):
        payload = {"exit_code": 0}
        event = ObservationEvent.create(
            event_type="process.exit",
            source="process",
            observed_state="exited",
            payload=payload,
        )

        payload["exit_code"] = 1

        self.assertEqual(event.payload["exit_code"], 0)

    def test_correlation_context_is_preserved(self):
        event = ObservationEvent.create(
            event_type="execution.completed",
            source="execution",
            observed_state="completed",
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            execution_id="execution-1",
            correlation_id="corr-1",
        )

        self.assertEqual(event.project_id, "project-1")
        self.assertEqual(event.task_id, "task-1")
        self.assertEqual(event.workflow_id, "workflow-1")
        self.assertEqual(event.execution_id, "execution-1")
        self.assertEqual(event.correlation_id, "corr-1")

    def test_empty_required_fields_are_rejected(self):
        fields = {
            "event_id": "evt-1",
            "event_type": "test",
            "source": "test",
            "timestamp": "2026-10-07T10:20:30+00:00",
            "observed_state": "test",
        }

        for field_name in fields:
            values = dict(fields)
            values[field_name] = " "

            with self.subTest(field=field_name):
                with self.assertRaises(ValueError):
                    ObservationEvent(**values)

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            ObservationEvent(
                event_id="evt-1",
                event_type="test",
                source="test",
                timestamp="not-a-timestamp",
                observed_state="test",
            )

    def test_payload_must_be_mapping(self):
        with self.assertRaises(TypeError):
            ObservationEvent(
                event_id="evt-1",
                event_type="test",
                source="test",
                timestamp="2026-10-07T10:20:30+00:00",
                observed_state="test",
                payload="invalid",
            )


if __name__ == "__main__":
    unittest.main()
