import tempfile
import unittest
from pathlib import Path
from concurrent.futures import Future

from application.external_agent import (
    ExternalAgentRequest,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.external_agent_session import (
    ExternalAgentSessionState,
    ExternalAgentSessionStatus,
)
from application.runtime_authority import RuntimeAuthority
from application.external_agent_recovery import (
    ExternalAgentRecoveryContext,
    ExternalAgentRecoveryService,
    ExternalRecoveryResult,
    ExternalRecoveryState,
)
from application.external_agent_retry_policy import (
    ExternalAgentRetryPolicy,
)
from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ProjectGoal,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.project_storage import ProjectStorage
from application.universal_agent_interface import (
    AgentRuntimeState,
    AgentRuntimeView,
    UniversalAgentInterface,
)
from application.workflow_storage import WorkflowStorage


class _SessionCapability:
    def __init__(self, session_id="session-c1"):
        self.session_id = session_id
        self.inspect_calls = []
        self.attach_calls = []

    def inspect_session(self, session_id, request):
        self.inspect_calls.append(session_id)
        return ExternalAgentSessionStatus(
            session_id=session_id,
            state=ExternalAgentSessionState.AVAILABLE,
        )

    def attach_session(self, session_id, request):
        self.attach_calls.append(session_id)
        return ExternalAgentSessionStatus(
            session_id=session_id,
            state=ExternalAgentSessionState.ATTACHED,
        )


class _Backend:
    def __init__(self):
        self.runtime = AgentRuntimeState.IDLE

    def risk_for(self, operation):
        return "SAFE"

    def start(self, task, operations, plan, progress):
        future = Future()
        self.runtime = AgentRuntimeState.RUNNING
        return future

    def pause(self):
        self.runtime = AgentRuntimeState.PAUSED
        return AgentRuntimeView(self.runtime, True)

    def resume(self):
        self.runtime = AgentRuntimeState.RUNNING
        return AgentRuntimeView(self.runtime, True)

    def stop(self):
        self.runtime = AgentRuntimeState.STOPPED
        return AgentRuntimeView(self.runtime, True)

    def inspect_runtime(self):
        return AgentRuntimeView(self.runtime, True)


def _persist_workflow(root: Path, run_status: str) -> None:
    project = ProjectModel(
        project_id="project-c1",
        goal=ProjectGoal(text="c1 recovery"),
    )
    ProjectStorage().save(project, root)

    task = TaskModel(
        task_id="task-c1",
        project_id="project-c1",
        description="recover external task",
    )
    plan = PlanModel(
        task_id="task-c1",
        project_id="project-c1",
    )
    run = RunModel(
        run_id="run-c1",
        task_id="task-c1",
    )
    result = ResultModel(
        run_id="run-c1",
        status="pending",
        completed_successfully=False,
    )
    snapshot = SnapshotModel(
        run_id="run-c1",
        task_id="task-c1",
        run_status=run_status,
    )

    WorkflowStorage().save(
        ApplicationExecutionModel(
            task=task,
            plan=plan,
            run=run,
            result=result,
            snapshot=snapshot,
        ),
        root,
    )


class TestExternalAgentRecoveryC13(unittest.TestCase):

    def setUp(self):
        self.backend = _Backend()
        self.agent = UniversalAgentInterface(self.backend)
        self.runtime_authority = RuntimeAuthority()
        self.gateway = ExternalAgentGateway(
            self.agent,
            workflow_id="project-c1",
            runtime_authority=self.runtime_authority,
        )
        self.recovery = ExternalAgentRecoveryService(self.gateway)

    def request(self):
        return ExternalAgentRequest(
            task_id="task-c1",
            payload="continue",
            workflow_id="workflow-c1",
        )

    def test_c5_6_restores_full_agent_context(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            restored = self.recovery.restore_agent_context(
                root,
                self.request(),
            )

            self.assertIsInstance(
                restored,
                ExternalAgentRecoveryContext,
            )
            self.assertEqual(restored.project_id, "project-c1")
            self.assertEqual(restored.goal, "c1 recovery")
            self.assertEqual(restored.task.task_id, "task-c1")
            self.assertEqual(restored.plan.task_id, "task-c1")
            self.assertEqual(restored.run.run_id, "run-c1")
            self.assertEqual(restored.execution.run_status, "PAUSED")
            self.assertEqual(restored.result.run_id, "run-c1")
            self.assertIsNone(restored.verification)
            self.assertIsNone(restored.context)
            self.assertIsNone(restored.error)

    def test_c5_6_restores_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = ProjectModel(
                project_id="project-c1",
                goal=ProjectGoal(text="verification recovery"),
            )
            ProjectStorage().save(project, root)

            task = TaskModel(
                task_id="task-c1",
                project_id="project-c1",
                description="recover with verification",
            )
            plan = PlanModel(task_id="task-c1", project_id="project-c1")
            run = RunModel(run_id="run-c1", task_id="task-c1")
            result = ResultModel(
                run_id="run-c1",
                status="success",
                completed_successfully=True,
            )
            snapshot = SnapshotModel(
                run_id="run-c1",
                task_id="task-c1",
                run_status="PAUSED",
            )

            from application.verification import VerificationResult, VerificationStatus

            verification = VerificationResult(
                run_id="run-c1",
                status=VerificationStatus.VERIFIED,
                verified=True,
                reason="recovery verification",
                checked_steps=1,
                successful_steps=1,
                failed_steps=0,
                blocked_steps=0,
            )

            WorkflowStorage().save(
                ApplicationExecutionModel(
                    task=task,
                    plan=plan,
                    run=run,
                    result=result,
                    snapshot=snapshot,
                    verification=verification,
                ),
                root,
            )

            restored = self.recovery.restore_agent_context(
                root,
                self.request(),
            )

            self.assertIsNotNone(restored)
            self.assertIsNotNone(restored.verification)
            self.assertEqual(
                restored.verification.reason,
                "recovery verification",
            )

    def test_c5_6_restores_recovery_error(self):
        from application.recovery_state_storage import (
            RecoveryState,
            RecoveryStateStorage,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            RecoveryStateStorage(root).save(
                RecoveryState(
                    recovery_id="recovery-c1",
                    snapshot_id="snapshot-c1",
                    status="FAILED",
                    reason="external connection interrupted",
                )
            )

            restored = self.recovery.restore_agent_context(
                root,
                self.request(),
            )

            self.assertIsNotNone(restored)
            self.assertEqual(
                restored.error,
                "external connection interrupted",
            )

    def test_c5_6_rejects_context_for_different_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            request = ExternalAgentRequest(
                task_id="different-task",
                payload="continue",
                workflow_id="workflow-c1",
            )

            restored = self.recovery.restore_agent_context(
                root,
                request,
            )

            self.assertIsNone(restored)

    def test_existing_session_is_verified_and_attached(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")
            capability = _SessionCapability()

            recovery = ExternalAgentRecoveryService(
                self.gateway,
                session_capability=capability,
            )

            result = recovery.recover_existing_session(
                root,
                self.request(),
                "session-c1",
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.SESSION_ATTACHED,
            )
            self.assertEqual(result.task_id, "task-c1")
            self.assertEqual(result.workflow_id, "workflow-c1")
            self.assertEqual(result.run_id, "run-c1")
            self.assertEqual(capability.inspect_calls, ["session-c1"])
            self.assertEqual(capability.attach_calls, ["session-c1"])

    def test_recovery_continuity_accepts_original_task_and_workflow(self):
        result = ExternalRecoveryResult(
            state=ExternalRecoveryState.SESSION_ATTACHED,
            task_id="task-c1",
            workflow_id="workflow-c1",
            project_id="project-c1",
            run_id="run-c1",
            task_status=None,
            run_status="PAUSED",
            recoverable=True,
        )

        self.assertTrue(
            self.recovery.verify_continuity(
                self.request(),
                result,
            )
        )

    def test_recovery_continuity_rejects_task_mismatch(self):
        result = ExternalRecoveryResult(
            state=ExternalRecoveryState.SESSION_ATTACHED,
            task_id="replacement-task",
            workflow_id="workflow-c1",
            project_id="project-c1",
            run_id="run-c1",
            task_status=None,
            run_status="PAUSED",
            recoverable=True,
        )

        self.assertFalse(
            self.recovery.verify_continuity(
                self.request(),
                result,
            )
        )

    def test_recovery_continuity_rejects_workflow_mismatch(self):
        result = ExternalRecoveryResult(
            state=ExternalRecoveryState.SESSION_ATTACHED,
            task_id="task-c1",
            workflow_id="replacement-workflow",
            project_id="project-c1",
            run_id="run-c1",
            task_status=None,
            run_status="PAUSED",
            recoverable=True,
        )

        self.assertFalse(
            self.recovery.verify_continuity(
                self.request(),
                result,
            )
        )

    def test_existing_session_recovery_never_creates_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            capability = _SessionCapability()
            recovery = ExternalAgentRecoveryService(
                self.gateway,
                session_capability=capability,
            )

            result = recovery.recover_existing_session(
                root,
                self.request(),
                None,
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.SESSION_NOT_AVAILABLE,
            )
            self.assertEqual(capability.inspect_calls, [])
            self.assertEqual(capability.attach_calls, [])

    def test_existing_session_requires_real_provider_capability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            recovery = ExternalAgentRecoveryService(self.gateway)

            result = recovery.recover_existing_session(
                root,
                self.request(),
                "session-c1",
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.SESSION_NOT_AVAILABLE,
            )
            self.assertTrue(result.recoverable)

    def test_connection_lost_is_recoverable(self):
        status = self.recovery.mark_connection_lost(
            message="connection interrupted",
        )

        self.assertEqual(
            status.state,
            ExternalConnectionState.WAITING_EXTERNAL,
        )
        self.assertEqual(
            status.reason,
            ExternalConnectionReason.CONNECTION_LOST,
        )
        self.assertTrue(status.recoverable)

    def test_missing_workflow_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.recovery.inspect_persisted(
                Path(temp),
                self.request(),
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.NOT_FOUND,
            )
            self.assertFalse(result.recoverable)

    def test_running_persisted_workflow_is_recoverable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "RUNNING")

            result = self.recovery.inspect_persisted(
                root,
                self.request(),
            )

            self.assertEqual(result.state, ExternalRecoveryState.READY)
            self.assertTrue(result.recoverable)
            self.assertEqual(result.run_id, "run-c1")

    def test_reconnect_does_not_fake_missing_in_memory_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            result = self.recovery.reconnect(
                root,
                self.request(),
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.PERSISTED_ONLY,
            )
            self.assertTrue(result.recoverable)

    def test_level1_recover_keeps_waiting_external_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            self.recovery.mark_connection_lost(
                message="external service unavailable",
            )

            attempts = []

            recovery = ExternalAgentRecoveryService(
                self.gateway,
                retry_policy=ExternalAgentRetryPolicy(
                    max_attempts=3,
                    retry_delay_seconds=0,
                ),
                sleeper=lambda delay: attempts.append(delay),
            )

            result = recovery.recover(root, self.request())

            self.assertEqual(
                result.state,
                ExternalRecoveryState.PERSISTED_ONLY,
            )
            self.assertTrue(result.recoverable)
            self.assertEqual(attempts, [])
            self.assertEqual(
                self.gateway.status().state,
                ExternalConnectionState.WAITING_EXTERNAL,
            )

    def test_level1_recover_retries_connection_with_bounded_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            request = self.request()

            self.gateway.connect()
            self.gateway.create_task(request)
            self.gateway.submit_task(request)
            self.gateway.start(request)
            self.gateway.pause(request)
            self.gateway.disconnect()

            attempts = []

            def sleeper(delay):
                attempts.append(delay)

            recovery = ExternalAgentRecoveryService(
                self.gateway,
                retry_policy=ExternalAgentRetryPolicy(
                    max_attempts=3,
                    retry_delay_seconds=0,
                ),
                sleeper=sleeper,
            )

            result = recovery.recover(root, request)

            self.assertEqual(result.state, ExternalRecoveryState.RESUMED)
            self.assertEqual(result.task_status, "RUNNING")
            self.assertEqual(attempts, [])

    def test_level1_recover_stops_after_retry_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            attempts = []

            def connect_without_transport():
                attempts.append(True)
                return self.gateway.status()

            recovery = ExternalAgentRecoveryService(
                self.gateway,
                retry_policy=ExternalAgentRetryPolicy(
                    max_attempts=2,
                    retry_delay_seconds=0,
                ),
                sleeper=lambda delay: None,
            )

            self.gateway.connect = connect_without_transport

            result = recovery.recover(root, self.request())

            self.assertEqual(
                result.state,
                ExternalRecoveryState.PERSISTED_ONLY,
            )
            self.assertTrue(result.recoverable)
            self.assertEqual(len(attempts), 2)

    def test_level1_recover_reconnects_and_resumes_original_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            request = self.request()

            self.gateway.connect()
            self.gateway.create_task(request)
            self.gateway.submit_task(request)
            self.gateway.start(request)
            self.gateway.pause(request)
            self.gateway.disconnect()

            result = self.recovery.recover(root, request)

            self.assertEqual(result.state, ExternalRecoveryState.RESUMED)
            self.assertEqual(result.task_id, "task-c1")
            self.assertEqual(result.workflow_id, "workflow-c1")
            self.assertEqual(result.run_id, "run-c1")
            self.assertEqual(result.task_status, "RUNNING")
            self.assertTrue(result.recoverable)

    def test_level1_recover_does_not_resume_running_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "RUNNING")

            request = self.request()

            self.gateway.connect()
            self.gateway.create_task(request)
            self.gateway.submit_task(request)
            self.gateway.start(request)
            self.gateway.disconnect()

            result = self.recovery.recover(root, request)

            self.assertEqual(result.state, ExternalRecoveryState.RECONNECTED)
            self.assertEqual(result.task_status, "RUNNING")
            self.assertTrue(result.recoverable)

    def test_level1_recover_does_not_fabricate_missing_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            result = self.recovery.recover(root, self.request())

            self.assertEqual(
                result.state,
                ExternalRecoveryState.PERSISTED_ONLY,
            )
            self.assertIsNone(result.task_status)
            self.assertTrue(result.recoverable)

    def test_live_paused_task_can_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _persist_workflow(root, "PAUSED")

            self.gateway.connect()
            self.gateway.create_task(
                ExternalAgentRequest(
                    task_id="task-c1",
                    payload="continue",
                    workflow_id="project-c1",
                )
            )
            self.gateway.submit_task(
                ExternalAgentRequest(
                    task_id="task-c1",
                    payload="continue",
                    workflow_id="project-c1",
                )
            )
            self.gateway.start(
                ExternalAgentRequest(
                    task_id="task-c1",
                    payload="continue",
                    workflow_id="project-c1",
                )
            )
            self.gateway.pause(
                ExternalAgentRequest(
                    task_id="task-c1",
                    payload="continue",
                    workflow_id="project-c1",
                )
            )

            result = self.recovery.resume(
                root,
                self.request(),
            )

            self.assertEqual(
                result.state,
                ExternalRecoveryState.RESUMED,
            )
            self.assertEqual(
                result.task_status,
                "RUNNING",
            )


if __name__ == "__main__":
    unittest.main()
