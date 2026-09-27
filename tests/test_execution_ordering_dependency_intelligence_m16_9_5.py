import unittest


class ExecutionOrderingDependencyIntelligenceTests(unittest.TestCase):
    def test_module_imports(self):
        from agent_workflow import execution_ordering
        from agent_workflow import dependency_graph

        self.assertIsNotNone(execution_ordering)
        self.assertIsNotNone(dependency_graph)


if __name__ == "__main__":
    unittest.main()
