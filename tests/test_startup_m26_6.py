from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from ui.startup import StartupCoordinator


class StartupCoordinatorM266Tests(unittest.TestCase):

    def test_start_opens_before_remaining_startup_work(self):
        root = Mock()
        coordinator = StartupCoordinator(root, runtime_root="runtime")

        events = []
        fake_runtime = Mock()
        fake_app = Mock()
        fake_opening = Mock()

        def create_runtime(*args, **kwargs):
            events.append("runtime")
            return fake_runtime

        app_calls = []

        def create_app(*args, **kwargs):
            events.append("visual")
            app_calls.append((args, kwargs))
            return fake_app

        def create_opening(*args, **kwargs):
            events.append("opening")
            fake_opening.start.side_effect = lambda: events.append("opening.start")
            return fake_opening

        with patch("ui.startup.ApplicationBootstrap.create", side_effect=create_runtime), \
             patch("ui.startup.CodingAssistantApp", side_effect=create_app), \
             patch("ui.startup.OpeningExperience", side_effect=create_opening):
            coordinator.start()

        self.assertEqual(
            events,
            ["runtime", "visual", "opening", "opening.start"],
        )
        root.after_idle.assert_called_once()
        self.assertEqual(len(app_calls), 1)
        self.assertIs(
            app_calls[0][1]["execution_service"],
            fake_runtime.execution_service,
        )
        self.assertIs(
            app_calls[0][1]["agent_service"],
            fake_runtime.agent_service,
        )

    def test_initialization_continues_through_event_loop(self):
        root = Mock()
        coordinator = StartupCoordinator(root, runtime_root="runtime")

        fake_runtime = Mock()
        fake_app = Mock()
        fake_opening = Mock()
        fake_opening.completed = False

        with patch("ui.startup.ApplicationBootstrap.create", return_value=fake_runtime), \
             patch("ui.startup.CodingAssistantApp", return_value=fake_app), \
             patch("ui.startup.OpeningExperience", return_value=fake_opening), \
             patch("ui.startup.DailyGreetingService") as greeting_cls, \
             patch("ui.startup.greeting_history_path", return_value="history.json"):

            greeting_cls.return_value.today_text.return_value = "Good evening"

            coordinator.start()

            root.after_idle.call_args.args[0]()
            root.after_idle.call_args.args[0]()

        self.assertTrue(coordinator.ready)
        self.assertFalse(coordinator.initializing)
        self.assertEqual(
            coordinator.completed_steps,
            ("runtime", "visual", "greeting"),
        )
        fake_opening.complete.assert_called_once()

    def test_app_entry_passes_root_to_startup_coordinator(self):
        source = Path("ui/app_entry.py").read_text(encoding="utf-8")
        self.assertIn(
            "coordinator = StartupCoordinator(",
            source,
        )
        self.assertIn(
            "            root,",
            source,
        )
        self.assertIn(
            "            runtime_root=runtime_root,",
            source,
        )
        self.assertIn(
            "            greeting_resolver=resolve_daily_greeting,",
            source,
        )

    def test_start_does_not_use_sleep_or_fixed_wait(self):
        source = Path("ui/startup.py").read_text(encoding="utf-8")

        self.assertNotIn("time.sleep", source)
        self.assertNotIn("sleep(", source)
        self.assertNotIn("duration_ms", source)


if __name__ == "__main__":
    unittest.main()
