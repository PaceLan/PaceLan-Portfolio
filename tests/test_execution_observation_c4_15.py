import unittest

from application.execution_context import ExecutionContext
from application.execution_observation import ExecutionObservation
from application.models import ExecutionModel, ResultModel
from application.observation_event import ObservationEvent


class ExecutionObservationC415Tests(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            command_id="command-1",
            workflow_id="workflow-1",
            process_id=1234,
            process_state="RUNNING",
            terminal_id="terminal-1",
            terminal_session_id="session-1",
            terminal_state="RUNNING",
            execution_state="RUNNING",
            recoverability="RECOVERABLE",
        )

    def test_context_creates_observation_event(self):
        event = ExecutionObservation.context(self.context)

        self.assertIsInstance(event, ObservationEvent)
        self.assertEqual(event.source, "execution")
        self.assertEqual(event.event_type, "execution")
        self.assertEqual(event.observed_state, "RUNNING")
        self.assertEqual(event.execution_id, "run-1")
        self.assertEqual(event.project_id, "project-1")
        self.assertEqual(event.task_id, "task-1")
        self.assertEqual(event.workflow_id, "workflow-1")
        self.assertEqual(event.payload["step_id"], "step-1")
        self.assertEqual(event.payload["process_state"], "RUNNING")
        self.assertEqual(event.payload["terminal_state"], "RUNNING")

    def test_lifecycle_factories_preserve_real_context(self):
        factories = (
            ("started", "STARTED"),
            ("running", "RUNNING"),
            ("paused", "PAUSED"),
            ("stopped", "STOPPED"),
            ("completed", "COMPLETED"),
            ("failed", "FAILED"),
        )

        for name, state in factories:
            with self.subTest(state=state):
                event = getattr(ExecutionObservation, name)(self.context)
                self.assertEqual(event.observed_state, "RUNNING")
                self.assertEqual(event.payload["state_event"], state)
                self.assertEqual(event.execution_id, "run-1")

    def test_execution_model_creates_observation_event(self):
        model = ExecutionModel(run_id="run-2", status="PAUSED")

        event = ExecutionObservation.execution(
            model,
            task_id="task-2",
            project_id="project-2",
            workflow_id="workflow-2",
        )

        self.assertEqual(event.observed_state, "PAUSED")
        self.assertEqual(event.execution_id, "run-2")
        self.assertEqual(event.task_id, "task-2")
        self.assertEqual(event.payload["run_id"], "run-2")

    def test_result_model_preserves_real_result(self):
        result = ResultModel(
            run_id="run-3",
            status="FAILED",
            total_steps=5,
            successful_steps=3,
            failed_steps=1,
            blocked_steps=1,
            completed_successfully=False,
            failure_index=4,
        )

        event = ExecutionObservation.result(
            result,
            task_id="task-3",
            project_id="project-3",
            workflow_id="workflow-3",
        )

        self.assertEqual(event.observed_state, "FAILED")
        self.assertEqual(event.execution_id, "run-3")
        self.assertEqual(event.payload["total_steps"], 5)
        self.assertEqual(event.payload["successful_steps"], 3)
        self.assertEqual(event.payload["failed_steps"], 1)
        self.assertEqual(event.payload["blocked_steps"], 1)
        self.assertFalse(event.payload["completed_successfully"])
        self.assertEqual(event.payload["failure_index"], 4)

    def test_custom_payload_and_correlation_are_preserved(self):
        event = ExecutionObservation.context(
            self.context,
            correlation_id="corr-1",
            payload={"source_detail": "checkpoint"},
        )

        self.assertEqual(event.correlation_id, "corr-1")
        self.assertEqual(event.payload["source_detail"], "checkpoint")

    def test_invalid_models_are_rejected(self):
        with self.assertRaises(TypeError):
            ExecutionObservation.context(object())

        with self.assertRaises(TypeError):
            ExecutionObservation.execution(object())

        with self.assertRaises(TypeError):
            ExecutionObservation.result(object())


if __name__ == "__main__":
    unittest.main()
