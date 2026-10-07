import unittest

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentResponse,
    ExternalAgentStatus,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_observation import ExternalAgentObservation
from application.observation_event import ObservationEvent


class ExternalAgentObservationC414Tests(unittest.TestCase):
    def test_status_becomes_connection_event(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.CONNECTED,
            message="connected",
        )

        event = ExternalAgentObservation.status(status)

        self.assertIsInstance(event, ObservationEvent)
        self.assertEqual(event.event_type, "external_agent")
        self.assertEqual(event.source, "external_agent")
        self.assertEqual(event.observed_state, "connected")
        self.assertEqual(event.payload["message"], "connected")

    def test_waiting_external_preserves_reason_and_recoverability(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=ExternalConnectionReason.SAFETY_CHECK,
            recoverable=True,
        )

        event = ExternalAgentObservation.status(status)

        self.assertEqual(event.observed_state, "waiting_external")
        self.assertEqual(event.payload["reason"], "safety_check")
        self.assertTrue(event.payload["recoverable"])

    def test_request_preserves_task_and_workflow_context(self):
        request = ExternalAgentRequest(
            task_id="task-1",
            payload="inspect",
            workflow_id="workflow-1",
        )

        event = ExternalAgentObservation.request(
            request,
            command="inspect_task",
            project_id="project-1",
        )

        self.assertEqual(event.task_id, "task-1")
        self.assertEqual(event.workflow_id, "workflow-1")
        self.assertEqual(event.project_id, "project-1")
        self.assertEqual(event.payload["command"], "inspect_task")
        self.assertEqual(event.payload["request_payload"], "inspect")

    def test_response_preserves_payload(self):
        response = ExternalAgentResponse(
            task_id="task-2",
            payload="result",
            workflow_id="workflow-2",
        )

        event = ExternalAgentObservation.response(
            response,
            command="result",
        )

        self.assertEqual(event.observed_state, "RESPONDED")
        self.assertEqual(event.task_id, "task-2")
        self.assertEqual(event.payload["response_payload"], "result")
        self.assertEqual(event.payload["command"], "result")

    def test_command_observation_preserves_result(self):
        event = ExternalAgentObservation.command(
            command="pause",
            task_id="task-3",
            workflow_id="workflow-3",
            result={"accepted": True},
        )

        self.assertEqual(event.observed_state, "COMMAND")
        self.assertEqual(event.payload["command"], "pause")
        self.assertEqual(event.payload["result"], {"accepted": True})

    def test_custom_payload_and_correlation_are_preserved(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=ExternalConnectionReason.CONNECTION_LOST,
            recoverable=True,
        )

        event = ExternalAgentObservation.status(
            status,
            task_id="task-4",
            correlation_id="corr-4",
            payload={"channel": "http"},
        )

        self.assertEqual(event.task_id, "task-4")
        self.assertEqual(event.correlation_id, "corr-4")
        self.assertEqual(event.payload["channel"], "http")

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            ExternalAgentObservation.status("invalid")

        with self.assertRaises(TypeError):
            ExternalAgentObservation.request("invalid")

        with self.assertRaises(TypeError):
            ExternalAgentObservation.response("invalid")

        with self.assertRaises(ValueError):
            ExternalAgentObservation.command(
                command="",
                task_id="task-1",
            )


if __name__ == "__main__":
    unittest.main()
