import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from application.external_agent_bridge import ExternalAgentMessageBridge
from application.external_agent_gateway import ExternalAgentGateway
from application.external_agent_http_server import ExternalAgentHTTPServer
from application.universal_agent_interface import (
    AgentRuntimeState,
    AgentRuntimeView,
    UniversalAgentInterface,
)


class _Backend:
    def __init__(self):
        self.runtime = AgentRuntimeState.IDLE

    def risk_for(self, operation):
        return "SAFE"

    def inspect_runtime(self):
        return AgentRuntimeView(self.runtime, True)


class TestExternalAgentHTTPBridgeC16(unittest.TestCase):
    def setUp(self):
        self.agent = UniversalAgentInterface(_Backend())
        self.gateway = ExternalAgentGateway(self.agent)
        self.gateway.connect()
        self.bridge = ExternalAgentMessageBridge(self.gateway)
        self.server = ExternalAgentHTTPServer(self.bridge)
        self.server.start()

    def tearDown(self):
        self.server.shutdown()

    def _post(self, body):
        payload = json.dumps(body).encode("utf-8")
        request = Request(
            self.server.url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_real_http_request_reaches_gateway_and_uai(self):
        result = self._post({
            "command": "create_task",
            "task_id": "http-task-1",
            "payload": "inspect project",
            "workflow_id": "workflow-http-1",
        })

        self.assertEqual(result["command"], "create_task")
        self.assertEqual(result["task_id"], "http-task-1")
        self.assertEqual(result["workflow_id"], "workflow-http-1")

        task = self.agent.inspect_task("http-task-1")
        self.assertEqual(task.task.task_id, "http-task-1")

    def test_http_invalid_command_does_not_bypass_contract(self):
        with self.assertRaises(HTTPError) as context:
            self._post({
                "command": "not-a-command",
                "task_id": "http-task-2",
                "payload": "inspect project",
            })

        self.assertEqual(context.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
