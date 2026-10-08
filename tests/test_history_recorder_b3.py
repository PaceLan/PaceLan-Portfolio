import tempfile
import unittest
from pathlib import Path

from application.history import AgentHistoryStatus
from application.history_recorder import AgentHistoryRecorder
from application.history_storage import AgentHistoryStorage
from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.verification import VerificationResult, VerificationStatus


class TestAgentHistoryRecorderB3(unittest.TestCase):
    def _execution(self, status="completed"):
        task = TaskModel(
            task_id="task-1",
            project_id="project-1",
        )
        plan = PlanModel(
            task_id="task-1",
            project_id="project-1",
        )
        run = RunModel(
            run_id="run-1",
            task_id="task-1",
        )
        result = ResultModel(
            run_id="run-1",
            status=status,
            completed_successfully=status == "completed",
        )
        snapshot = SnapshotModel(
            run_id="run-1",
            task_id="task-1",
            run_status=status,
        )
        return ApplicationExecutionModel(
            task=task,
            plan=plan,
            run=run,
            result=result,
            snapshot=snapshot,
        )

    def _verification(self):
        return VerificationResult(
            run_id="run-1",
            status=VerificationStatus.VERIFIED,
            verified=True,
            reason="test",
            checked_steps=1,
            successful_steps=1,
            failed_steps=0,
            blocked_steps=0,
        )

    def test_record_execution_persists_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            recorder = AgentHistoryRecorder(
                storage=AgentHistoryStorage(),
                project_path=project,
            )

            entry = recorder.record_execution(
                self._execution(),
                self._verification(),
                history_id="history-1",
            )

            restored = AgentHistoryStorage().load(project)

            self.assertEqual(restored, (entry,))
            self.assertEqual(
                restored[0].result_status,
                AgentHistoryStatus.COMPLETED,
            )

    def test_recorder_restores_existing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            storage = AgentHistoryStorage()
            existing = AgentHistoryRecorder(
                storage=storage,
                project_path=project,
            )
            first = existing.record_execution(
                self._execution(),
                self._verification(),
                history_id="history-1",
            )

            restarted = AgentHistoryRecorder(
                storage=AgentHistoryStorage(),
                project_path=project,
            )

            self.assertEqual(restarted.store.list_all(), (first,))

    def test_memory_only_recorder_remains_compatible(self):
        recorder = AgentHistoryRecorder()

        entry = recorder.record_execution(
            self._execution(),
            self._verification(),
            history_id="history-1",
        )

        self.assertEqual(recorder.store.list_all(), (entry,))


if __name__ == "__main__":
    unittest.main()
