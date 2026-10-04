import unittest

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentResponse,
    ExternalAgentStatus,
    ExternalConnectionReason,
    ExternalConnectionState,
)


class TestExternalAgentBoundaryC1_1(unittest.TestCase):

    def test_connected_status(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.CONNECTED,
        )

        self.assertEqual(status.state, ExternalConnectionState.CONNECTED)
        self.assertFalse(status.recoverable)

    def test_waiting_external_requires_reason(self):
        with self.assertRaises(ValueError):
            ExternalAgentStatus(
                state=ExternalConnectionState.WAITING_EXTERNAL,
            )

    def test_safety_check_is_waiting_external(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=ExternalConnectionReason.SAFETY_CHECK,
            recoverable=True,
        )

        self.assertEqual(
            status.reason,
            ExternalConnectionReason.SAFETY_CHECK,
        )
        self.assertTrue(status.recoverable)

    def test_quota_limit_is_waiting_external(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=ExternalConnectionReason.QUOTA_LIMIT,
            recoverable=True,
        )

        self.assertEqual(
            status.reason,
            ExternalConnectionReason.QUOTA_LIMIT,
        )
        self.assertTrue(status.recoverable)

    def test_connection_lost_is_waiting_external_when_recoverable(self):
        status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=ExternalConnectionReason.CONNECTION_LOST,
            recoverable=True,
        )

        self.assertEqual(
            status.reason,
            ExternalConnectionReason.CONNECTION_LOST,
        )
        self.assertTrue(status.recoverable)

    def test_recoverable_state_requires_flag(self):
        with self.assertRaises(ValueError):
            ExternalAgentStatus(
                state=ExternalConnectionState.RECOVERABLE,
            )

    def test_non_recoverable_state_cannot_be_marked_recoverable(self):
        with self.assertRaises(ValueError):
            ExternalAgentStatus(
                state=ExternalConnectionState.FAILED,
                recoverable=True,
            )

    def test_request_is_transport_neutral(self):
        request = ExternalAgentRequest(
            task_id="task-1",
            payload="continue",
            workflow_id="workflow-1",
        )

        self.assertEqual(request.task_id, "task-1")
        self.assertEqual(request.payload, "continue")
        self.assertEqual(request.workflow_id, "workflow-1")

    def test_response_is_transport_neutral(self):
        response = ExternalAgentResponse(
            task_id="task-1",
            payload="continue",
            workflow_id="workflow-1",
        )

        self.assertEqual(response.task_id, "task-1")
        self.assertEqual(response.payload, "continue")
        self.assertEqual(response.workflow_id, "workflow-1")


if __name__ == "__main__":
    unittest.main()
