import unittest
from pathlib import Path

from application.bootstrap import ApplicationRuntime
from application.runtime_authority import RuntimeAuthority
from application.services import ApplicationExecutionService
from application.unified_control_loop import UnifiedControlLoop


class C3FinalBoundaryC314Tests(unittest.TestCase):

    def test_bootstrap_owns_the_single_runtime_authority(self):
        source = Path("application/bootstrap.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("RuntimeAuthority()"), 1)

    def test_execution_service_requires_runtime_authority(self):
        with self.assertRaises(TypeError):
            ApplicationExecutionService(None)

    def test_control_loop_requires_shared_runtime_authority(self):
        authority = RuntimeAuthority()
        service = object.__new__(ApplicationExecutionService)
        service._runtime_authority = authority

        loop = UnifiedControlLoop.__new__(UnifiedControlLoop)
        loop._execution_service = service
        loop._runtime_authority = authority

        self.assertIs(loop.runtime_authority, service.runtime_authority)

    def test_production_application_has_one_shared_authority(self):
        runtime = ApplicationRuntime
        self.assertIn("runtime_authority", runtime.__dataclass_fields__)
        self.assertIn("control_loop", runtime.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
