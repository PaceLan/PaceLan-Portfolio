import unittest
from dataclasses import FrozenInstanceError

import application
from application import (
    ExecutionModel,
    PlanModel,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)


class ApplicationPublicContractM1861Tests(unittest.TestCase):

    def test_public_exports_are_complete(self):
        expected = {
            "ExecutionModel",
            "PlanModel",
            "ProjectModel",
            "ResultModel",
            "RunModel",
            "SnapshotModel",
            "StepModel",
            "TaskModel",
        }

        self.assertEqual(set(application.__all__), expected)

    def test_public_models_are_importable_from_package_root(self):
        for name in application.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(application, name))

    def test_models_are_frozen(self):
        models = (
            ProjectModel("p1"),
            TaskModel("t1", "p1"),
            StepModel("step-001", "read"),
            PlanModel("t1", "p1"),
            RunModel("r1", "t1"),
            ExecutionModel("r1", "SUCCESS"),
            ResultModel("r1", "SUCCESS"),
            SnapshotModel("r1", "t1", "SUCCESS"),
        )

        for model in models:
            field_name = next(iter(vars(model)))

            with self.subTest(model=type(model).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(model, field_name, "changed")

    def test_snapshot_step_states_are_immutable(self):
        snapshot = SnapshotModel(
            run_id="r1",
            task_id="t1",
            run_status="SUCCESS",
            step_states={"step-001": "SUCCESS"},
        )

        with self.assertRaises(TypeError):
            snapshot.step_states["step-002"] = "FAILED"

    def test_models_do_not_expose_core_object_fields(self):
        models = (
            ProjectModel("p1"),
            TaskModel("t1", "p1"),
            StepModel("step-001", "read"),
            PlanModel("t1", "p1"),
            RunModel("r1", "t1"),
            ExecutionModel("r1", "SUCCESS"),
            ResultModel("r1", "SUCCESS"),
            SnapshotModel("r1", "t1", "SUCCESS"),
        )

        forbidden_types = {
            "Project",
            "Task",
            "Run",
            "Execution",
            "Result",
            "WorkflowPlan",
            "WorkflowStep",
            "ExecutionSnapshot",
            "WorkflowResult",
        }

        for model in models:
            for value in vars(model).values():
                if value is None:
                    continue

                self.assertNotIn(
                    type(value).__name__,
                    forbidden_types,
                    msg=(
                        f"{type(model).__name__} "
                        "exposes Core object"
                    ),
                )


if __name__ == "__main__":
    unittest.main()