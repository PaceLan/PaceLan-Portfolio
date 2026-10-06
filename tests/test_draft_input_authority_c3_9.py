import unittest

from application.draft_input_authority import (
    DraftInput,
    DraftInputAuthority,
    DraftInputKind,
)


class DraftInputAuthorityC391Tests(unittest.TestCase):
    def setUp(self):
        self.authority = DraftInputAuthority()

    def test_accept_creates_draft_input(self):
        item = self.authority.accept(
            "  inspect the authentication flow  ",
            kind=DraftInputKind.IDEA,
            source="external_agent",
        )

        self.assertIsInstance(item, DraftInput)
        self.assertEqual(item.content, "inspect the authentication flow")
        self.assertEqual(item.kind, DraftInputKind.IDEA)
        self.assertEqual(item.source, "external_agent")

    def test_draft_input_has_no_execution_authority(self):
        item = self.authority.accept("Implement feature")

        self.assertFalse(
            self.authority.can_enter_formal_execution(item)
        )

    def test_draft_input_requires_goal_confirmation(self):
        item = self.authority.accept("Implement feature")

        self.assertTrue(
            self.authority.requires_goal_confirmation(item)
        )

    def test_empty_content_is_rejected(self):
        with self.assertRaises(ValueError):
            self.authority.accept(" ")

    def test_empty_source_is_rejected(self):
        with self.assertRaises(ValueError):
            self.authority.accept("Implement feature", source=" ")

    def test_default_kind_is_draft(self):
        item = self.authority.accept("Implement feature")

        self.assertEqual(item.kind, DraftInputKind.DRAFT)


if __name__ == "__main__":
    unittest.main()
