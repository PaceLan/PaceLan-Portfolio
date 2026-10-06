from application.runtime_authority import RuntimeAuthority

import json

import unittest

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

    def risk_for(self, operation):

        return "SAFE"



    def inspect_runtime(self):

        return AgentRuntimeView(AgentRuntimeState.IDLE, True)





class ExternalHTTPDraftBoundaryC394Tests(unittest.TestCase):

    def setUp(self):

        self.agent = UniversalAgentInterface(_Backend())

        self.runtime_authority = RuntimeAuthority()

        self.gateway = ExternalAgentGateway(

            self.agent,

            runtime_authority=self.runtime_authority,

        )

        self.gateway.connect()

        self.bridge = ExternalAgentMessageBridge(self.gateway)

        self.server = ExternalAgentHTTPServer(self.bridge)

        self.server.start()



    def tearDown(self):

        self.server.shutdown()



    def test_http_create_task_remains_created(self):

        body = json.dumps({

            "command": "create_task",

            "task_id": "http-draft-1",

            "payload": "  implement feature  ",

        }).encode("utf-8")



        request = Request(

            self.server.url,

            data=body,

            method="POST",

            headers={"Content-Type": "application/json"},

        )



        with urlopen(request, timeout=3) as response:

            result = json.loads(

                response.read().decode("utf-8")

            )



        self.assertEqual(result["command"], "create_task")



        task = self.agent.inspect_task("http-draft-1")

        self.assertEqual(task.status.value, "CREATED")



    def test_http_create_does_not_start_task(self):

        body = json.dumps({

            "command": "create_task",

            "task_id": "http-draft-2",

            "payload": "run implementation",

        }).encode("utf-8")



        request = Request(

            self.server.url,

            data=body,

            method="POST",

            headers={"Content-Type": "application/json"},

        )



        with urlopen(request, timeout=3):

            pass



        runtime = self.agent.inspect_runtime()

        self.assertEqual(runtime.state, AgentRuntimeState.IDLE)





if __name__ == "__main__":

    unittest.main()

