from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from nudgy.db import Store
from nudgy.parsing import parse_deadline, parse_when
from nudgy.schedule import reminder_times, remaining
from nudgy.texts import T, fmt_left, t, urgency

TZ = ZoneInfo("Asia/Jerusalem")
NOW = datetime(2026, 11, 13, 10, 0, tzinfo=TZ)  # a Friday


def test_day_month_with_time():
    due, title = parse_deadline("20/11 18:30 Algorithms HW 3", NOW, TZ)
    assert (due.day, due.month, due.year, due.hour, due.minute) == (20, 11, 2026, 18, 30)
    assert title == "Algorithms HW 3"


def test_default_time_is_end_of_day():
    due, _ = parse_deadline("2026-12-01 Project", NOW, TZ)
    assert (due.hour, due.minute) == (23, 59)


def test_past_day_month_rolls_to_next_year():
    due, _ = parse_deadline("05/01 Exam", NOW, TZ)
    assert due.year == 2027


def test_words_in_both_languages():
    assert parse_deadline("tomorrow 09:00 Quiz", NOW, TZ)[0].day == 14
    assert parse_deadline("מחר מטלה", NOW, TZ)[0].day == 14
    assert parse_deadline("+3 Lab report", NOW, TZ)[0].day == 16


def test_weekday_is_always_in_the_future():
    assert parse_deadline("friday Essay", NOW, TZ)[0].day == 20  # next Friday, not today
    assert parse_deadline("יום ראשון מטלה", NOW, TZ)[0].day == 15


def test_invalid_input():
    assert parse_deadline("31/02 Nope", NOW, TZ) is None
    assert parse_deadline("hello world", NOW, TZ) is None
    assert parse_deadline("tomorrow", NOW, TZ) is None  # no title
    assert parse_when("25:00", NOW, TZ) is None


def test_reminders_skip_the_past():
    due = NOW + timedelta(hours=30)
    kinds = [k for k, _ in reminder_times(due, NOW)]
    assert kinds == ["1d", "3h", "due"]


def test_remaining_and_urgency():
    assert remaining(NOW + timedelta(days=2, hours=3, minutes=5), NOW) == (2, 3, 5)
    assert remaining(NOW - timedelta(minutes=1), NOW)[0] == -1
    assert urgency(NOW + timedelta(hours=5), NOW) == "🔴"
    assert urgency(NOW + timedelta(days=10), NOW) == "🟢"
    assert "3" in fmt_left(NOW + timedelta(hours=3), NOW, "en")


def test_store_roundtrip(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    task = s.add(1, "HW", NOW + timedelta(days=1))
    assert s.open_tasks(1)[0].title == "HW"
    assert s.open_tasks(1)[0].due.tzinfo is not None
    assert not s.mark_done(task.id, chat_id=2)  # someone else's task
    assert s.mark_done(task.id, 1)
    assert s.open_tasks(1) == [] and s.count_done(1) == 1
    s.set_lang(1, "he")
    assert s.get_lang(1) == "he"


def test_texts_match_in_both_languages():
    assert set(T["en"]) == set(T["he"])
    assert "&lt;b&gt;" in t("en", "deleted", title="<b>")  # user text is escaped


def test_no_long_dashes_in_texts():
    for lang in T.values():
        for text in lang.values():
            assert "\u2014" not in text and "\u2013" not in text


def test_hebrew_commands_stay_readable():
    text = t("he", "help")
    assert "‎/add‎" in text
    assert "</b>" in text and "20/11" in text  # html tags and dates untouched
