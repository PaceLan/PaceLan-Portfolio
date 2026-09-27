import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.execution_readiness import ExecutionReadiness
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.risk_approval import ExecutionReadinessGate
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep


class PlannerReadinessIntegrationM1691Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)

        self.project_root = root / "project"
        self.project_root.mkdir()

        (self.project_root / "main.py").write_text(
            "from helper import run\n\nrun()\n",
            encoding="utf-8",
        )

        (self.project_root / "helper.py").write_text(
            "def run():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.project_root).scan()
        context = ProjectContextBuilder().build(scan_result)

        self.project_context_agent = ProjectContextAgentInterface(context)
        self.context_understanding = ContextUnderstanding(
            self.project_context_agent
        )
        self.planner = AgentProjectPlanner(
            self.project_context_agent
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _task(self, description: str = "inspect project") -> WorkflowTask:
        return WorkflowTask(
            task_id="task-m1691",
            project_id="project-m1691",
            description=description,
        )

    def test_context_to_plan_preserves_task_identity(self) -> None:
        task = self._task()

        understood = self.context_understanding.understand(task)
        plan = self.planner.build_from_context(
            task,
            understood,
        )

        self.assertEqual(plan.task.task_id, task.task_id)
        self.assertEqual(plan.task.project_id, task.project_id)

    def test_generated_plan_is_readiness_checked(self) -> None:
        task = self._task("inspect project")

        understood = self.context_understanding.understand(task)
        plan = self.planner.build_from_context(
            task,
            understood,
        )

        readiness = ExecutionReadiness().check(plan)

        self.assertTrue(readiness.ready)
        self.assertEqual(
            len(readiness.checked_step_ids),
            len(plan.steps),
        )

    def test_plan_steps_are_gate_ready(self) -> None:
        task = self._task("inspect project")

        understood = self.context_understanding.understand(task)
        plan = self.planner.build_from_context(
            task,
            understood,
        )

        self.assertTrue(
            ExecutionReadinessGate.is_plan_ready(plan.steps)
        )

    def test_supplied_step_preserves_action_through_planning(self) -> None:
        called = []

        def action() -> str:
            called.append(True)
            return "ok"

        task = self._task("inspect project")
        understood = self.context_understanding.understand(task)

        supplied = WorkflowStep(
            operation="inspect",
            action=action,
            target="main.py",
        )

        plan = self.planner.build_from_context(
            task,
            understood,
            steps=(supplied,),
        )

        self.assertEqual(len(plan.steps), 1)
        self.assertIs(plan.steps[0].action, action)
        self.assertEqual(called, [])

    def test_readiness_and_gate_are_non_executing(self) -> None:
        called = []

        def action() -> str:
            called.append(True)
            return "ok"

        task = self._task("inspect project")
        understood = self.context_understanding.understand(task)

        supplied = WorkflowStep(
            operation="inspect",
            action=action,
            target="main.py",
        )

        plan = self.planner.build_from_context(
            task,
            understood,
            steps=(supplied,),
        )

        readiness = ExecutionReadiness().check(plan)
        gate_ready = ExecutionReadinessGate.is_plan_ready(
            plan.steps
        )

        self.assertTrue(readiness.ready)
        self.assertTrue(gate_ready)
        self.assertEqual(called, [])

    def test_invalid_step_is_rejected_before_readiness(self) -> None:
        task = self._task("inspect project")
        understood = self.context_understanding.understand(task)

        with self.assertRaises(TypeError):
            self.planner.build_from_context(
                task,
                understood,
                steps=("not-a-workflow-step",),
            )


if __name__ == "__main__":
    unittest.main()