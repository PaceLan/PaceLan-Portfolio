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
from application.runtime_authority import RuntimeAuthority
from application.external_agent_recovery import (
    ExternalAgentRecoveryService,
    ExternalRecoveryState,
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
