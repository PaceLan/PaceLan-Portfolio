from application.runtime_authority import RuntimeAuthority

import unittest



from application.draft_input_authority import DraftInputAuthority

from application.external_agent import ExternalAgentRequest

from application.external_agent_bridge import (

    ExternalAgentCommand,

    ExternalAgentMessageBridge,

)

from application.external_agent_gateway import ExternalAgentGateway

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





class ExternalBridgeDraftBoundaryC393Tests(unittest.TestCase):

    def setUp(self):

        self.agent = UniversalAgentInterface(_Backend())

        self.runtime_authority = RuntimeAuthority()

        self.gateway = ExternalAgentGateway(

            self.agent,

            runtime_authority=self.runtime_authority,

        )

        self.gateway.connect()

        self.bridge = ExternalAgentMessageBridge(self.gateway)



    def test_create_task_enters_as_created(self):

        request = ExternalAgentRequest(

            task_id="bridge-draft-1",

            payload="  inspect project  ",

        )



        result = self.bridge.dispatch(

            request,

            ExternalAgentCommand.CREATE_TASK,

        )



        self.assertEqual(result.value.status.value, "CREATED")

        self.assertEqual(

            result.value.task.description,

            "inspect project",

        )



    def test_bridge_does_not_turn_draft_into_execution(self):

        request = ExternalAgentRequest(

            task_id="bridge-draft-2",

            payload="implement feature",

        )



        result = self.bridge.dispatch(

            request,

            ExternalAgentCommand.CREATE_TASK,

        )



        self.assertFalse(

            DraftInputAuthority.can_enter_formal_execution(

                DraftInputAuthority().accept(result.value.task.description)

            )

        )





if __name__ == "__main__":

    unittest.main()

