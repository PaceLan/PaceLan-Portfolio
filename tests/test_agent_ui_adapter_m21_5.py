
import unittest

from ui.agent_state import (
    AgentInteractionState,
    AgentUnderstandingState,
)
from ui.agent_adapter import AgentUIAdapter


class M215AgentUIAdapterTests(unittest.TestCase):
    def test_adapter_exists(self):
        self.assertTrue(hasattr(AgentUIAdapter, "from_execution"))

    def test_none_execution_returns_default_state(self):
        state = AgentUIAdapter.from_execution(None)

        self.assertIsInstance(state, AgentInteractionState)
        self.assertEqual(state.task.title, "No task")
        self.assertEqual(
            state.understanding.summary,
            "No understanding available",
        )

    def test_adapter_preserves_understanding_data(self):
        class FakeExecution:
            class Task:
                title = "Authentication"
                description = "Inspect authentication flow"

            task = Task()

            class Understanding:
                summary = "Task auth-001: 2 relevant files, 2 relevant symbols, 1 relationships, 1 dependencies."
                structured_summary = "STRUCTURED SHOULD NOT BE DISPLAYED"
                relevant_files = ("src/auth.py", "src/session.py")
                relevant_symbols = ("AuthService", "Session")
                relationships = ("auth.py -> session.py",)
                dependencies = ("src/session.py",)

            context_understanding = Understanding()

            class Plan:
                summary = "Authentication plan"
                status = "Ready"
                steps = ("Inspect auth", "Inspect session")

            plan = Plan()

            class Result:
                summary = "Completed"
                status = "Success"

            result = Result()

        state = AgentUIAdapter.from_execution(FakeExecution())

        self.assertEqual(state.task.title, "Authentication")
        self.assertEqual(
            state.task.description,
            "Inspect authentication flow",
        )
        self.assertIsInstance(
            state.understanding,
            AgentUnderstandingState,
        )
        self.assertEqual(
            state.understanding.summary,
            "Task auth-001: 2 relevant files, 2 relevant symbols, 1 relationships, 1 dependencies.",
        )
        self.assertEqual(
            state.understanding.relevant_files,
            ("src/auth.py", "src/session.py"),
        )
        self.assertEqual(
            state.understanding.relevant_symbols,
            ("AuthService", "Session"),
        )
        self.assertEqual(
            state.understanding.relationships,
            ("auth.py -> session.py",),
        )
        self.assertEqual(
            state.understanding.dependencies,
            ("src/session.py",),
        )


if __name__ == "__main__":
    unittest.main()
