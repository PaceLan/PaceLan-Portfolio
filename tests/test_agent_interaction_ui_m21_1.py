import unittest

from ui.agent_state import (
    AgentExecutionState,
    AgentInteractionState,
    AgentPlanState,
    AgentResultState,
    AgentTaskState,
)


class M211AgentStateTests(unittest.TestCase):

    def test_default_agent_state_is_idle(self):
        state = AgentInteractionState()

        self.assertEqual(state.task.status, "No task")
        self.assertEqual(state.plan.status, "No plan")
        self.assertEqual(state.execution.status, "Idle")
        self.assertEqual(state.result.status, "No result")

    def test_task_state_is_immutable(self):
        state = AgentTaskState()

        with self.assertRaises(Exception):
            state.status = "Running"

    def test_plan_state_is_immutable(self):
        state = AgentPlanState()

        with self.assertRaises(Exception):
            state.status = "Ready"

    def test_execution_state_is_immutable(self):
        state = AgentExecutionState()

        with self.assertRaises(Exception):
            state.status = "Running"

    def test_result_state_is_immutable(self):
        state = AgentResultState()

        with self.assertRaises(Exception):
            state.status = "Success"

    def test_agent_state_is_composed_of_four_sections(self):
        state = AgentInteractionState()

        self.assertIsInstance(state.task, AgentTaskState)
        self.assertIsInstance(state.plan, AgentPlanState)
        self.assertIsInstance(state.execution, AgentExecutionState)
        self.assertIsInstance(state.result, AgentResultState)


if __name__ == "__main__":
    unittest.main()
