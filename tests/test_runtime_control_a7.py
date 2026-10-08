import unittest

from application.runtime_control import (
    ApplicationRuntimeControlService,
    RuntimeControlResult,
    RuntimeControlState,
)


class _Target:
    def __init__(self):
        self._state = "IDLE"
        self.actions = []

    def start_runtime(self):
        self.actions.append("start")
        self._state = "RUNNING"

    def pause_runtime(self):
        self.actions.append("pause")
        self._state = "PAUSED"

    def resume_runtime(self):
        self.actions.append("resume")
        self._state = "RUNNING"

    def terminate_runtime(self):
        self.actions.append("terminate")
        self._state = "TERMINATED"

    def runtime_state(self):
        return self._state


class RuntimeControlA7Tests(unittest.TestCase):
    def setUp(self):
        self.target = _Target()
        self.service = ApplicationRuntimeControlService(self.target)

    def test_start_transitions_idle_to_running(self):
        result = self.service.start()

        self.assertIsInstance(result, RuntimeControlResult)
        self.assertEqual(result.action, "start")
        self.assertEqual(result.state, RuntimeControlState.RUNNING)
        self.assertTrue(result.accepted)
        self.assertEqual(self.target.actions, ["start"])

    def test_pause_transitions_running_to_paused(self):
        self.service.start()

        result = self.service.pause()

        self.assertEqual(result.action, "pause")
        self.assertEqual(result.state, RuntimeControlState.PAUSED)
        self.assertTrue(result.accepted)

    def test_resume_transitions_paused_to_running(self):
        self.service.start()
        self.service.pause()

        result = self.service.resume()

        self.assertEqual(result.action, "resume")
        self.assertEqual(result.state, RuntimeControlState.RUNNING)
        self.assertTrue(result.accepted)

    def test_terminate_transitions_to_terminated(self):
        self.service.start()

        result = self.service.terminate()

        self.assertEqual(result.action, "terminate")
        self.assertEqual(result.state, RuntimeControlState.TERMINATED)
        self.assertTrue(result.accepted)

    def test_status_is_observation_only(self):
        self.service.start()
        self.target.actions.clear()

        result = self.service.status()

        self.assertEqual(result.action, "status")
        self.assertEqual(result.state, RuntimeControlState.RUNNING)
        self.assertTrue(result.accepted)
        self.assertEqual(self.target.actions, [])

    def test_control_sequence(self):
        self.service.start()
        self.service.pause()
        self.service.resume()
        self.service.terminate()

        self.assertEqual(
            self.target.actions,
            ["start", "pause", "resume", "terminate"],
        )

    def test_result_is_immutable(self):
        result = self.service.status()

        with self.assertRaises(AttributeError):
            result.action = "changed"


if __name__ == "__main__":
    unittest.main()
