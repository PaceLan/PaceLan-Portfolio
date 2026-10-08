import unittest
from datetime import datetime, timedelta, timezone

from application.chatgpt_timed_recovery_scheduler import (
    ChatGPTTimedRecoveryScheduler,
    RecoverySchedule,
)


class ChatGPTTimedRecoverySchedulerC515Tests(unittest.TestCase):
    def setUp(self):
        self.scheduler = ChatGPTTimedRecoveryScheduler()
        self.detected_at = datetime(
            2026, 10, 8, 1, 0, tzinfo=timezone.utc
        )

    def test_first_check_is_15_minutes_after_detection(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )

        self.assertEqual(
            schedule.waiting_until,
            self.detected_at + timedelta(minutes=15),
        )
        self.assertEqual(
            schedule.next_check,
            self.detected_at + timedelta(minutes=15),
        )

    def test_not_due_before_waiting_period(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )

        self.assertFalse(
            self.scheduler.is_due(
                schedule,
                now=self.detected_at + timedelta(minutes=14),
            )
        )

    def test_due_at_first_check(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )

        self.assertTrue(
            self.scheduler.is_due(
                schedule,
                now=self.detected_at + timedelta(minutes=15),
            )
        )

    def test_next_check_is_three_minutes_later(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )
        checked_at = schedule.next_check

        updated = self.scheduler.next_check(
            schedule,
            checked_at=checked_at,
        )

        self.assertEqual(
            updated.next_check,
            checked_at + timedelta(minutes=3),
        )
        self.assertEqual(updated.retry_count, 1)

    def test_repeated_checks_advance_every_three_minutes(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )

        first = self.scheduler.next_check(
            schedule,
            checked_at=schedule.next_check,
        )
        second = self.scheduler.next_check(
            first,
            checked_at=first.next_check,
        )

        self.assertEqual(second.retry_count, 2)
        self.assertEqual(
            second.next_check,
            self.detected_at + timedelta(minutes=21),
        )

    def test_naive_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.scheduler.schedule(
                detected_at=datetime(2026, 10, 8, 1, 0)
            )

    def test_early_check_update_is_rejected(self):
        schedule = self.scheduler.schedule(
            detected_at=self.detected_at
        )

        with self.assertRaises(ValueError):
            self.scheduler.next_check(
                schedule,
                checked_at=schedule.next_check - timedelta(seconds=1),
            )


if __name__ == "__main__":
    unittest.main()
