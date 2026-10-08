from application.runtime_authority import RuntimeAuthority

import unittest



from application.external_agent_bridge import ExternalAgentMessageBridge

from application.external_agent_gateway import ExternalAgentGateway

from application.external_agent_http_server import ExternalAgentHTTPServer

from application.universal_agent_interface import UniversalAgentInterface

from application.vscode_integration import VSCodeIntegration





class _Backend:

    def risk_for(self, operation):

        return "SAFE"



    def inspect_runtime(self):

        from application.universal_agent_interface import (

            AgentRuntimeState,

            AgentRuntimeView,

        )

        return AgentRuntimeView(AgentRuntimeState.IDLE, True)





class TestVSCodeIntegrationC21(unittest.TestCase):

    def setUp(self):

        self.agent = UniversalAgentInterface(_Backend())

        self.runtime_authority = RuntimeAuthority()

        gateway = ExternalAgentGateway(

            self.agent,

            runtime_authority=self.runtime_authority,

        )

        gateway.connect()



        bridge = ExternalAgentMessageBridge(gateway)

        self.server = ExternalAgentHTTPServer(bridge)

        self.server.start()



        self.integration = VSCodeIntegration(endpoint=self.server.url)



    def tearDown(self):

        self.server.shutdown()



    def test_workspace_lifecycle_is_local_and_explicit(self):

        opened = self.integration.workspace_opened(r"C:\workspace")



        self.assertEqual(opened.root, r"C:\workspace")

        self.assertEqual(self.integration.workspace.root, r"C:\workspace")



        closed = self.integration.workspace_closed()



        self.assertIsNone(closed.root)



    def test_command_reaches_c1_http_boundary(self):

        result = self.integration.send(

            command="create_task",

            task_id="vscode-task-1",

            payload="inspect project",

            workflow_id="vscode-workflow-1",

        )



        self.assertEqual(result.command, "create_task")

        self.assertEqual(result.task_id, "vscode-task-1")

        self.assertEqual(result.workflow_id, "vscode-workflow-1")



        task = self.agent.inspect_task("vscode-task-1")

        self.assertEqual(task.task.task_id, "vscode-task-1")



    def test_invalid_command_is_reported_without_bypass(self):

        with self.assertRaises(RuntimeError):

            self.integration.send(

                command="not-a-command",

                task_id="vscode-task-2",

                payload="inspect project",

            )





if __name__ == "__main__":

    unittest.main()

