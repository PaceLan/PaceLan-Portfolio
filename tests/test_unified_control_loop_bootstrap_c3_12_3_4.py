from pathlib import Path
import tempfile
import unittest

from application.bootstrap import ApplicationBootstrap, ApplicationRuntime
from application.runtime_authority import RuntimeControlState


class UnifiedControlLoopBootstrapC31234Tests(unittest.TestCase):
    def test_bootstrap_shares_one_runtime_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = ApplicationBootstrap.create(Path(tmp))

            self.assertIsInstance(runtime, ApplicationRuntime)
            self.assertIs(
                runtime.control_loop.runtime_authority,
                runtime.runtime_authority,
            )
            self.assertIs(
                runtime.execution_service.runtime_authority,
                runtime.runtime_authority,
            )

    def test_control_loop_does_not_own_duplicate_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = ApplicationBootstrap.create(Path(tmp))
            loop = runtime.control_loop

            self.assertIs(
                loop.runtime_authority,
                runtime.runtime_authority,
            )
            self.assertEqual(
                runtime.runtime_authority.state(),
                RuntimeControlState.IDLE,
            )

            self.assertNotIn("_runtime_state", vars(loop))

    def test_control_loop_commands_change_shared_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = ApplicationBootstrap.create(Path(tmp))
            loop = runtime.control_loop

            loop.runtime_authority.start()
            self.assertEqual(
                runtime.execution_service.runtime_state(),
                RuntimeControlState.RUNNING.value,
            )

            loop.pause()
            self.assertEqual(
                runtime.runtime_authority.state(),
                RuntimeControlState.PAUSED,
            )

            loop.resume()
            self.assertEqual(
                runtime.runtime_authority.state(),
                RuntimeControlState.RUNNING,
            )

            loop.stop()
            self.assertEqual(
                runtime.runtime_authority.state(),
                RuntimeControlState.TERMINATED,
            )

    def test_control_loop_is_application_runtime_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = ApplicationBootstrap.create(Path(tmp))

            self.assertIsNotNone(runtime.control_loop)
            self.assertTrue(callable(runtime.control_loop.start))
            self.assertTrue(callable(runtime.control_loop.pause))
            self.assertTrue(callable(runtime.control_loop.resume))
            self.assertTrue(callable(runtime.control_loop.stop))
            self.assertTrue(callable(runtime.control_loop.inspect))
            self.assertTrue(callable(runtime.control_loop.wait))


if __name__ == "__main__":
    unittest.main()
