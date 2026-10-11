import unittest

from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from application.autonomous_plan_binding import AutonomousPlanBindingService
from application.models import PlanModel


class AutonomousPlanBindingServiceTests(unittest.TestCase):
    def test_binds_and_retrieves_executable_plan(self):
        plan = PlanModel(
            task_id="task-c6-4",
            project_id="project-c6-4",
        )
        workflow_plan = WorkflowPlan(
            task=WorkflowTask(
                task_id="task-c6-4",
                description="execute",
                project_id="project-c6-4",
            ),
            steps=(
                WorkflowStep(
                    operation="verify",
                    action=lambda: "ok",
                    step_id="step-1",
                ),
            ),
        )

        service = AutonomousPlanBindingService()
        self.assertIs(service.bind(plan, workflow_plan), plan)
        self.assertIs(service.get("task-c6-4"), workflow_plan)

    def test_rejects_task_mismatch(self):
        plan = PlanModel(
            task_id="task-a",
            project_id="project-c6-4",
        )
        workflow_plan = WorkflowPlan(
            task=WorkflowTask(
                task_id="task-b",
                description="execute",
                project_id="project-c6-4",
            ),
        )

        with self.assertRaises(ValueError):
            AutonomousPlanBindingService().bind(plan, workflow_plan)

    def test_rejects_project_mismatch(self):
        plan = PlanModel(
            task_id="task-c6-4",
            project_id="project-a",
        )
        workflow_plan = WorkflowPlan(
            task=WorkflowTask(
                task_id="task-c6-4",
                description="execute",
                project_id="project-b",
            ),
        )

        with self.assertRaises(ValueError):
            AutonomousPlanBindingService().bind(plan, workflow_plan)

    def test_missing_binding_is_rejected(self):
        with self.assertRaises(KeyError):
            AutonomousPlanBindingService().get("missing")


if __name__ == "__main__":
    unittest.main()
