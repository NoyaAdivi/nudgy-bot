"""Turn what the user types ("20/11 23:59 Algorithms HW") into a real deadline.

This module has no Telegram code in it, so it is easy to test.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TIME = time(23, 59)

_WORD_DAYS = {
    "today": 0, "היום": 0,
    "tomorrow": 1, "מחר": 1,
    "מחרתיים": 2,
}

# Monday = 0 ... Sunday = 6 (same as date.weekday())
_WEEKDAYS = {
    "mon": 0, "monday": 0, "שני": 0,
    "tue": 1, "tuesday": 1, "שלישי": 1,
    "wed": 2, "wednesday": 2, "רביעי": 2,
    "thu": 3, "thursday": 3, "חמישי": 3,
    "fri": 4, "friday": 4, "שישי": 4,
    "sat": 5, "saturday": 5, "שבת": 5,
    "sun": 6, "sunday": 6, "ראשון": 6,
}

_DMY = re.compile(r"^(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2}|\d{4}))?$")
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")  # 9:30, 23:59
_IN_DAYS = re.compile(r"^\+(\d{1,3})$")  # "+3" means in 3 days


def _parse_date(token: str, today: date) -> date | None:
    token = token.lower().strip()
    if token.startswith("יום"):
        token = token[3:].strip()
    if token in _WORD_DAYS:
        return today + timedelta(days=_WORD_DAYS[token])
    if token in _WEEKDAYS:
        ahead = (_WEEKDAYS[token] - today.weekday()) % 7 or 7
        return today + timedelta(days=ahead)
    if m := _IN_DAYS.match(token):
        return today + timedelta(days=int(m.group(1)))
    if m := _ISO.match(token):
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    if m := _DMY.match(token):
        day, month, year = int(m.group(1)), int(m.group(2)), m.group(3)
        try:
            if year:
                y = int(year)
                return date(y + 2000 if y < 100 else y, month, day)
            d = date(today.year, month, day)
            # "20/1" written in December means next January
            return d if d >= today else date(today.year + 1, month, day)
        except ValueError:
            return None
    return None


def _parse_time(token: str) -> time | None:
    m = _TIME.match(token.strip())
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def parse_when(text: str, now: datetime, tz: ZoneInfo) -> tuple[datetime, int] | None:
    """Read a date and an optional time from the start of ``text``.

    Returns the deadline and how many words were used, or None.
    """
    words = text.split()
    if not words:
        return None
    local_now = now.astimezone(tz)
    # allow "יום שלישי" as two words
    first = words[0]
    used = 1
    if first == "יום" and len(words) > 1:
        first, used = "יום" + words[1], 2
    day = _parse_date(first, local_now.date())
    if day is None:
        return None
    at = DEFAULT_TIME
    if len(words) > used and (t := _parse_time(words[used])):
        at, used = t, used + 1
    return datetime.combine(day, at, tzinfo=tz), used


def parse_deadline(text: str, now: datetime, tz: ZoneInfo) -> tuple[datetime, str] | None:
    """Parse "<date> [time] <title>" into (deadline, title)."""
    found = parse_when(text, now, tz)
    if not found:
        return None
    due, used = found
    title = " ".join(text.split()[used:]).strip(" -:")
    if not title:
        return None
    return due, title
