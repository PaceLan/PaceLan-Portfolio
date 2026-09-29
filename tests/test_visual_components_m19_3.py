import unittest


class VisualComponentsM193Tests(unittest.TestCase):
    def test_component_module_exists(self):
        from ui.visual_components import (
            Navigation,
            Panel,
            State,
            Status,
            Workspace,
        )

        for component in (
            Panel,
            Navigation,
            Status,
            Workspace,
            State,
        ):
            self.assertIsNotNone(component)

    def test_components_expose_visual_role(self):
        from ui.visual_components import (
            Navigation,
            Panel,
            State,
            Status,
            Workspace,
        )

        for component in (
            Panel,
            Navigation,
            Status,
            Workspace,
            State,
        ):
            self.assertTrue(hasattr(component, "visual_role"))

    def test_components_are_immutable(self):
        from ui.visual_components import Panel

        component = Panel()

        with self.assertRaises((AttributeError, TypeError)):
            component.visual_role = "changed"

    def test_component_roles_are_distinct(self):
        from ui.visual_components import (
            Navigation,
            Panel,
            State,
            Status,
            Workspace,
        )

        roles = {
            Panel().visual_role,
            Navigation().visual_role,
            Status().visual_role,
            Workspace().visual_role,
            State().visual_role,
        }

        self.assertEqual(len(roles), 5)


if __name__ == "__main__":
    unittest.main()
