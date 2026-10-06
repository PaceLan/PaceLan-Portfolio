import unittest

from application.external_agent import (
    ExternalAgentRequest,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.runtime_authority import RuntimeAuthority
from application.external_agent_transport import (
    ExternalAgentTransportState,
    ExternalAgentTransportStatus,
    ExternalAgentTransportUnavailableError,
)
from application.universal_agent_interface import (
    AgentOperationRequest,
    AgentRuntimeState,
    AgentRuntimeView,
    UniversalAgentInterface,
)


class _Backend:
    def __init__(self):
        self.runtime = AgentRuntimeState.IDLE
        self.calls = []

    def risk_for(self, operation):
        return "SAFE"

    def start(self, task, operations, plan, progress):
        from concurrent.futures import Future
        future = Future()
        self.calls.append(("start", task.task_id))
        self.runtime = AgentRuntimeState.RUNNING
        return future

    def pause(self):
        self.calls.append(("pause",))
        self.runtime = AgentRuntimeState.PAUSED
        return AgentRuntimeView(self.runtime, True)

    def resume(self):
        self.calls.append(("resume",))
        self.runtime = AgentRuntimeState.RUNNING
        return AgentRuntimeView(self.runtime, True)

    def stop(self):
        self.calls.append(("stop",))
        self.runtime = AgentRuntimeState.STOPPED
        return AgentRuntimeView(self.runtime, True)

    def inspect_runtime(self):
        return AgentRuntimeView(self.runtime, True)


class _Transport:
    def __init__(self, *, connected=True):
        self.connected = connected
        self.calls = []
        self.messages = []

    def status(self):
        return ExternalAgentTransportStatus(
            state=(
                ExternalAgentTransportState.CONNECTED
                if self.connected
                else ExternalAgentTransportState.DISCONNECTED
            ),
            provider="TEST",
        )

    def connect(self):
        self.calls.append(("connect",))
        return self.status()

    def disconnect(self):
        self.calls.append(("disconnect",))
        self.connected = False
        return self.status()

    def send(self, message):
        if not self.connected:
            raise ExternalAgentTransportUnavailableError("transport unavailable")
        self.calls.append(("send", message))
        self.messages.append(message)
        return "transport-response"


class TestExternalAgentGatewayC12(unittest.TestCase):

    def setUp(self):
        self.backend = _Backend()
        self.agent = UniversalAgentInterface(self.backend)
        self.runtime_authority = RuntimeAuthority()
        self.gateway = ExternalAgentGateway(
            self.agent,
            workflow_id="project-1",
            runtime_authority=self.runtime_authority,
        )

    def request(self):
        return ExternalAgentRequest(
            task_id="external-task-1",
            payload="inspect project",
            workflow_id="workflow-1",
        )

    def test_gateway_starts_disconnected(self):
        self.assertEqual(
            self.gateway.status().state,
            ExternalConnectionState.DISCONNECTED,
        )

    def test_connect_and_disconnect(self):
        self.gateway.connect()

        self.assertEqual(
            self.gateway.status().state,
            ExternalConnectionState.CONNECTED,
        )

        self.gateway.disconnect()

        self.assertEqual(
            self.gateway.status().state,
            ExternalConnectionState.DISCONNECTED,
        )

    def test_operations_require_connection(self):
        with self.assertRaises(RuntimeError):
            self.gateway.create_task(self.request())

    def test_create_and_submit_delegate_to_universal_agent(self):
        self.gateway.connect()

        created = self.gateway.create_task(self.request())
        submitted = self.gateway.submit_task(
            self.request(),
            (
                AgentOperationRequest("inspect"),
            ),
        )

        self.assertEqual(created.task.task_id, "external-task-1")
        self.assertEqual(submitted.task.task_id, "external-task-1")
        self.assertEqual(submitted.status.value, "READY")

    def test_risk_approval_is_exposed_without_bypassing_agent(self):
        self.gateway.connect()

        self.gateway.create_task(self.request())
        self.gateway.submit_task(
            self.request(),
            (AgentOperationRequest("inspect"),),
        )

        steps = self.gateway.inspect_risk_approval(self.request())

        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].risk, "SAFE")

    def test_runtime_controls_delegate(self):
        self.gateway.connect()

        self.gateway.create_task(self.request())
        self.gateway.submit_task(self.request(), ())
        self.gateway.start(self.request())
        self.gateway.pause(self.request())
        self.gateway.resume(self.request())
        self.gateway.stop(self.request())

        self.assertEqual(
            [
                ("start", "external-task-1"),
                ("pause",),
                ("resume",),
                ("stop",),
            ],
            self.backend.calls,
        )

    def test_wait_external_preserves_reason(self):
        status = self.gateway.wait_external(
            ExternalConnectionReason.QUOTA_LIMIT,
            message="external quota reached",
        )

        self.assertEqual(
            status.state,
            ExternalConnectionState.WAITING_EXTERNAL,
        )
        self.assertEqual(
            status.reason,
            ExternalConnectionReason.QUOTA_LIMIT,
        )
        self.assertTrue(status.recoverable)

    def test_response_keeps_external_correlation(self):
        request = self.request()

        response = self.gateway.make_response(
            request,
            "task accepted",
        )

        self.assertEqual(response.task_id, request.task_id)
        self.assertEqual(response.workflow_id, request.workflow_id)
        self.assertEqual(response.payload, "task accepted")


class TestExternalAgentGatewayC15Transport(unittest.TestCase):

    def setUp(self):
        backend = _Backend()
        agent = UniversalAgentInterface(backend)
        self.transport = _Transport()
        self.runtime_authority = RuntimeAuthority()
        self.gateway = ExternalAgentGateway(
            agent,
            transport=self.transport,
            runtime_authority=self.runtime_authority,
        )

    def test_connect_delegates_to_transport(self):
        status = self.gateway.connect()

        self.assertEqual(
            status.state,
            ExternalConnectionState.CONNECTED,
        )
        self.assertEqual(self.transport.calls, [("connect",)])
        self.assertEqual(
            self.gateway.transport_status().provider,
            "TEST",
        )

    def test_disconnect_delegates_to_transport(self):
        self.gateway.connect()

        status = self.gateway.disconnect()

        self.assertEqual(
            status.state,
            ExternalConnectionState.DISCONNECTED,
        )
        self.assertEqual(
            self.transport.calls,
            [("connect",), ("disconnect",)],
        )

    def test_unavailable_transport_cannot_fake_gateway_connection(self):
        transport = _Transport(connected=False)
        gateway = ExternalAgentGateway(
            UniversalAgentInterface(_Backend()),
            transport=transport,
            runtime_authority=RuntimeAuthority(),
        )

        status = gateway.connect()

        self.assertEqual(
            status.state,
            ExternalConnectionState.DISCONNECTED,
        )
        self.assertFalse(
            gateway.transport_status().available,
        )

        with self.assertRaises(RuntimeError):
            gateway.send("hello")

    def test_runtime_authority_is_required(self):
        with self.assertRaises(TypeError):
            ExternalAgentGateway(
                UniversalAgentInterface(_Backend()),
            )

    def test_send_delegates_to_connected_transport(self):
        self.gateway.connect()

        response = self.gateway.send("hello")

        self.assertEqual(response, "transport-response")
        self.assertEqual(
            self.transport.calls,
            [("connect",), ("send", "hello")],
        )


if __name__ == "__main__":
    unittest.main()
