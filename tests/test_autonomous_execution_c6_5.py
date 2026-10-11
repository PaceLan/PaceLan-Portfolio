import unittest

from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from application.autonomous_execution import AutonomousExecutionService
from application.autonomous_plan_binding import AutonomousPlanBindingService
from application.models import PlanModel
from application.services import ApplicationExecutionService
from application.task_management import ProductTask


class RecordingExecutionService(ApplicationExecutionService):
    def run(self, task, steps=()):
        self.received_task = task
        self.received_steps = tuple(steps)
        return "run-result"

    def start(self, task, steps=()):
        self.received_task = task
        self.received_steps = tuple(steps)
        return "start-result"


class AutonomousExecutionServiceTests(unittest.TestCase):
    def setUp(self):
        self.task = ProductTask(
            task_id="task-c6-5",
            project_id="project-c6-5",
            title="C6.5 execution",
            description="execute task",
        )
        self.plan = PlanModel(
            task_id="task-c6-5",
            project_id="project-c6-5",
        )
        self.steps = (
            WorkflowStep(
                operation="verify",
                action=lambda: "ok",
                step_id="step-1",
            ),
            WorkflowStep(
                operation="finish",
                action=lambda: "done",
                step_id="step-2",
            ),
        )
        self.workflow_plan = WorkflowPlan(
            task=WorkflowTask(
                task_id="task-c6-5",
                description="execute task",
                project_id="project-c6-5",
            ),
            steps=self.steps,
        )
        self.binding = AutonomousPlanBindingService()
        self.binding.bind(self.plan, self.workflow_plan)
        self.execution = RecordingExecutionService.__new__(
            RecordingExecutionService
        )
        self.service = AutonomousExecutionService(
            self.execution,
            self.binding,
        )

    def test_run_uses_bound_workflow_steps(self):
        result = self.service.run(self.task, self.plan)

        self.assertEqual(result, "run-result")
        self.assertEqual(self.execution.received_steps, self.steps)

    def test_start_uses_bound_workflow_steps(self):
        result = self.service.start(self.task, self.plan)

        self.assertEqual(result, "start-result")
        self.assertEqual(self.execution.received_steps, self.steps)

    def test_missing_binding_is_rejected(self):
        binding = AutonomousPlanBindingService()
        service = AutonomousExecutionService(
            self.execution,
            binding,
        )

        with self.assertRaises(KeyError):
            service.run(self.task, self.plan)

    def test_task_and_plan_mismatch_is_rejected(self):
        other_task = ProductTask(
            task_id="task-other",
            project_id="project-c6-5",
            title="Other task",
            description="execute task",
        )

        with self.assertRaises(ValueError):
            self.service.run(other_task, self.plan)


    def test_modified_plan_with_same_identity_is_rejected(self):
        altered_plan = PlanModel(
            task_id=self.plan.task_id,
            project_id=self.plan.project_id,
            ready=True,
        )
        with self.assertRaises(ValueError):
            self.service.run(self.task, altered_plan)



if __name__ == "__main__":
    unittest.main()
