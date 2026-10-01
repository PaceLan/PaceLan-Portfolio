import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from ui.daily_greeting import (
    GREETINGS,
    DailyGreetingService,
    Greeting,
    greeting_history_path,
)


class DailyGreetingM265Tests(unittest.TestCase):

    def test_has_at_least_fifty_greetings(self):
        self.assertGreaterEqual(len(GREETINGS), 50)

    def test_greetings_have_categories(self):
        categories = {item.category for item in GREETINGS}
        self.assertGreaterEqual(
            categories,
            {"morning", "focus", "creative", "agent", "calm"},
        )

    def test_greetings_are_structured(self):
        self.assertTrue(
            all(
                isinstance(item, Greeting)
                and item.text.strip()
                and item.category.strip()
                for item in GREETINGS
            )
        )

    def test_same_day_is_stable_without_history(self):
        service = DailyGreetingService(history_limit=0)
        day = date(2026, 10, 1)

        first = service.greeting_for_date(day)
        second = service.greeting_for_date(day)

        self.assertEqual(first, second)

    def test_different_days_can_resolve_different_greetings(self):
        service = DailyGreetingService(history_limit=0)

        values = {
            service.greeting_for_date(
                date(2026, 10, 1) + timedelta(days=index)
            ).text
            for index in range(10)
        }

        self.assertGreater(len(values), 1)

    def test_recent_history_avoids_immediate_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            service = DailyGreetingService(history_path=path)

            first_day = date(2026, 10, 1)
            second_day = first_day + timedelta(days=1)

            first = service.greeting_for_date(first_day)
            second = service.greeting_for_date(second_day)

            self.assertNotEqual(first.text, second.text)

    def test_same_day_does_not_duplicate_history_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            service = DailyGreetingService(history_path=path)

            day = date(2026, 10, 1)
            service.greeting_for_date(day)
            service.greeting_for_date(day)

            payload = path.read_text(encoding="utf-8")
            self.assertEqual(payload.count('"date": "2026-10-01"'), 1)

    def test_history_survives_new_service_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            day = date(2026, 10, 1)

            first_service = DailyGreetingService(history_path=path)
            first = first_service.greeting_for_date(day)

            second_service = DailyGreetingService(history_path=path)
            second = second_service.greeting_for_date(day)

            self.assertEqual(first, second)

    def test_history_path_defaults_to_pacepilot_data_location(self):
        path = greeting_history_path(
            base_directory="C:/Temp/PacePilot"
        )
        self.assertEqual(
            path,
            Path("C:/Temp/PacePilot") / "greeting_history.json",
        )


if __name__ == "__main__":
    unittest.main()
