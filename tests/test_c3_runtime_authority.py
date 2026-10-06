import tempfile
import unittest
from pathlib import Path

from application.external_agent import ExternalAgentRequest
from application.external_agent_bridge import (
    ExternalAgentCommand,
    ExternalAgentMessageBridge,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.external_agent_http_server import ExternalAgentHTTPServer
from application.runtime_authority import RuntimeAuthority
from application.runtime_control import RuntimeControlState
from application.services import ApplicationExecutionService
from agent_workflow.agent_service import AgentService
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService
from application.universal_agent_interface import (
    AgentRuntimeState,
    AgentRuntimeView,
    UniversalAgentInterface,
)
from application.vscode_integration import VSCodeIntegration


class _Backend:
    def __init__(self):
        self.runtime = AgentRuntimeState.IDLE

    def risk_for(self, operation):
        return "SAFE"

    def start(self, task, operations, plan, progress):
        self.runtime = AgentRuntimeState.RUNNING
        from concurrent.futures import Future
        return Future()

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


class _FailingStartBackend(_Backend):
    def start(self, task, operations, plan, progress):
        raise RuntimeError("start failed")


class _FailingPauseBackend(_Backend):
    def pause(self):
        raise RuntimeError("pause failed")


class _FailingResumeBackend(_Backend):
    def resume(self):
        raise RuntimeError("resume failed")


class _FailingStopBackend(_Backend):
    def stop(self):
        raise RuntimeError("stop failed")


class C3RuntimeAuthorityTests(unittest.TestCase):
    def make_gateway(self):
        authority = RuntimeAuthority()
        agent = UniversalAgentInterface(_Backend())
        gateway = ExternalAgentGateway(
            agent,
            runtime_authority=authority,
        )
        gateway.connect()
        return authority, gateway

    def test_gateway_uses_injected_runtime_authority(self):
        authority, gateway = self.make_gateway()

        self.assertIs(gateway.runtime_authority, authority)
        self.assertEqual(
            authority.state(),
            RuntimeControlState.IDLE,
        )
        self.assertEqual(
            gateway.inspect_runtime().state,
            RuntimeControlState.IDLE,
        )

    def _started_gateway(self, backend):
        authority = RuntimeAuthority()
        gateway = ExternalAgentGateway(
            UniversalAgentInterface(backend),
            runtime_authority=authority,
        )
        gateway.connect()

        request = ExternalAgentRequest(
            task_id="c3-failure-task",
            payload="c3 failure task",
        )
        gateway.create_task(request)
        gateway.submit_task(request, ())
        gateway.start(request)

        return authority, gateway, request

    def test_start_backend_failure_rolls_authority_back(self):
        authority = RuntimeAuthority()
        gateway = ExternalAgentGateway(
            UniversalAgentInterface(_FailingStartBackend()),
            runtime_authority=authority,
        )
        gateway.connect()

        request = ExternalAgentRequest(
            task_id="c3-start-failure",
            payload="c3 start failure test",
        )
        gateway.create_task(request)
        gateway.submit_task(request, ())

        with self.assertRaises(RuntimeError):
            gateway.start(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.IDLE,
        )

    def test_pause_backend_failure_rolls_authority_back(self):
        authority, gateway, request = self._started_gateway(
            _FailingPauseBackend()
        )

        with self.assertRaises(RuntimeError):
            gateway.pause(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.RUNNING,
        )

    def test_resume_backend_failure_rolls_authority_back(self):
        authority, gateway, request = self._started_gateway(
            _FailingResumeBackend()
        )

        gateway.pause(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.PAUSED,
        )

        with self.assertRaises(RuntimeError):
            gateway.resume(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.PAUSED,
        )

    def test_stop_backend_failure_from_paused_restores_paused(self):
        authority, gateway, request = self._started_gateway(
            _FailingStopBackend()
        )

        gateway.pause(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.PAUSED,
        )

        with self.assertRaises(RuntimeError):
            gateway.stop(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.PAUSED,
        )

    def test_stop_backend_failure_rolls_authority_back(self):
        authority, gateway, request = self._started_gateway(
            _FailingStopBackend()
        )

        with self.assertRaises(RuntimeError):
            gateway.stop(request)

        self.assertEqual(
            authority.state(),
            RuntimeControlState.RUNNING,
        )

    def test_application_and_gateway_share_same_runtime_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(__file__).resolve().parents[1]
            storage = Path(temp)

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)
            context_agent = ProjectContextAgentInterface(context)

            workflow = AgentWorkflow(
                history_store=HistoryStore(storage / "history"),
                snapshot_service=SnapshotService(
                    root,
                    snapshot_directory=storage / "snapshots",
                ),
            )

            agent_service = AgentService(
                WorkflowService(workflow),
                project_context_agent=context_agent,
            )

            authority = RuntimeAuthority()

            execution_service = ApplicationExecutionService(
                agent_service,
                runtime_authority=authority,
            )

            gateway = ExternalAgentGateway(
                UniversalAgentInterface(_Backend()),
                runtime_authority=authority,
            )

            self.assertIs(
                execution_service.runtime_authority,
                gateway.runtime_authority,
            )

            authority.start()

            self.assertEqual(
                execution_service.runtime_state(),
                RuntimeControlState.RUNNING.value,
            )
            self.assertEqual(
                gateway.runtime_authority.view().state,
                RuntimeControlState.RUNNING,
            )

            execution_service.pause_runtime()

            self.assertEqual(
                gateway.runtime_authority.view().state,
                RuntimeControlState.PAUSED,
            )

            execution_service.resume_runtime()

            self.assertEqual(
                gateway.runtime_authority.view().state,
                RuntimeControlState.RUNNING,
            )

            execution_service.terminate_runtime()

            self.assertEqual(
                gateway.runtime_authority.view().state,
                RuntimeControlState.TERMINATED,
            )

    def test_external_and_vscode_share_runtime_authority(self):
        authority, gateway = self.make_gateway()
        bridge = ExternalAgentMessageBridge(gateway)
        server = ExternalAgentHTTPServer(bridge)
        server.start()

        request = ExternalAgentRequest(
            task_id="c3-shared-authority-task",
            payload="c3 shared runtime authority task",
        )

        try:
            gateway.create_task(request)
            gateway.submit_task(request, ())

            gateway.start(request)

            self.assertEqual(
                authority.state(),
                RuntimeControlState.RUNNING,
            )

            integration = VSCodeIntegration(endpoint=server.url)

            integration.send(
                command="pause",
                task_id=request.task_id,
                payload="",
            )

            self.assertEqual(
                authority.state(),
                RuntimeControlState.PAUSED,
            )
            self.assertEqual(
                gateway.inspect_runtime().state,
                RuntimeControlState.PAUSED,
            )

            http_view = integration.send(
                command="inspect_runtime",
                task_id=request.task_id,
                payload="",
            )
            self.assertIn("PAUSED", http_view.value)

            gateway.resume(request)

            self.assertEqual(
                authority.state(),
                RuntimeControlState.RUNNING,
            )

            http_view = integration.send(
                command="inspect_runtime",
                task_id=request.task_id,
                payload="",
            )
            self.assertIn("RUNNING", http_view.value)
        finally:
            server.shutdown()

    def test_http_runtime_query_reads_authority(self):
        authority, gateway = self.make_gateway()
        bridge = ExternalAgentMessageBridge(gateway)
        server = ExternalAgentHTTPServer(bridge)
        server.start()

        try:
            authority.start()

            integration = VSCodeIntegration(endpoint=server.url)
            result = integration.send(
                command="inspect_runtime",
                task_id="c3-http-runtime-query",
                payload="",
            )

            self.assertEqual(result.command, "inspect_runtime")
            self.assertEqual(result.task_id, "c3-http-runtime-query")
            self.assertEqual(
                gateway.runtime_authority.view().state,
                RuntimeControlState.RUNNING,
            )
            self.assertIn("RUNNING", result.value)
        finally:
            server.shutdown()

    def test_external_bridge_runtime_query_reads_authority(self):
        authority, gateway = self.make_gateway()
        bridge = ExternalAgentMessageBridge(gateway)

        authority.start()

        request = ExternalAgentRequest(
            task_id="c3-runtime-query",
            payload="",
        )

        result = bridge.dispatch(
            request,
            ExternalAgentCommand.INSPECT_RUNTIME,
        )

        self.assertEqual(
            gateway.runtime_authority.view().state,
            RuntimeControlState.RUNNING,
        )
        self.assertIs(
            gateway.runtime_authority,
            authority,
        )
        self.assertEqual(
            result.value.state,
            RuntimeControlState.RUNNING,
        )


if __name__ == "__main__":
    unittest.main()
