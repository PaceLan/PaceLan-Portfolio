from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RecoverySchedule:
    detected_at: datetime
    waiting_until: datetime
    next_check: datetime
    retry_count: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("detected_at", self.detected_at),
            ("waiting_until", self.waiting_until),
            ("next_check", self.next_check),
        ):
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.retry_count < 0:
            raise ValueError("retry_count must not be negative")


class ChatGPTTimedRecoveryScheduler:
    WAIT_SECONDS = 15 * 60
    CHECK_INTERVAL_SECONDS = 3 * 60

    def schedule(
        self,
        *,
        detected_at: datetime,
        retry_count: int = 0,
    ) -> RecoverySchedule:
        if detected_at.tzinfo is None:
            raise ValueError("detected_at must be timezone-aware")
        if retry_count < 0:
            raise ValueError("retry_count must not be negative")

        waiting_until = detected_at + timedelta(
            seconds=self.WAIT_SECONDS
        )

        return RecoverySchedule(
            detected_at=detected_at,
            waiting_until=waiting_until,
            next_check=waiting_until,
            retry_count=retry_count,
        )

    def is_due(
        self,
        schedule: RecoverySchedule,
        *,
        now: datetime,
    ) -> bool:
        if not isinstance(schedule, RecoverySchedule):
            raise TypeError("schedule must be a RecoverySchedule")
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return now >= schedule.next_check

    def next_check(
        self,
        schedule: RecoverySchedule,
        *,
        checked_at: datetime,
    ) -> RecoverySchedule:
        if not isinstance(schedule, RecoverySchedule):
            raise TypeError("schedule must be a RecoverySchedule")
        if checked_at.tzinfo is None:
            raise ValueError("checked_at must be timezone-aware")
        if checked_at < schedule.next_check:
            raise ValueError("checked_at must not precede next_check")

        return RecoverySchedule(
            detected_at=schedule.detected_at,
            waiting_until=schedule.waiting_until,
            next_check=checked_at
            + timedelta(seconds=self.CHECK_INTERVAL_SECONDS),
            retry_count=schedule.retry_count + 1,
        )


__all__ = ["ChatGPTTimedRecoveryScheduler", "RecoverySchedule"]
