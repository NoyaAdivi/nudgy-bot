"""When should a deadline send a reminder?"""
from __future__ import annotations

from datetime import datetime, timedelta

# kind -> how long before the deadline
OFFSETS: dict[str, timedelta] = {
    "3d": timedelta(days=3),
    "1d": timedelta(days=1),
    "3h": timedelta(hours=3),
    "due": timedelta(0),
}


def reminder_times(due: datetime, now: datetime) -> list[tuple[str, datetime]]:
    """All reminders for ``due`` that are still in the future, earliest first."""
    out = [(kind, due - delta) for kind, delta in OFFSETS.items()]
    return sorted([(k, when) for k, when in out if when > now], key=lambda x: x[1])


def remaining(due: datetime, now: datetime) -> tuple[int, int, int]:
    """(days, hours, minutes) left until ``due``. Negative days mean it passed."""
    seconds = int((due - now).total_seconds())
    if seconds < 0:
        return -1, 0, 0
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    return days, hours, seconds // 60
