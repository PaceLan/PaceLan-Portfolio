from __future__ import annotations

import unittest

from application.external_agent_recovery import (
    ExternalRecoveryResult,
    ExternalRecoveryState,
)
from application.external_agent_user_recovery import (
    ExternalAgentUserRecoveryService,
    ExternalUserRecoveryState,
)


class ExternalAgentUserRecoveryC57Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ExternalAgentUserRecoveryService()

    def result(
        self,
        *,
        state: ExternalRecoveryState,
        recoverable: bool = True,
        message: str = "existing session unavailable",
    ) -> ExternalRecoveryResult:
        return ExternalRecoveryResult(
            state=state,
            task_id="task-c57",
            workflow_id="workflow-c57",
            project_id="project-c57",
            run_id="run-c57",
            task_status=None,
            run_status="PAUSED",
            recoverable=recoverable,
            message=message,
        )

    def test_session_unavailable_becomes_waiting_for_user(self) -> None:
        result = self.service.present(
            self.result(state=ExternalRecoveryState.SESSION_NOT_AVAILABLE),
            action_required="Reconnect the existing Agent Session.",
        )

        self.assertEqual(
            result.state,
            ExternalUserRecoveryState.WAITING_FOR_USER,
        )
        self.assertEqual(result.task_id, "task-c57")
        self.assertEqual(result.workflow_id, "workflow-c57")
        self.assertEqual(result.project_id, "project-c57")
        self.assertEqual(result.run_id, "run-c57")
        self.assertEqual(result.reason, "existing session unavailable")
        self.assertEqual(
            result.action_required,
            "Reconnect the existing Agent Session.",
        )
        self.assertTrue(result.recoverable)

    def test_persisted_only_recovery_preserves_original_identity(self) -> None:
        result = self.service.present(
            self.result(
                state=ExternalRecoveryState.PERSISTED_ONLY,
                message="original Agent task is not present",
            ),
            action_required="Restore the original Agent connection.",
        )

        self.assertEqual(result.task_id, "task-c57")
        self.assertEqual(result.workflow_id, "workflow-c57")
        self.assertEqual(result.run_id, "run-c57")
        self.assertEqual(result.reason, "original Agent task is not present")

    def test_non_recoverable_state_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.present(
                self.result(
                    state=ExternalRecoveryState.PERSISTED_ONLY,
                    recoverable=False,
                ),
                action_required="Intervene manually.",
            )

    def test_running_recovery_is_not_user_wait(self) -> None:
        with self.assertRaises(ValueError):
            self.service.present(
                self.result(state=ExternalRecoveryState.RECONNECTED),
                action_required="Reconnect the Agent.",
            )

    def test_empty_user_action_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.present(
                self.result(state=ExternalRecoveryState.SESSION_NOT_AVAILABLE),
                action_required="   ",
            )


if __name__ == "__main__":
    unittest.main()
