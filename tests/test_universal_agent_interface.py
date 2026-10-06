from concurrent.futures import Future
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from threading import Event
import time
import unittest
from unittest.mock import Mock

from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)
from application.runtime_control import RuntimeControlResult, RuntimeControlState
from application.services import ApplicationExecutionService
from application.runtime_authority import RuntimeAuthority
from application.universal_agent_backend import (
    AgentServiceUnderstandingProvider,
    ApplicationExecutionBackend,
    LocalOperation,
)
from application.universal_agent_interface import (
    AgentEventName,
    AgentOperationRequest,
    AgentRuntimeState,
    AgentRuntimeView,
    AgentTaskStatus,
    AgentUnderstandingView,
    UniversalAgentInterface,
)
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class _ApprovalAuthorizer:
    def authorize(self, task_id, step_id, decision, actor):
        return actor == "reviewer"


class _FakeBackend:
    def __init__(self, *, complete_immediately=True, operations=None):
        self.complete_immediately = complete_immediately
        self.operations = operations or {"inspect": "SAFE"}
        self.runtime_calls = []
        self.future = None
        self.result = None

    def risk_for(self, operation):
        return self.operations[operation]

    def start(self, task, operations, plan, progress):
        self.future = Future()
        if self.complete_immediately:
            for step in plan.steps:
                progress(step.step_id, "started")
                progress(step.step_id, "completed")
            self.future.set_result(_execution(task, plan))
        return self.future

    def pause(self):
        self.runtime_calls.append("pause")
        return AgentRuntimeView(AgentRuntimeState.PAUSED, True)

    def resume(self):
        self.runtime_calls.append("resume")
        return AgentRuntimeView(AgentRuntimeState.RUNNING, True)

    def stop(self):
        self.runtime_calls.append("stop")
        return AgentRuntimeView(AgentRuntimeState.STOPPED, True)

    def inspect_runtime(self):
        self.runtime_calls.append("inspect")
        return AgentRuntimeView(AgentRuntimeState.RUNNING, True)


def _execution(task, plan):
    now = datetime.now(timezone.utc)
    run = RunModel("run-1", task.task_id)
    result = ResultModel(
        run_id=run.run_id,
        status="COMPLETED",
        total_steps=len(plan.steps),
        successful_steps=len(plan.steps),
        completed_successfully=True,
    )
    snapshot = SnapshotModel(
        run_id=run.run_id,
        task_id=task.task_id,
        run_status="COMPLETED",
        step_states={step.step_id: "SUCCESS" for step in plan.steps},
        started_at=now,
        finished_at=now,
    )
    return ApplicationExecutionModel(task, plan, run, result, snapshot)


class UniversalAgentInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.backend = _FakeBackend()
        self.interface = UniversalAgentInterface(
            self.backend,
            understanding_provider=self,
        )

    def inspect(self, task):
        return AgentUnderstandingView(
            task_id=task.task_id,
            summary="Local understanding",
            relevant_files=("main.py",),
        )

    def _create_and_submit_safe_task(self):
        created = self.interface.create_task(
            "project-1",
            "inspect the project",
            task_id="task-1",
        )
        submitted = self.interface.submit_task(
            created.task.task_id,
            (AgentOperationRequest("inspect", target="main.py"),),
        )
        return created, submitted

    def test_task_understanding_plan_and_events_are_inspectable(self):
        created, submitted = self._create_and_submit_safe_task()

        self.assertEqual(created.status, AgentTaskStatus.CREATED)
        self.assertEqual(submitted.status, AgentTaskStatus.READY)
        self.assertTrue(self.interface.inspect_plan("task-1").ready)
        self.assertEqual(
            self.interface.inspect_understanding("task-1").summary,
            "Local understanding",
        )
        self.assertEqual(
            self.interface.events(task_id="task-1")[-1].name,
            AgentEventName.TASK_SUBMITTED,
        )

    def test_real_backend_future_populates_result_progress_and_history(self):
        _, submitted = self._create_and_submit_safe_task()

        started = self.interface.start(submitted.task.task_id)

        self.assertEqual(started.status, AgentTaskStatus.RUNNING)
        self.assertEqual(
            self.interface.inspect_task("task-1").status,
            AgentTaskStatus.COMPLETED,
        )
        self.assertEqual(self.interface.inspect_progress("task-1"), 100)
        self.assertEqual(self.interface.result("task-1").status, "COMPLETED")
        self.assertEqual(self.interface.inspect_execution("task-1").progress, 100)
        self.assertEqual(
            self.interface.history()[0].status,
            AgentTaskStatus.COMPLETED,
        )
        event_names = {event.name for event in self.interface.events()}
        self.assertTrue(
            {
                AgentEventName.TASK_STARTED,
                AgentEventName.TASK_EXECUTION_STARTED,
                AgentEventName.TASK_EXECUTION_PROGRESS,
                AgentEventName.TASK_COMPLETED,
            }.issubset(event_names)
        )
        ordered_events = [event.name for event in self.interface.events()]
        self.assertLess(
            ordered_events.index(AgentEventName.TASK_STARTED),
            ordered_events.index(AgentEventName.TASK_EXECUTION_PROGRESS),
        )

    def test_high_risk_defaults_to_waiting_and_cannot_self_approve(self):
        backend = _FakeBackend(operations={"delete": "HIGH_RISK"})
        interface = UniversalAgentInterface(backend)
        task = interface.create_task("project-1", "delete file", task_id="risk-1")
        waiting = interface.submit_task(
            task.task.task_id,
            (AgentOperationRequest("delete", target="data.txt"),),
        )

        self.assertEqual(waiting.status, AgentTaskStatus.WAITING_APPROVAL)
        self.assertFalse(waiting.plan.ready)
        with self.assertRaises(PermissionError):
            interface.approve("risk-1", waiting.plan.steps[0].step_id, actor="agent")
        with self.assertRaises(PermissionError):
            interface.start("risk-1")
        self.assertFalse(backend.runtime_calls)

    def test_authorized_approval_and_rejection_are_explicit(self):
        backend = _FakeBackend(operations={"delete": "HIGH_RISK"})
        interface = UniversalAgentInterface(
            backend,
            approval_authorizer=_ApprovalAuthorizer(),
        )
        task = interface.create_task("project-1", "delete file", task_id="risk-2")
        waiting = interface.submit_task(
            task.task.task_id,
            (AgentOperationRequest("delete", target="data.txt"),),
        )
        step_id = waiting.plan.steps[0].step_id

        approved = interface.approve("risk-2", step_id, actor="reviewer")
        self.assertTrue(approved.plan.ready)
        self.assertEqual(approved.plan.steps[0].approval, "APPROVED")
        self.assertEqual(approved.status, AgentTaskStatus.READY)

        rejected_task = interface.create_task(
            "project-1",
            "delete another file",
            task_id="risk-3",
        )
        rejected_wait = interface.submit_task(
            rejected_task.task.task_id,
            (AgentOperationRequest("delete", target="other.txt"),),
        )
        rejected = interface.reject(
            "risk-3",
            rejected_wait.plan.steps[0].step_id,
            actor="reviewer",
        )
        self.assertEqual(rejected.status, AgentTaskStatus.REJECTED)
        with self.assertRaises(PermissionError):
            interface.start("risk-3")

    def test_runtime_control_and_events_delegate_to_backend(self):
        backend = _FakeBackend(complete_immediately=False)
        interface = UniversalAgentInterface(backend)
        task = interface.create_task("project-1", "inspect", task_id="runtime-1")
        interface.submit_task(task.task.task_id, ())
        interface.start(task.task.task_id)

        self.assertEqual(
            interface.pause(task.task.task_id).state,
            AgentRuntimeState.PAUSED,
        )
        self.assertEqual(
            interface.resume(task.task.task_id).state,
            AgentRuntimeState.RUNNING,
        )
        self.assertEqual(
            interface.stop(task.task.task_id).state,
            AgentRuntimeState.STOPPED,
        )
        self.assertEqual(backend.runtime_calls, ["pause", "resume", "stop"])
        self.assertEqual(
            [event.name for event in interface.events(task_id="runtime-1")][-3:],
            [
                AgentEventName.TASK_PAUSED,
                AgentEventName.TASK_RESUMED,
                AgentEventName.TASK_STOPPED,
            ],
        )

    def test_operation_limit_is_enforced_before_submission(self):
        interface = UniversalAgentInterface(
            _FakeBackend(),
            max_operations_per_task=1,
        )
        task = interface.create_task("project-1", "inspect", task_id="limit-1")

        with self.assertRaises(PermissionError):
            interface.submit_task(
                task.task.task_id,
                (
                    AgentOperationRequest("inspect"),
                    AgentOperationRequest("inspect"),
                ),
            )


class ApplicationExecutionBackendTests(unittest.TestCase):
    def _stub_execution_service(self):
        service = object.__new__(ApplicationExecutionService)
        service.start = Mock(return_value=Future())
        service.pause = Mock(
            return_value=RuntimeControlResult("pause", RuntimeControlState.PAUSED, True)
        )
        service.resume = Mock(
            return_value=RuntimeControlResult("resume", RuntimeControlState.RUNNING, True)
        )
        service.terminate = Mock(
            return_value=RuntimeControlResult("terminate", RuntimeControlState.TERMINATED, True)
        )
        service.runtime_status = Mock(
            return_value=RuntimeControlResult("status", RuntimeControlState.RUNNING, True)
        )
        return service

    def test_adapter_maps_registered_local_operations_to_existing_service(self):
        calls = []
        service = self._stub_execution_service()
        backend = ApplicationExecutionBackend(
            service,
            {
                "inspect": LocalOperation(
                    "SAFE",
                    lambda task, operation: calls.append(operation.target) or "ok",
                ),
            },
        )
        interface = UniversalAgentInterface(backend)
        task = interface.create_task("project-1", "inspect", task_id="adapter-1")
        submitted = interface.submit_task(
            task.task.task_id,
            (AgentOperationRequest("inspect", target="main.py"),),
        )

        interface.start(task.task.task_id)

        service.start.assert_called_once()
        workflow_steps = service.start.call_args.args[1]
        self.assertEqual(len(workflow_steps), 1)
        self.assertEqual(workflow_steps[0].risk.value, "SAFE")
        self.assertEqual(workflow_steps[0].approval.value, "NOT_REQUESTED")
        self.assertEqual(workflow_steps[0].action(), "ok")
        self.assertEqual(calls, ["main.py"])

    def test_adapter_rechecks_high_risk_approval_before_dispatch(self):
        service = self._stub_execution_service()
        backend = ApplicationExecutionBackend(
            service,
            {"delete": LocalOperation("HIGH_RISK", lambda task, operation: "deleted")},
        )
        interface = UniversalAgentInterface(
            backend,
            approval_authorizer=_ApprovalAuthorizer(),
        )
        task = interface.create_task("project-1", "delete", task_id="adapter-2")
        waiting = interface.submit_task(
            task.task.task_id,
            (AgentOperationRequest("delete", target="data.txt"),),
        )
        interface.approve(
            task.task.task_id,
            waiting.plan.steps[0].step_id,
            actor="reviewer",
        )

        interface.start(task.task.task_id)

        workflow_step = service.start.call_args.args[1][0]
        self.assertEqual(workflow_step.risk.value, "HIGH_RISK")
        self.assertEqual(workflow_step.approval.value, "APPROVED")

    def test_agent_understanding_provider_maps_existing_context_interface(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "main.py").write_text(
                "def inspect_project():\n    return True\n",
                encoding="utf-8",
            )
            context = ProjectContextBuilder().build(
                ProjectScanner(project).scan()
            )
            context_agent = ProjectContextAgentInterface(context)
            workflow = AgentWorkflow(
                history_store=HistoryStore(project / "history.json"),
                snapshot_service=SnapshotService(
                    project,
                    store=SnapshotStore(project, project / "snapshots"),
                ),
            )
            agent_service = AgentService(
                WorkflowService(workflow),
                project_context_agent=context_agent,
            )
            provider = AgentServiceUnderstandingProvider(agent_service)

            view = provider.inspect(
                TaskModel(
                    task_id="understand-1",
                    project_id="project-1",
                    description="inspect project",
                    context="target: main.py",
                )
            )

        self.assertEqual(view.task_id, "understand-1")
        self.assertIn("understand-1", view.summary)
        self.assertIn("main.py", view.relevant_files)


class _CapturingApplicationExecutionBackend(ApplicationExecutionBackend):
    def start(self, task, operations, plan, progress):
        self.future = super().start(task, operations, plan, progress)
        return self.future


class LocalExecutionRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        workflow = AgentWorkflow(
            history_store=HistoryStore(self.root / "history.json"),
            snapshot_service=SnapshotService(
                self.root,
                store=SnapshotStore(self.root, self.root / "snapshots"),
            ),
        )
        self.execution_service = ApplicationExecutionService(
            AgentService(WorkflowService(workflow)),
            runtime_authority=RuntimeAuthority(),
        )

    def tearDown(self):
        self.execution_service._executor.shutdown(wait=True)
        self.temporary_directory.cleanup()

    def _make_interface(self, operations):
        backend = _CapturingApplicationExecutionBackend(
            self.execution_service,
            operations,
        )
        return backend, UniversalAgentInterface(backend)

    def test_pause_and_resume_gate_the_next_local_operation(self):
        first_started = Event()
        release_first = Event()
        second_started = Event()

        def first(_task, _operation):
            first_started.set()
            if not release_first.wait(5):
                raise TimeoutError("test did not release the first operation")
            return "first complete"

        def second(_task, _operation):
            second_started.set()
            return "second complete"

        backend, interface = self._make_interface(
            {
                "first": LocalOperation("SAFE", first),
                "second": LocalOperation("SAFE", second),
            }
        )
        task = interface.create_task("project-1", "inspect", task_id="pause-1")
        interface.submit_task(
            task.task.task_id,
            (
                AgentOperationRequest("first"),
                AgentOperationRequest("second"),
            ),
        )

        interface.start(task.task.task_id)
        self.assertTrue(first_started.wait(3))
        self.assertEqual(
            interface.pause(task.task.task_id).state,
            AgentRuntimeState.PAUSED,
        )
        release_first.set()
        self.assertFalse(second_started.wait(0.3))
        self.assertEqual(
            interface.resume(task.task.task_id).state,
            AgentRuntimeState.RUNNING,
        )
        self.assertTrue(second_started.wait(3))
        self.assertEqual(backend.future.result(timeout=3).result.status, "COMPLETED")

    def test_stop_prevents_next_operation_and_preserves_stopped_status(self):
        first_started = Event()
        release_first = Event()
        second_started = Event()

        def first(_task, _operation):
            first_started.set()
            if not release_first.wait(5):
                raise TimeoutError("test did not release the first operation")
            return "first complete"

        def second(_task, _operation):
            second_started.set()
            return "must not execute"

        backend, interface = self._make_interface(
            {
                "first": LocalOperation("SAFE", first),
                "second": LocalOperation("SAFE", second),
            }
        )
        task = interface.create_task("project-1", "inspect", task_id="stop-1")
        interface.submit_task(
            task.task.task_id,
            (
                AgentOperationRequest("first"),
                AgentOperationRequest("second"),
            ),
        )

        interface.start(task.task.task_id)
        self.assertTrue(first_started.wait(3))
        self.assertEqual(
            interface.stop(task.task.task_id).state,
            AgentRuntimeState.STOPPED,
        )
        release_first.set()
        execution = backend.future.result(timeout=3)

        self.assertFalse(second_started.is_set())
        self.assertEqual(execution.result.status, "FAILED")
        self.assertEqual(
            interface.inspect_task(task.task.task_id).status,
            AgentTaskStatus.STOPPED,
        )


if __name__ == "__main__":
    unittest.main()
