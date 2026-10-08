import unittest

from application.universal_agent_runtime_target import UniversalAgentRuntimeTarget


class _Agent:
    def __init__(self):
        self.actions = []
        self.state = "IDLE"

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
        return View(self.state)


class UniversalAgentRuntimeTargetA73Tests(unittest.TestCase):
    def setUp(self):
        self.agent = _Agent()
        self.target = UniversalAgentRuntimeTarget(self.agent, "task-1")

    def test_start(self):
        self.target.start_runtime()
        self.assertEqual(self.agent.actions, [("start", "task-1")])
        self.assertEqual(self.target.runtime_state(), "RUNNING")

    def test_pause_resume(self):
        self.target.start_runtime()
        self.target.pause_runtime()
        self.assertEqual(self.target.runtime_state(), "PAUSED")

        self.target.resume_runtime()
        self.assertEqual(self.target.runtime_state(), "RUNNING")

    def test_terminate_maps_stopped_to_terminated(self):
        self.target.start_runtime()
        self.target.terminate_runtime()
        self.assertEqual(self.target.runtime_state(), "TERMINATED")

    def test_control_sequence(self):
        self.target.start_runtime()
        self.target.pause_runtime()
        self.target.resume_runtime()
        self.target.terminate_runtime()

        self.assertEqual(
            self.agent.actions,
            [
                ("start", "task-1"),
                ("pause", "task-1"),
                ("resume", "task-1"),
                ("stop", "task-1"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
