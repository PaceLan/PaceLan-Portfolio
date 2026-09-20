import unittest

from agent_workflow.core_interfaces import (
    Execution,
    Project,
    Record,
    Result,
    Run,
    Task,
)


class CoreInterfacesTests(unittest.TestCase):
    def test_project_creation(self):
        project = Project(project_id="project-1")

        self.assertEqual(project.project_id, "project-1")

    def test_task_creation_and_project_relation(self):
        task = Task(
            task_id="task-1",
            project_id="project-1",
        )

        self.assertEqual(task.task_id, "task-1")
        self.assertEqual(task.project_id, "project-1")

    def test_run_creation_and_task_relation(self):
        run = Run(
            run_id="run-1",
            task_id="task-1",
        )

        self.assertEqual(run.run_id, "run-1")
        self.assertEqual(run.task_id, "task-1")

    def test_execution_creation(self):
        execution = Execution(
            run_id="run-1",
            status="IN_PROGRESS",
        )

        self.assertEqual(execution.run_id, "run-1")
        self.assertEqual(execution.status, "IN_PROGRESS")

    def test_result_creation(self):
        result = Result(
            run_id="run-1",
            status="COMPLETED",
        )

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.status, "COMPLETED")

    def test_record_creation(self):
        record = Record(
            record_id="record-1",
            project_id="project-1",
            run_id="run-1",
        )

        self.assertEqual(record.record_id, "record-1")
        self.assertEqual(record.project_id, "project-1")
        self.assertEqual(record.run_id, "run-1")

    def test_core_objects_are_immutable(self):
        project = Project(project_id="project-1")

        with self.assertRaises(AttributeError):
            project.project_id = "project-2"


if __name__ == "__main__":
    unittest.main()