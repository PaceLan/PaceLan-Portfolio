import sys
import unittest

from application.process_lifecycle import ProcessLifecycleState
from application.process_lifecycle_controller import ProcessLifecycleController


class ProcessLifecycleControllerC44Tests(unittest.TestCase):
    def test_start_creates_real_process_and_pid(self):
        controller = ProcessLifecycleController()

        snapshot = controller.start(
            sys.executable,
            ("-c", "print('ok')"),
        )

        self.assertIsInstance(snapshot.process_id, int)
        self.assertGreater(snapshot.process_id, 0)
        self.assertEqual(snapshot.state, ProcessLifecycleState.RUNNING)

        controller.process.wait()

    def test_running_process_remains_running(self):
        controller = ProcessLifecycleController()
        controller.start(
            sys.executable,
            ("-c", "import time; time.sleep(0.3)"),
        )

        try:
            current = controller.snapshot()
            self.assertEqual(current.state, ProcessLifecycleState.RUNNING)
            self.assertIsNone(current.exit_code)
        finally:
            controller.process.terminate()
            controller.process.wait()
    def test_terminate_stops_running_process(self):
        controller = ProcessLifecycleController()
        controller.start(
            sys.executable,
            ("-c", "import time; time.sleep(30)"),
        )

        snapshot = controller.terminate()

        self.assertIsNotNone(snapshot.process_id)
        self.assertEqual(snapshot.state, ProcessLifecycleState.FAILED)
        self.assertIsNotNone(snapshot.exit_code)
        self.assertIsNotNone(snapshot.finished_at)

    def test_successful_process_becomes_exited(self):
        controller = ProcessLifecycleController()
        controller.start(sys.executable, ("-c", "pass"))

        controller.process.wait()
        snapshot = controller.snapshot()

        self.assertEqual(snapshot.state, ProcessLifecycleState.EXITED)
        self.assertEqual(snapshot.exit_code, 0)
        self.assertIsNotNone(snapshot.finished_at)

    def test_nonzero_process_becomes_failed(self):
        controller = ProcessLifecycleController()
        controller.start(sys.executable, ("-c", "raise SystemExit(3)"))

        controller.process.wait()
        snapshot = controller.snapshot()

        self.assertEqual(snapshot.state, ProcessLifecycleState.FAILED)
        self.assertEqual(snapshot.exit_code, 3)

    def test_missing_executable_becomes_failed(self):
        controller = ProcessLifecycleController()

        with self.assertRaises(FileNotFoundError):
            controller.start(
                "__pacepilot_missing_executable__",
            )

        self.assertEqual(
            controller.snapshot().state,
            ProcessLifecycleState.FAILED,
        )


if __name__ == "__main__":
    unittest.main()
