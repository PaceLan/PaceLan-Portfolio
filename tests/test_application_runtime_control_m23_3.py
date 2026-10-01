import unittest

from application.runtime_control import (
    ApplicationRuntimeControlService,
    RuntimeControlState,
)


class _Target:
    def __init__(self):
        self._state = "RUNNING"
        self.actions = []

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


class ApplicationRuntimeControlM233Tests(unittest.TestCase):
    def setUp(self):
        self.target = _Target()
        self.service = ApplicationRuntimeControlService(self.target)

    def test_pause(self):
        result = self.service.pause()
        self.assertEqual(result.state, RuntimeControlState.PAUSED)
        self.assertTrue(result.accepted)
        self.assertEqual(self.target.actions, ["pause"])

    def test_resume(self):
        self.service.pause()
        result = self.service.resume()
        self.assertEqual(result.state, RuntimeControlState.RUNNING)
        self.assertEqual(self.target.actions, ["pause", "resume"])

    def test_terminate_is_distinct_from_failure(self):
        result = self.service.terminate()
        self.assertEqual(result.state, RuntimeControlState.TERMINATED)
        self.assertNotEqual(result.state.value, "FAILED")

    def test_status(self):
        result = self.service.status()
        self.assertEqual(result.state, RuntimeControlState.RUNNING)


if __name__ == "__main__":
    unittest.main()
