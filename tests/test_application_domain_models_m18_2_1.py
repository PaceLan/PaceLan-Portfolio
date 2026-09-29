import unittest
from dataclasses import FrozenInstanceError

from application.models import (
    ExecutionModel,
    PlanModel,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)


class ApplicationDomainModelsM1821Tests(unittest.TestCase):

    def test_project_model(self):
        model = ProjectModel("project-001")
        self.assertEqual(model.project_id, "project-001")

    def test_task_model(self):
        model = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="Build feature",
            context="Application layer",
        )
        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(model.project_id, "project-001")
        self.assertEqual(model.description, "Build feature")
        self.assertEqual(model.context, "Application layer")

    def test_step_model_does_not_expose_action(self):
        model = StepModel(
            step_id="step-001",
            operation="build",
        )
        self.assertEqual(model.step_id, "step-001")
        self.assertEqual(model.operation, "build")
        self.assertFalse(hasattr(model, "action"))

    def test_plan_model(self):
        step = StepModel("step-001", "build")
        model = PlanModel(
            task_id="task-001",
            project_id="project-001",
            steps=(step,),
        )
        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(model.project_id, "project-001")
        self.assertEqual(model.steps, (step,))

    def test_run_model(self):
        model = RunModel("run-001", "task-001")
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")

    def test_execution_model(self):
        model = ExecutionModel("run-001", "RUNNING")
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "RUNNING")

    def test_result_model(self):
        model = ResultModel(
            run_id="run-001",
            status="COMPLETED",
            total_steps=3,
            successful_steps=3,
            completed_successfully=True,
        )
        self.assertEqual(model.total_steps, 3)
        self.assertEqual(model.successful_steps, 3)
        self.assertTrue(model.completed_successfully)

    def test_snapshot_model(self):
        model = SnapshotModel(
            run_id="run-001",
            task_id="task-001",
            run_status="COMPLETED",
            step_states={"step-001": "SUCCESS"},
        )
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(
            model.step_states["step-001"],
            "SUCCESS",
        )

    def test_models_are_immutable(self):
        model = ProjectModel("project-001")

        with self.assertRaises(FrozenInstanceError):
            model.project_id = "project-002"

    def test_application_models_have_no_core_imports(self):
        import application.models as models

        self.assertNotIn(
            "agent_workflow",
            {
                value.__name__.split(".")[0]
                for value in vars(models).values()
                if hasattr(value, "__name__")
            },
        )


if __name__ == "__main__":
    unittest.main()