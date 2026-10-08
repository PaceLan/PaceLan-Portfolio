import unittest

from application.agent_runtime_control import AgentRuntimeControlService
from application.runtime_control import RuntimeControlState


class _Agent:
    def __init__(self):
        self.state = "IDLE"
        self.actions = []

    def start(self, task_id):
        self.actions.append(("start", task_id))
        self.state = "RUNNING"

    def pause(self, task_id):
        self.actions.append(("pause", task_id))
        self.state = "PAUSED"

    def resume(self, task_id):
        self.actions.append(("resume", task_id))
        self.state = "RUNNING"

    def stop(self, task_id):
        self.actions.append(("stop", task_id))
        self.state = "STOPPED"

    def inspect_runtime(self):
        class View:
            def __init__(self, state):
                self.state = type("State", (), {"value": state})()
                self.accepted = True
                self.message = ""
        return View(self.state)


class AgentRuntimeControlA74Tests(unittest.TestCase):
    def setUp(self):
        self.agent = _Agent()
        self.service = AgentRuntimeControlService(
            self.agent,
            "task-1",
        )

    def test_full_control_lifecycle(self):
        self.assertEqual(
            self.service.start().state,
            RuntimeControlState.RUNNING,
        )
        self.assertEqual(
            self.service.pause().state,
            RuntimeControlState.PAUSED,
        )
        self.assertEqual(
            self.service.resume().state,
            RuntimeControlState.RUNNING,
        )
        self.assertEqual(
            self.service.terminate().state,
            RuntimeControlState.TERMINATED,
        )

        self.assertEqual(
            self.agent.actions,
            [
                ("start", "task-1"),
                ("pause", "task-1"),
                ("resume", "task-1"),
                ("stop", "task-1"),
            ],
        )

    def test_status_is_observation(self):
        result = self.service.status()

        self.assertEqual(result.action, "status")
        self.assertEqual(result.state, RuntimeControlState.IDLE)
        self.assertTrue(result.accepted)
        self.assertEqual(self.agent.actions, [])


if __name__ == "__main__":
    unittest.main()
