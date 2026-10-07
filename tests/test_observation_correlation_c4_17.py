import unittest

from application.observation_correlation import (
    ObservationCorrelation,
    ObservationCorrelator,
)
from application.observation_event import ObservationEvent


class ObservationCorrelationC417Tests(unittest.TestCase):
    def setUp(self):
        self.correlator = ObservationCorrelator()

    def event(self, **kwargs):
        defaults = {
            "event_type": "test",
            "source": "test",
            "observed_state": "running",
        }
        defaults.update(kwargs)
        return ObservationEvent.create(**defaults)

    def test_explicit_correlation_id_has_highest_priority(self):
        event = self.event(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            execution_id="execution-1",
            correlation_id="corr-1",
        )

        result = self.correlator.correlate(event)

        self.assertIsInstance(result, ObservationCorrelation)
        self.assertEqual(result.correlation_key, "corr-1")
        self.assertEqual(result.basis, "correlation")

    def test_execution_id_is_used_when_correlation_is_absent(self):
        event = self.event(
            task_id="task-1",
            execution_id="execution-1",
        )

        result = self.correlator.correlate(event)

        self.assertEqual(result.correlation_key, "execution-1")
        self.assertEqual(result.basis, "execution")

    def test_context_priority_is_stable(self):
        cases = (
            ("workflow_id", "workflow-1", "workflow"),
            ("task_id", "task-1", "task"),
            ("project_id", "project-1", "project"),
        )

        for field_name, value, basis in cases:
            with self.subTest(field_name=field_name):
                result = self.correlator.correlate(
                    self.event(**{field_name: value})
                )
                self.assertEqual(result.correlation_key, value)
                self.assertEqual(result.basis, basis)

    def test_event_id_is_fallback_without_context(self):
        event = self.event(event_id="event-1")

        result = self.correlator.correlate(event)

        self.assertEqual(result.correlation_key, "event-1")
        self.assertEqual(result.basis, "event")

    def test_correlator_does_not_modify_event_or_create_correlation_id(self):
        event = self.event(task_id="task-1")

        result = self.correlator.correlate(event)

        self.assertIs(result.event, event)
        self.assertIsNone(event.correlation_id)
        self.assertEqual(result.correlation_key, "task-1")

    def test_group_preserves_events_and_groups_by_existing_context(self):
        first = self.event(event_id="event-1", task_id="task-1")
        second = self.event(event_id="event-2", task_id="task-1")
        third = self.event(event_id="event-3", task_id="task-2")

        groups = self.correlator.group([first, second, third])

        self.assertEqual(set(groups), {"task-1", "task-2"})
        self.assertEqual(
            [item.event.event_id for item in groups["task-1"]],
            ["event-1", "event-2"],
        )
        self.assertEqual(
            [item.event.event_id for item in groups["task-2"]],
            ["event-3"],
        )

    def test_invalid_event_is_rejected(self):
        with self.assertRaises(TypeError):
            self.correlator.correlate(object())


if __name__ == "__main__":
    unittest.main()
