import unittest
from dataclasses import MISSING, fields, is_dataclass

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


def make_workflow_task() -> WorkflowTask:
    """Build a minimal WorkflowTask without assuming optional field ordering."""
    if not is_dataclass(WorkflowTask):
        raise TypeError("WorkflowTask must remain a dataclass")

    values = {}

    for field in fields(WorkflowTask):
        if field.default is not MISSING:
            continue

        if field.default_factory is not MISSING:
            continue

        name = field.name

        if name == "task_id":
            values[name] = "task-m17-4-001"
        elif name == "project_id":
            values[name] = "project-m17-4-001"
        elif name in {"name", "title"}:
            values[name] = "M17.4 integrity task"
        elif name in {"description", "prompt", "instruction", "content"}:
            values[name] = "Verify planner and ordering integrity"
        elif name == "intent":
            values[name] = "verify"
        elif name == "context":
            values[name] = None
        elif field.type is str:
            values[name] = ""
        elif field.type is bool:
            values[name] = False
        elif field.type is int:
            values[name] = 0
        else:
            raise TypeError(
                f"Unsupported required WorkflowTask field: {name}"
            )

    return WorkflowTask(**values)


class PlannerOrderingIntegrityM174Tests(unittest.TestCase):
    def setUp(self):
        self.task = make_workflow_task()

    @staticmethod
    def action_a():
        return "A"

    @staticmethod
    def action_b():
        return "B"

    def test_planner_enrich_step_preserves_all_step_fields(self):
        source = WorkflowStep(
            operation="inspect",
            action=self.action_a,
            risk=RiskLevel.SAFE,
            approval=ApprovalStatus.NOT_REQUESTED,
            target="src/main.py",
            context="existing-context",
            step_id="step-007",
        )

        enriched = AgentProjectPlanner._enrich_step(
            source,
            "project_root=.; total_files=3; python_files=2",
        )

        self.assertIsInstance(enriched, WorkflowStep)
        self.assertEqual(enriched.operation, source.operation)
        self.assertIs(enriched.action, source.action)
        self.assertEqual(enriched.risk, source.risk)
        self.assertEqual(enriched.approval, source.approval)
        self.assertEqual(enriched.target, source.target)
        self.assertEqual(
            enriched.context,
            "existing-context; "
            "project_root=.; total_files=3; python_files=2",
        )
        self.assertEqual(enriched.step_id, source.step_id)

    def test_planner_enrich_step_injects_project_context_when_empty(self):
        source = WorkflowStep(
            operation="inspect",
            action=self.action_a,
            context=None,
            step_id="step-001",
        )

        enriched = AgentProjectPlanner._enrich_step(
            source,
            "project_root=.; total_files=3; python_files=2",
        )

        self.assertEqual(
            enriched.context,
            "project_root=.; total_files=3; python_files=2",
        )

    def test_planner_enrich_step_does_not_execute_action(self):
        calls = []

        def action():
            calls.append("executed")
            return "done"

        source = WorkflowStep(
            operation="inspect",
            action=action,
            step_id="step-001",
        )

        enriched = AgentProjectPlanner._enrich_step(
            source,
            "project_root=.; total_files=1; python_files=1",
        )

        self.assertIs(enriched.action, action)
        self.assertEqual(calls, [])

    def test_planner_enrich_step_rejects_invalid_step(self):
        with self.assertRaises(TypeError):
            AgentProjectPlanner._enrich_step(
                "not-a-workflow-step",
                "project_root=.; total_files=0; python_files=0",
            )

    def test_ordering_preserves_task_identity(self):
        step_b = WorkflowStep(
            operation="B",
            action=self.action_b,
            step_id="step-b",
        )
        step_a = WorkflowStep(
            operation="A",
            action=self.action_a,
            step_id="step-a",
        )

        plan = WorkflowPlan(
            task=self.task,
            steps=(step_b, step_a),
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
                "step-a": (),
            },
        )

        self.assertIsNot(ordered, plan)
        self.assertIs(ordered.task, plan.task)

    def test_ordering_preserves_step_identity(self):
        step_b = WorkflowStep(
            operation="B",
            action=self.action_b,
            step_id="step-b",
        )
        step_a = WorkflowStep(
            operation="A",
            action=self.action_a,
            step_id="step-a",
        )

        plan = WorkflowPlan(
            task=self.task,
            steps=(step_b, step_a),
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
                "step-a": (),
            },
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-a", "step-b"),
        )

        self.assertIs(ordered.steps[0], step_a)
        self.assertIs(ordered.steps[1], step_b)

    def test_ordering_does_not_mutate_original_plan(self):
        step_b = WorkflowStep(
            operation="B",
            action=self.action_b,
            step_id="step-b",
        )
        step_a = WorkflowStep(
            operation="A",
            action=self.action_a,
            step_id="step-a",
        )

        original_steps = (step_b, step_a)
        plan = WorkflowPlan(
            task=self.task,
            steps=original_steps,
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
                "step-a": (),
            },
        )

        self.assertEqual(plan.steps, original_steps)
        self.assertIs(plan.steps[0], step_b)
        self.assertIs(plan.steps[1], step_a)
        self.assertNotEqual(
            tuple(step.step_id for step in plan.steps),
            tuple(step.step_id for step in ordered.steps),
        )

    def test_ordering_does_not_execute_actions(self):
        calls = []

        def action_a():
            calls.append("A")
            return "A"

        def action_b():
            calls.append("B")
            return "B"

        step_b = WorkflowStep(
            operation="B",
            action=action_b,
            step_id="step-b",
        )
        step_a = WorkflowStep(
            operation="A",
            action=action_a,
            step_id="step-a",
        )

        plan = WorkflowPlan(
            task=self.task,
            steps=(step_b, step_a),
        )

        ExecutionOrdering().order(
            plan,
            {
                "step-a": (),
                "step-b": ("step-a",),
            },
        )

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()