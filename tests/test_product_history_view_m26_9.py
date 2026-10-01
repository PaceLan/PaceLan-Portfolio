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
    ):
        return ProductGrowthEvent(
            event_id=event_id,
            date=date,
            kind="milestone",
            title=title,
            description=f"Description for {title}.",
            version=version,
        )

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
            "2026-10-01 ? Opening Experience ? M26.4",
        )
        self.assertEqual(
            view.timeline.get(1),
            "2026-10-02 ? Unified Transition ? M26.7",
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
            "2026-10-01 ? Older ? M26",
        )
        self.assertEqual(
            view.timeline.get(1),
            "2026-10-02 ? Newer ? M26",
        )

        view.destroy()

    def test_refresh_replaces_rendered_history(self):
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
            "2026-10-02 ? Second ? M26.7",
        )

        view.destroy()


if __name__ == "__main__":
    unittest.main()
