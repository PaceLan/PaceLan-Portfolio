import unittest

from application.history import AgentHistoryStatus, AgentHistoryStore
from application.history_recorder import AgentHistoryRecorder
from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.verification import VerificationResult, VerificationStatus


class TestAgentHistoryRecorderA6(unittest.TestCase):
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

    def _verification(
        self,
        status=VerificationStatus.VERIFIED,
        verified=True,
    ):
        return VerificationResult(
            run_id="run-1",
            status=status,
            verified=verified,
            reason="test",
            checked_steps=1,
            successful_steps=1 if verified else 0,
            failed_steps=0,
            blocked_steps=0,
        )

    def test_records_real_application_execution(self):
        store = AgentHistoryStore()
        recorder = AgentHistoryRecorder(store)

        entry = recorder.record_execution(
            self._execution(),
            self._verification(),
            history_id="history-1",
            timestamp="2026-10-03T00:00:00+00:00",
        )

        self.assertEqual(entry.project_id, "project-1")
        self.assertEqual(entry.task_id, "task-1")
        self.assertEqual(entry.execution_id, "run-1")
        self.assertEqual(
            entry.verification_status,
            VerificationStatus.VERIFIED.value,
        )
        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.COMPLETED,
        )
        self.assertIs(store.get("history-1"), entry)

    def test_rejects_mismatched_execution_and_verification(self):
        recorder = AgentHistoryRecorder()

        verification = VerificationResult(
            run_id="different-run",
            status=VerificationStatus.VERIFIED,
            verified=True,
            reason="test",
            checked_steps=1,
            successful_steps=1,
            failed_steps=0,
            blocked_steps=0,
        )

        with self.assertRaisesRegex(ValueError, "same run_id"):
            recorder.record_execution(
                self._execution(),
                verification,
                history_id="history-1",
            )

    def test_maps_failed_execution_to_failed_history(self):
        recorder = AgentHistoryRecorder()

        entry = recorder.record_execution(
            self._execution("failed"),
            self._verification(
                VerificationStatus.NOT_VERIFIED,
                verified=False,
            ),
            history_id="history-1",
        )

        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.FAILED,
        )

    def test_maps_blocked_execution_to_blocked_history(self):
        recorder = AgentHistoryRecorder()

        entry = recorder.record_execution(
            self._execution("blocked"),
            self._verification(
                VerificationStatus.BLOCKED,
                verified=False,
            ),
            history_id="history-1",
        )

        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.BLOCKED,
        )



