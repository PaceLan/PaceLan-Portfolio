import unittest

from application.external_agent import ExternalAgentRequest
from application.external_agent_bridge import (
    ExternalAgentCommand,
    ExternalAgentMessageBridge,
)
from application.external_agent_gateway import ExternalAgentGateway
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


class TestExternalAgentMessageBridgeC16(unittest.TestCase):
    def setUp(self):
        self.backend = _Backend()
        self.agent = UniversalAgentInterface(self.backend)
        self.gateway = ExternalAgentGateway(
            self.agent,
            workflow_id="project-1",
        )
        self.bridge = ExternalAgentMessageBridge(self.gateway)
        self.request = ExternalAgentRequest(
            task_id="external-task-1",
            payload="inspect project",
            workflow_id="workflow-1",
        )
        self.gateway.connect()

    def test_create_task_delegates_to_gateway(self):
        result = self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.CREATE_TASK,
        )
        self.assertEqual(result.command, ExternalAgentCommand.CREATE_TASK)
        self.assertEqual(result.value.task.task_id, self.request.task_id)
        self.assertEqual(result.response.task_id, self.request.task_id)

    def test_submit_task_delegates_existing_task(self):
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.CREATE_TASK,
        )
        result = self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.SUBMIT_TASK,
            operations=(AgentOperationRequest("inspect"),),
        )
        self.assertEqual(result.value.task.task_id, self.request.task_id)
        self.assertEqual(result.value.status.value, "READY")

    def test_runtime_commands_use_same_gateway(self):
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.CREATE_TASK,
        )
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.SUBMIT_TASK,
        )
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.START,
        )
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.PAUSE,
        )
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.RESUME,
        )
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.STOP,
        )

        self.assertEqual(
            self.backend.calls,
            [
                ("start", self.request.task_id),
                ("pause",),
                ("resume",),
                ("stop",),
            ],
        )

    def test_inspect_and_result_preserve_correlation(self):
        self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.CREATE_TASK,
        )

        inspected = self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.INSPECT_TASK,
        )
        result = self.bridge.dispatch(
            self.request,
            ExternalAgentCommand.RESULT,
        )

        self.assertEqual(
            inspected.response.task_id,
            self.request.task_id,
        )
        self.assertIsNone(result.value)
        self.assertEqual(
            result.response.workflow_id,
            self.request.workflow_id,
        )

    def test_bridge_does_not_bypass_gateway(self):
        self.gateway.disconnect()

        with self.assertRaises(RuntimeError):
            self.bridge.dispatch(
                self.request,
                ExternalAgentCommand.CREATE_TASK,
            )

    def test_invalid_contract_types_are_rejected(self):
        with self.assertRaises(TypeError):
            self.bridge.dispatch(
                self.request,
                "start",
            )

        with self.assertRaises(TypeError):
            self.bridge.dispatch(
                "not-a-request",
                ExternalAgentCommand.START,
            )


if __name__ == "__main__":
    unittest.main()
