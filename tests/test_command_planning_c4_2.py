import unittest
from dataclasses import FrozenInstanceError

from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from application.command_planning import Command, CommandPlan, CommandPlanner


class CommandPlanningC42Tests(unittest.TestCase):
    def setUp(self):
        self.task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="inspect helper.py",
        )
        self.plan = WorkflowPlan(
            task=self.task,
            steps=(
                WorkflowStep(
                    operation="inspect",
                    action=lambda: None,
                    target="helper.py",
                    context="inspect-context",
                    step_id="step-001",
                ),
            ),
        )
        self.planner = CommandPlanner()

    def test_maps_workflow_step_to_command(self):
        result = self.planner.plan(self.plan)

        self.assertIsInstance(result, CommandPlan)
        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(len(result.commands), 1)

        command = result.commands[0]
        self.assertEqual(command.task_id, "task-001")
        self.assertEqual(command.project_id, "project-001")
        self.assertEqual(command.step_id, "step-001")
        self.assertEqual(command.operation, "inspect")
        self.assertEqual(command.target, "helper.py")
        self.assertEqual(command.context, "inspect-context")

    def test_command_contains_no_callable(self):
        command = self.planner.plan(self.plan).commands[0]
        self.assertFalse(any(callable(value) for value in vars(command).values()))

    def test_models_are_immutable(self):
        command = self.planner.plan(self.plan).commands[0]
        with self.assertRaises(FrozenInstanceError):
            command.operation = "analyze"

    def test_invalid_plan_is_rejected(self):
        with self.assertRaises(TypeError):
            self.planner.plan(object())

    def test_command_order_matches_workflow_order(self):
        plan = WorkflowPlan(
            task=self.task,
            steps=(
                WorkflowStep("inspect", lambda: None, step_id="step-001"),
                WorkflowStep("analyze", lambda: None, step_id="step-002"),
            ),
        )

        commands = self.planner.plan(plan).commands

        self.assertEqual(
            [command.step_id for command in commands],
            ["step-001", "step-002"],
        )


    def test_empty_plan_produces_empty_command_plan(self):
        plan = WorkflowPlan(task=self.task)
        result = self.planner.plan(plan)

        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(result.commands, ())

    def test_default_target_and_context_are_preserved(self):
        plan = WorkflowPlan(
            task=self.task,
            steps=(
                WorkflowStep(
                    operation="inspect",
                    action=lambda: None,
                    step_id="step-001",
                ),
            ),
        )

        command = self.planner.plan(plan).commands[0]

        self.assertEqual(command.target, ".")
        self.assertIsNone(command.context)
if __name__ == "__main__":
    unittest.main()

