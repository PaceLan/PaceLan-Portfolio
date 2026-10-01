import json
import tempfile
import unittest
from pathlib import Path

from ui.product_history import (
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
        kind="milestone",
        title="Visual experience system",
        description="Established the product visual experience foundation.",
        version="M26",
    ):
        return ProductGrowthEvent(
            event_id=event_id,
            date=date,
            kind=kind,
            title=title,
            description=description,
            version=version,
        )

    def test_event_is_structured_and_serializable(self):
        event = self._event()

        self.assertEqual(event.kind, "milestone")
        self.assertEqual(
            event.to_dict(),
            {
                "event_id": "m26-001",
                "date": "2026-10-01",
                "kind": "milestone",
                "title": "Visual experience system",
                "description": "Established the product visual experience foundation.",
                "version": "M26",
            },
        )
        json.dumps(event.to_dict())

    def test_empty_history_has_no_latest_event(self):
        history = ProductHistory()

        self.assertEqual(history.events(), ())
        self.assertIsNone(history.latest())

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

    def test_history_file_contains_only_product_history_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product_history.json"
            history = ProductHistory().append(self._event())

            ProductHistoryStore(path).save(history)

            payload = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.assertEqual(
                set(payload),
                {"version", "events"},
            )
            self.assertEqual(
                set(payload["events"][0]),
                {
                    "event_id",
                    "date",
                    "kind",
                    "title",
                    "description",
                    "version",
                },
            )

    def test_product_history_path_is_dedicated(self):
        path = product_history_path("C:/Temp/PacePilot")

        self.assertEqual(
            path,
            Path("C:/Temp/PacePilot") / "product_history.json",
        )


if __name__ == "__main__":
    unittest.main()
