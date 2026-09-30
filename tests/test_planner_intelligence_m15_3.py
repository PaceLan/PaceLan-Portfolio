import tempfile
import unittest
from pathlib import Path

from agent_workflow.context_understanding import (
    ContextUnderstanding,
    ContextUnderstandingResult,
)
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep


class PlannerIntelligenceM153Tests(unittest.TestCase):

    def _build_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            (root / 'main.py').write_text(
                'import helper\n\n'
                'def main():\n'
                '    return helper.value()\n',
                encoding='utf-8',
            )
            (root / 'helper.py').write_text(
                'def value():\n'
                '    return 42\n',
                encoding='utf-8',
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)
            interface = ProjectContextAgentInterface(context)
            understanding = ContextUnderstanding(interface)

            return understanding.understand(
                WorkflowTask(
                    task_id='task-m153',
                    project_id='project-m153',
                    description='analyze helper.py',
                )
            )

    def _task(self, description):
        return WorkflowTask(
            task_id='task-m153',
            project_id='project-m153',
            description=description,
        )

    def _planner(self):
        return PlannerIntelligence()

    def test_inspect_intent_generates_only_inspect(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('inspect helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect'],
        )

    def test_analyze_intent_generates_inspect_then_analyze(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('analyze helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect', 'analyze', 'analyze'],
        )

    def test_trace_intent_generates_inspect_then_trace(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('trace dependencies of helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect', 'trace_dependencies'],
        )

    def test_understand_intent_generates_context_step(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('understand helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect', 'analyze', 'analyze'],
        )

    def test_mixed_intent_generates_ordered_operations(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('analyze helper.py and trace its dependencies'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect', 'analyze', 'analyze', 'trace_dependencies'],
        )

    def test_task_description_changes_planning_strategy(self):
        context = self._build_context()
        planner = self._planner()

        inspect_plan = planner.plan(
            self._task('inspect helper.py'),
            context,
        )
        analyze_plan = planner.plan(
            self._task('analyze helper.py'),
            context,
        )

        self.assertNotEqual(
            [step.operation for step in inspect_plan.steps],
            [step.operation for step in analyze_plan.steps],
        )

    def test_intent_does_not_change_target_selection(self):
        context = self._build_context()
        planner = self._planner()

        inspect_plan = planner.plan(
            self._task('inspect helper.py'),
            context,
        )
        analyze_plan = planner.plan(
            self._task('analyze helper.py'),
            context,
        )

        inspect_targets = [step.target for step in inspect_plan.steps]
        analyze_targets = [step.target for step in analyze_plan.steps]

        self.assertIn('helper.py', inspect_targets)
        self.assertIn('helper.py', analyze_targets)

    def test_step_ids_are_stable(self):
        context = self._build_context()
        planner = self._planner()

        first = planner.plan(
            self._task('analyze helper.py'),
            context,
        )
        second = planner.plan(
            self._task('analyze helper.py'),
            context,
        )

        self.assertEqual(
            [step.step_id for step in first.steps],
            [step.step_id for step in second.steps],
        )

    def test_step_ids_are_sequential(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('analyze helper.py and trace dependencies'),
            context,
        )

        self.assertEqual(
            [step.step_id for step in plan.steps],
            ['step-001', 'step-002', 'step-003', 'step-004'],
        )

    def test_actions_are_never_executed(self):
        context = self._build_context()

        executed = []

        def action():
            executed.append(True)
            return 'executed'

        step = WorkflowStep(
            operation='inspect',
            action=action,
            target='helper.py',
            step_id='action-001',
        )

        plan = self._planner().plan(
            self._task('analyze helper.py'),
            context,
            actions=(step,),
        )

        self.assertIsNotNone(plan)
        self.assertEqual(step.operation, 'inspect')
        self.assertEqual(step.target, 'helper.py')
        self.assertEqual(executed, [])

    def test_empty_context_remains_safe(self):
        planner = self._planner()
        task = self._task('analyze helper.py')

        empty = ContextUnderstandingResult(
            task=task,
            relevant_files=(),
            relevant_symbols=(),
            relationships=(),
            dependencies=(),
            summary='',
        )

        plan = planner.plan(
            task,
            empty,
        )

        self.assertIsNotNone(plan)
        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect', 'analyze'],
        )

    def test_unknown_task_defaults_to_inspect(self):
        context = self._build_context()

        plan = self._planner().plan(
            self._task('hello helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in plan.steps],
            ['inspect'],
        )

    def test_understand_is_distinct_from_inspect(self):
        context = self._build_context()
        planner = self._planner()

        inspect_plan = planner.plan(
            self._task('inspect helper.py'),
            context,
        )
        understand_plan = planner.plan(
            self._task('understand helper.py'),
            context,
        )

        self.assertEqual(
            [step.operation for step in inspect_plan.steps],
            ['inspect'],
        )
        self.assertEqual(
            [step.operation for step in understand_plan.steps],
            ['inspect', 'analyze', 'analyze'],
        )


if __name__ == '__main__':
    unittest.main()
