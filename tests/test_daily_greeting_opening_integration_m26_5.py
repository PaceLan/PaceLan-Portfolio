import unittest
from pathlib import Path


class DailyGreetingOpeningIntegrationM265Tests(unittest.TestCase):
    def test_daily_greeting_import(self):
        source = (Path("ui") / "app_entry.py").read_text(encoding="utf-8")
        self.assertIn(
            "from ui.daily_greeting import DailyGreetingService, greeting_history_path",
            source,
        )

    def test_daily_greeting_resolved(self):
        source = (Path("ui") / "app_entry.py").read_text(encoding="utf-8")
        self.assertIn("greeting_service = DailyGreetingService(", source)
        self.assertIn("daily_greeting = greeting_service.today_text()", source)

    def test_greeting_passed_to_opening(self):
        source = (Path("ui") / "app_entry.py").read_text(encoding="utf-8")
        self.assertIn(
            "config=OpeningConfig(greeting=daily_greeting)",
            source,
        )

    def test_opening_interface_preserved(self):
        source = (Path("ui") / "opening_experience.py").read_text(encoding="utf-8")
        self.assertIn("config: OpeningConfig | None = None", source)
        self.assertIn('greeting: str = "Welcome back"', source)


if __name__ == "__main__":
    unittest.main()
