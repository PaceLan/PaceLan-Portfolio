import unittest
from unittest import mock
from concurrent.futures import Future

from application.models import TaskModel
from application.runtime_authority import RuntimeAuthority
from application.services import ApplicationExecutionService
from application.unified_control_loop import UnifiedControlLoop


class _ExecutionServiceStub:
    def __init__(self, authority):
        self._authority = authority
        self.calls = []
        self.future = Future()

    @property
    def runtime_authority(self):
        return self._authority

    def start(self, task, steps=()):
        self.calls.append(("start", task.task_id, tuple(steps)))
        return self.future

    def pause(self):
        self.calls.append(("pause",))
        return "paused"

    def resume(self):
        self.calls.append(("resume",))
        return "resumed"

    def terminate(self):
        self.calls.append(("terminate",))
        return "terminated"

    def runtime_status(self):
        self.calls.append(("inspect",))
        return "status"


class UnifiedControlLoopC3123Tests(unittest.TestCase):
    def make_loop(self):
        authority = RuntimeAuthority()
        service = mock.Mock(spec=ApplicationExecutionService)
        service.runtime_authority = authority
        service.future = Future()
        service.start.return_value = service.future
        service.pause.return_value = "paused"
        service.resume.return_value = "resumed"
        service.terminate.return_value = "terminated"
        service.runtime_status.return_value = "status"
        loop = UnifiedControlLoop(service, authority)
        return authority, service, loop

    def test_uses_same_runtime_authority(self):
        authority, service, loop = self.make_loop()

        self.assertIs(loop.runtime_authority, authority)
        self.assertIs(loop.execution_service, service)
        self.assertIs(
            loop.execution_service.runtime_authority,
            loop.runtime_authority,
        )

    def test_start_delegates_without_creating_runtime_state(self):
        _, service, loop = self.make_loop()
        task = TaskModel(
            task_id="task-1",
            project_id="project-1",
            description="test",
        )

        future = loop.start(task)

        self.assertIs(future, service.future)
        service.start.assert_called_once_with(task, ())

    def test_runtime_controls_delegate(self):
        _, service, loop = self.make_loop()

        self.assertEqual(loop.pause(), "paused")
        self.assertEqual(loop.resume(), "resumed")
        self.assertEqual(loop.stop(), "terminated")
        self.assertEqual(loop.inspect(), "status")

        service.pause.assert_called_once_with()
        service.resume.assert_called_once_with()
        service.terminate.assert_called_once_with()
        service.runtime_status.assert_called_once_with()

    def test_wait_returns_future_result(self):
        _, _, loop = self.make_loop()
        expected = object()
        future = Future()
        future.set_result(expected)

        self.assertIs(loop.wait(future), expected)

    def test_wait_requires_future(self):
        _, _, loop = self.make_loop()

        with self.assertRaises(TypeError):
            loop.wait(object())

    def test_rejects_different_runtime_authority(self):
        service = mock.Mock(spec=ApplicationExecutionService)
        service.runtime_authority = RuntimeAuthority()

        with self.assertRaises(ValueError):
            UnifiedControlLoop(
                service,
                RuntimeAuthority(),
            )


if __name__ == "__main__":
    unittest.main()
