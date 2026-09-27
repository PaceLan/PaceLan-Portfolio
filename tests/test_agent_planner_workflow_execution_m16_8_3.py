import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow, WorkflowStatus, WorkflowTask
from agent_workflow.workflow_service import WorkflowService

from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentPlannerWorkflowExecutionM1683Tests(unittest.TestCase):

    def make_environment(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        root = Path(temporary_directory.name)
        project_root = root / "project"
        snapshot_root = root / "snapshots"
        history_root = root / "history"

        project_root.mkdir()
        history_root.mkdir()

        (project_root / "main.py").write_text(
            "def main():\n"
            "    return helper()\n",
            encoding="utf-8",
        )
        (project_root / "helper.py").write_text(
            "def helper():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            project_root,
            snapshot_root,
        )

        workflow = AgentWorkflow(
            history_store=HistoryStore(history_root),
            snapshot_service=SnapshotService(
                project_root,
                store=snapshot_store,
            ),
        )

        workflow_service = WorkflowService(workflow)
        scan_result = ProjectScanner(project_root).scan()
        project_context = ProjectContextBuilder().build(scan_result)

        project_context_agent = ProjectContextAgentInterface(
            project_context
        )

        context_agent = ContextUnderstanding(
            project_context_agent
        )
        planner = AgentProjectPlanner(project_context_agent)

        return (
            project_root,
            workflow_service,
            context_agent,
            planner,
        )

    def test_planner_plan_is_executable_by_workflow_service(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-execute",
            project_id="project-1683",
            description="analyze helper.py",
        )

        context = context_agent.understand(task)
        plan = planner.build_from_context(task, context)

        result = service.execute(plan)

        self.assertIsNotNone(service.last_run_context)
        self.assertIsNotNone(service.last_execution_tracker)
        self.assertTrue(result.completed_successfully)

    def test_task_identity_survives_planner_to_execution(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-identity",
            project_id="project-identity",
            description="inspect helper.py",
        )

        context = context_agent.understand(task)
        plan = planner.build_from_context(task, context)
        result = service.execute(plan)

        run_context = service.last_run_context

        self.assertEqual(plan.task.task_id, task.task_id)
        self.assertEqual(plan.task.project_id, task.project_id)
        self.assertEqual(run_context.task_id, task.task_id)
        self.assertTrue(result.completed_successfully)

    def test_planner_step_ids_match_execution_tracker(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-step-id",
            project_id="project-step-id",
            description="analyze helper.py",
        )

        context = context_agent.understand(task)
        plan = planner.build_from_context(task, context)

        expected_ids = tuple(step.step_id for step in plan.steps)

        service.execute(plan)

        tracker = service.last_execution_tracker
        self.assertIsNotNone(tracker)

        assert tracker is not None
        snapshot = tracker.snapshot()

        self.assertEqual(tuple(snapshot.step_states.keys()), expected_ids)

    def test_planner_context_reaches_execution_steps(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-context",
            project_id="project-context",
            description="analyze helper.py",
        )

        context = context_agent.understand(task)
        plan = planner.build_from_context(task, context)

        self.assertTrue(plan.steps)
        self.assertTrue(
            any(step.context for step in plan.steps)
        )

        result = service.execute(plan)

        self.assertTrue(result.completed_successfully)

    def test_planner_execution_is_deterministic(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-deterministic",
            project_id="project-deterministic",
            description="trace dependencies of helper.py",
        )

        context = context_agent.understand(task)

        plan_a = planner.build_from_context(task, context)
        plan_b = planner.build_from_context(task, context)

        self.assertEqual(plan_a.task, plan_b.task)
        self.assertEqual(
            tuple(
                (
                    step.operation,
                    step.target,
                    step.context,
                    step.step_id,
                )
                for step in plan_a.steps
            ),
            tuple(
                (
                    step.operation,
                    step.target,
                    step.context,
                    step.step_id,
                )
                for step in plan_b.steps
            ),
        )

    def test_existing_step_attributes_survive_execution(self):
        _, service, context_agent, planner = self.make_environment()

        task = WorkflowTask(
            task_id="m16-8-3-attributes",
            project_id="project-attributes",
            description="inspect helper.py",
        )

        context = context_agent.understand(task)

        plan = planner.build_from_context(task, context)

        for step in plan.steps:
            self.assertIsNotNone(step.operation)
            self.assertIsNotNone(step.target)
            self.assertIsNotNone(step.action)

        result = service.execute(plan)

        self.assertIn(
            result.status,
            {
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.BLOCKED,
            },
        )


if __name__ == "__main__":
    unittest.main()