import tkinter as tk
import unittest

from ui.product_history import ProductGrowthEvent, ProductHistory
from ui.product_history_view import ProductHistoryView


class ProductHistoryViewM269Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def _event(
        self,
        event_id,
        date,
        title,
        version="M26",
        module="M26",
        category="visual experience",
        added="",
        changed="",
        fixed="",
        notes="",
    ):
        return ProductGrowthEvent(
            event_id=event_id,
            date=date,
            version=version,
            module=module,
            category=category,
            title=title,
            added=added or f"Added content for {title}.",
            changed=changed,
            fixed=fixed,
            notes=notes,
        )

    def _details(self, view):
        return view.details.get("1.0", tk.END)

    def test_view_renders_product_history_timeline(self):
        history = ProductHistory().extend(
            (
                self._event(
                    "older",
                    "2026-10-01",
                    "Opening Experience",
                    "M26.4",
                ),
                self._event(
                    "newer",
                    "2026-10-02",
                    "Unified Transition",
                    "M26.7",
                ),
            )
        )

        view = ProductHistoryView(self.root, history)

        self.assertEqual(
            view.heading.cget("text"),
            "PacePilot Growth History",
        )
        self.assertEqual(
            view.timeline.get(0),
            "2026-10-01  •  Opening Experience  •  M26.4",
        )
        self.assertEqual(
            view.timeline.get(1),
            "2026-10-02  •  Unified Transition  •  M26.7",
        )

        view.destroy()

    def test_view_uses_timeline_order_not_insertion_order(self):
        older = self._event(
            "older",
            "2026-10-01",
            "Older",
        )
        newer = self._event(
            "newer",
            "2026-10-02",
            "Newer",
        )

        history = ProductHistory().append(newer).append(older)
        view = ProductHistoryView(self.root, history)

        self.assertEqual(
            view.timeline.get(0),
            "2026-10-01  •  Older  •  M26",
        )
        self.assertEqual(
            view.timeline.get(1),
            "2026-10-02  •  Newer  •  M26",
        )

        view.destroy()

    def test_view_renders_cumulative_summary(self):
        history = ProductHistory().extend(
            (
                self._event(
                    "first",
                    "2026-10-01",
                    "Opening Experience",
                    "M26.4",
                ),
                self._event(
                    "second",
                    "2026-10-02",
                    "Unified Transition",
                    "M26.7",
                ),
            )
        )

        view = ProductHistoryView(self.root, history)

        self.assertEqual(
            view.summary.cget("text"),
            history.summary(),
        )

        view.destroy()

    def test_view_renders_selected_event_details(self):
        event = self._event(
            "details",
            "2026-10-02",
            "Unified Transition",
            "M26.7",
            module="M26",
            category="transitions",
            added="Established the unified transition system.",
            changed="Unified visual state transitions.",
            fixed="Fixed inconsistent transition behavior.",
            notes="Locked as M26.7.",
        )

        view = ProductHistoryView(
            self.root,
            ProductHistory().append(event),
        )

        details = self._details(view)

        self.assertIn("Unified Transition", details)
        self.assertIn("Date: 2026-10-02", details)
        self.assertIn("Version: M26.7", details)
        self.assertIn("Module: M26", details)
        self.assertIn("Category: transitions", details)
        self.assertIn("Added:", details)
        self.assertIn("Established the unified transition system.", details)
        self.assertIn("Changed:", details)
        self.assertIn("Unified visual state transitions.", details)
        self.assertIn("Fixed:", details)
        self.assertIn("Fixed inconsistent transition behavior.", details)
        self.assertIn("Notes:", details)
        self.assertIn("Locked as M26.7.", details)

        view.destroy()

    def test_selection_changes_event_details(self):
        first = self._event(
            "first",
            "2026-10-01",
            "Opening Experience",
            "M26.4",
        )
        second = self._event(
            "second",
            "2026-10-02",
            "Unified Transition",
            "M26.7",
        )

        view = ProductHistoryView(
            self.root,
            ProductHistory().extend((first, second)),
        )

        view.timeline.selection_clear(0)
        view.timeline.selection_set(1)
        view._on_selection()

        details = self._details(view)

        self.assertIn("Unified Transition", details)
        self.assertIn("Version: M26.7", details)
        self.assertNotIn("Opening Experience", details)

        view.destroy()

    def test_refresh_replaces_rendered_history_and_summary(self):
        first = ProductHistory().append(
            self._event(
                "first",
                "2026-10-01",
                "First",
            )
        )
        second = ProductHistory().append(
            self._event(
                "second",
                "2026-10-02",
                "Second",
                "M26.7",
            )
        )

        view = ProductHistoryView(self.root, first)
        view.refresh(second)

        self.assertEqual(view.timeline.size(), 1)
        self.assertEqual(
            view.timeline.get(0),
            "2026-10-02  •  Second  •  M26.7",
        )
        self.assertEqual(
            view.summary.cget("text"),
            second.summary(),
        )
        self.assertIn("Second", self._details(view))

        view.destroy()


if __name__ == "__main__":
    unittest.main()
