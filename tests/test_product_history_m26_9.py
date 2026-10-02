import json
import tempfile
import unittest
from pathlib import Path

from ui.product_history import (
    PRODUCT_GROWTH_EVENTS,
    ProductGrowthEvent,
    ProductHistory,
    ProductHistoryStore,
    product_history_path,
)


class ProductHistoryM269Tests(unittest.TestCase):

    def _event(
        self,
        event_id="m26-001",
        date="2026-10-01",
        version="M26",
        module="M26",
        category="visual experience",
        title="Visual experience system",
        added="Established the product visual experience foundation.",
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
            added=added,
            changed=changed,
            fixed=fixed,
            notes=notes,
        )

    def test_event_is_structured_and_serializable(self):
        event = self._event(
            changed="Improved visual continuity.",
            fixed="Fixed transition inconsistencies.",
            notes="Recorded as a product milestone.",
        )

        self.assertEqual(event.version, "M26")
        self.assertEqual(event.module, "M26")
        self.assertEqual(event.category, "visual experience")
        self.assertEqual(
            event.to_dict(),
            {
                "event_id": "m26-001",
                "date": "2026-10-01",
                "version": "M26",
                "module": "M26",
                "category": "visual experience",
                "title": "Visual experience system",
                "added": "Established the product visual experience foundation.",
                "changed": "Improved visual continuity.",
                "fixed": "Fixed transition inconsistencies.",
                "notes": "Recorded as a product milestone.",
            },
        )
        json.dumps(event.to_dict())

    def test_description_is_derived_from_structured_content(self):
        event = self._event(
            added="Added the foundation.",
            changed="Changed the interaction flow.",
            fixed="Fixed visual inconsistencies.",
            notes="Kept the history deterministic.",
        )

        self.assertEqual(
            event.description,
            "Added the foundation. Changed the interaction flow. "
            "Fixed visual inconsistencies. Kept the history deterministic.",
        )

    def test_empty_history_has_no_latest_event(self):
        history = ProductHistory()

        self.assertEqual(history.events(), ())
        self.assertIsNone(history.latest())
        self.assertEqual(
            history.summary(),
            "PacePilot has no recorded product growth yet.",
        )

    def test_append_preserves_event_order(self):
        first = self._event(event_id="m25", version="M25")
        second = self._event(event_id="m26", version="M26")

        history = ProductHistory().append(first).append(second)

        self.assertEqual(history.events(), (first, second))
        self.assertEqual(history.latest(), second)

    def test_latest_is_based_on_history_date(self):
        newer = self._event(
            event_id="newer",
            date="2026-10-02",
        )
        older = self._event(
            event_id="older",
            date="2026-10-01",
        )

        history = ProductHistory().append(newer).append(older)

        self.assertEqual(history.latest(), newer)

    def test_from_events_creates_product_history(self):
        first = self._event(event_id="m25", version="M25")
        second = self._event(event_id="m26", version="M26")

        history = ProductHistory.from_events((first, second))

        self.assertEqual(history.events(), (first, second))

    def test_duplicate_event_id_replaces_existing_event(self):
        first = self._event(title="Original")
        replacement = self._event(title="Updated")

        history = ProductHistory().append(first).append(replacement)

        self.assertEqual(history.events(), (replacement,))

    def test_events_can_be_filtered_by_version(self):
        m25 = self._event(event_id="m25", version="M25")
        m26 = self._event(event_id="m26", version="M26")

        history = ProductHistory.from_events((m25, m26))

        self.assertEqual(
            history.events_for_version("M26"),
            (m26,),
        )

    def test_events_can_be_filtered_by_module(self):
        visual = self._event(
            event_id="visual",
            module="M26",
        )
        runtime = self._event(
            event_id="runtime",
            module="M25",
        )

        history = ProductHistory.from_events((visual, runtime))

        self.assertEqual(
            history.events_for_module("M26"),
            (visual,),
        )

    def test_summary_describes_cumulative_history(self):
        first = self._event(
            event_id="first",
            version="M25",
            title="Runtime foundation",
        )
        second = self._event(
            event_id="second",
            version="M26",
            date="2026-10-02",
            title="Unified transition",
        )

        history = ProductHistory.from_events((first, second))

        self.assertEqual(
            history.summary(),
            "PacePilot has recorded 2 product milestones "
            "across 2 versions. The latest recorded milestone is "
            "Unified transition (M26), dated 2026-10-02.",
        )

    def test_history_round_trips_through_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product_history.json"
            store = ProductHistoryStore(path)

            history = ProductHistory().append(self._event())
            store.save(history)

            restored = store.load()

            self.assertEqual(restored, history)

    def test_missing_file_returns_empty_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ProductHistoryStore(
                Path(directory) / "missing.json"
            )

            self.assertEqual(store.load(), ProductHistory())

    def test_invalid_json_raises_explicit_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product_history.json"
            path.write_text("{not valid json", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "invalid product history JSON",
            ):
                ProductHistoryStore(path).load()

    def test_unsupported_schema_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product_history.json"
            path.write_text(
                json.dumps({"version": 999, "events": []}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "unsupported product history version",
            ):
                ProductHistoryStore(path).load()

    def test_history_file_contains_structured_product_history_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product_history.json"
            history = ProductHistory().append(
                self._event(
                    changed="Changed the interaction model.",
                    fixed="Fixed visual inconsistencies.",
                    notes="Product-level historical record.",
                )
            )

            ProductHistoryStore(path).save(history)

            payload = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.assertEqual(
                set(payload),
                {"version", "events"},
            )
            self.assertEqual(
                payload["version"],
                ProductHistoryStore.SCHEMA_VERSION,
            )
            self.assertEqual(
                set(payload["events"][0]),
                {
                    "event_id",
                    "date",
                    "version",
                    "module",
                    "category",
                    "title",
                    "added",
                    "changed",
                    "fixed",
                    "notes",
                },
            )

    def test_product_history_path_is_dedicated(self):
        path = product_history_path("C:/Temp/PacePilot")

        self.assertEqual(
            path,
            Path("C:/Temp/PacePilot") / "product_history.json",
        )

    def test_real_product_growth_events_are_structured(self):
        self.assertGreaterEqual(len(PRODUCT_GROWTH_EVENTS), 1)

        for event in PRODUCT_GROWTH_EVENTS:
            self.assertTrue(event.version)
            self.assertTrue(event.module)
            self.assertTrue(event.category)
            self.assertTrue(event.title)

    def test_real_product_growth_events_are_chronological(self):
        history = ProductHistory.from_events(PRODUCT_GROWTH_EVENTS)

        self.assertEqual(
            history.timeline(),
            tuple(
                sorted(
                    PRODUCT_GROWTH_EVENTS,
                    key=lambda event: (event.date, event.event_id),
                )
            ),
        )

        self.assertEqual(
            history.latest().version,
            "M26.7",
        )


if __name__ == "__main__":
    unittest.main()
    def test_missing_required_event_field_is_rejected(self):
        payload = {
            "event_id": "missing-title",
            "date": "2026-10-02",
            "version": "M26.7",
            "module": "M26",
            "category": "transitions",
        }

        with self.assertRaisesRegex(
            ValueError,
            "missing product growth event fields: title",
        ):
            ProductGrowthEvent.from_dict(payload)

    def test_non_string_required_event_field_is_rejected(self):
        payload = {
            "event_id": "invalid-title",
            "date": "2026-10-02",
            "version": "M26.7",
            "module": "M26",
            "category": "transitions",
            "title": 123,
        }

        with self.assertRaisesRegex(
            ValueError,
            "title must not be empty",
        ):
            ProductGrowthEvent.from_dict(payload)
