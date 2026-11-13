"""Every message the bot sends, in English and Hebrew."""
from __future__ import annotations

from datetime import datetime
from html import escape

from .schedule import remaining

T: dict[str, dict[str, str]] = {
    "en": {
        "welcome": (
            "👋 <b>Hi {name}, I'm Nudgy!</b>\n"
            "I remember your deadlines so you don't have to.\n\n"
            "I'll nudge you <b>3 days</b>, <b>1 day</b> and <b>3 hours</b> before, and right when it's due.\n\n"
            "Try it now:\n<code>/add tomorrow 23:59 Algorithms HW 3</code>\n\n"
            "Type /help to see everything I can do."
        ),
        "help": (
            "🗓 <b>What I can do</b>\n\n"
            "/add <i>date [time] task</i>  add a deadline\n"
            "/add  (no text) and I'll ask you step by step\n"
            "/list  all open deadlines\n"
            "/today  what's due today\n"
            "/week  the next 7 days\n"
            "/lang  עברית / English\n"
            "/cancel  stop what we're doing\n\n"
            "📅 <b>Dates I understand</b>\n"
            "<code>20/11</code> · <code>20/11/2026</code> · <code>2026-11-20</code> · "
            "<code>today</code> · <code>tomorrow</code> · <code>+3</code> (in 3 days) · <code>friday</code>\n"
            "No time? I'll use <b>23:59</b>."
        ),
        "ask_title": "✏️ What's the task? (for example: <i>Data Structures HW 4</i>)",
        "ask_date": "📅 When is it due? (for example: <code>20/11 23:59</code> or <code>tomorrow</code>)",
        "bad_date": "🤔 I couldn't read that date. Try <code>20/11 23:59</code>, <code>tomorrow</code> or <code>+3</code>.",
        "bad_add": "🤔 Write it like this:\n<code>/add 20/11 23:59 Algorithms HW 3</code>\nor just /add and I'll ask.",
        "past": "⌛ That time already passed. Pick a date in the future.",
        "added": "✅ <b>Saved!</b>\n📌 {title}\n🗓 {when}\n⏳ {left}\n\nI'll remind you {count}.",
        "count_one": "once more",
        "count_many": "{n} times",
        "cancelled": "👌 Cancelled.",
        "empty": "🎉 No open deadlines. Enjoy the free time!\nAdd one with /add",
        "list_head": "🗂 <b>Your deadlines</b> ({n})",
        "today_head": "☀️ <b>Due today</b>",
        "week_head": "📆 <b>Next 7 days</b>",
        "none_today": "☀️ Nothing due today.",
        "none_week": "📆 Nothing due in the next 7 days.",
        "btn_done": "✅ Done",
        "btn_delete": "🗑 Delete",
        "btn_snooze": "⏰ Remind me in 1h",
        "marked_done": "🎉 Nice work! <s>{title}</s> is done. ({n} finished so far)",
        "deleted": "🗑 Deleted: {title}",
        "gone": "This deadline doesn't exist anymore.",
        "snoozed": "⏰ OK, I'll remind you again in an hour.",
        "remind_3d": "🔔 <b>3 days left</b>\n📌 {title}\n🗓 {when}",
        "remind_1d": "🔔 <b>Tomorrow!</b>\n📌 {title}\n🗓 {when}",
        "remind_3h": "⏰ <b>Only 3 hours left</b>\n📌 {title}\n🗓 {when}",
        "remind_due": "🚨 <b>It's due now</b>\n📌 {title}\nDid you submit it?",
        "remind_snooze": "🔔 <b>Reminder</b>\n📌 {title}\n🗓 {when}",
        "lang_pick": "🌍 Choose a language:",
        "lang_set": "✅ I'll talk to you in English from now on.",
        "left": "{d}d {h}h {m}m left",
        "left_hours": "{h}h {m}m left",
        "passed": "already passed",
        "days": "Mon Tue Wed Thu Fri Sat Sun",
    },
    "he": {
        "welcome": (
            "👋 <b>היי {name}, אני Nudgy!</b>\n"
            "אני זוכר את הדדליינים בשבילך, כדי שלא תצטרכו לזכור.\n\n"
            "אזכיר לך <b>3 ימים</b>, <b>יום אחד</b> ו־<b>3 שעות</b> לפני, ובדיוק כשמגיע הזמן.\n\n"
            "נסו עכשיו:\n<code>/add מחר 23:59 מטלה 3 באלגוריתמים</code>\n\n"
            "כתבו /help כדי לראות את כל מה שאני יודע לעשות."
        ),
        "help": (
            "🗓 <b>מה אני יודע לעשות</b>\n\n"
            "/add <i>תאריך [שעה] משימה</i>  הוספת דדליין\n"
            "/add  (בלי טקסט) ואשאל אותך שלב אחרי שלב\n"
            "/list  כל הדדליינים הפתוחים\n"
            "/today  מה צריך להגיש היום\n"
            "/week  7 הימים הקרובים\n"
            "/lang  עברית / English\n"
            "/cancel  ביטול הפעולה\n\n"
            "📅 <b>תאריכים שאני מבין</b>\n"
            "<code>20/11</code> · <code>20/11/2026</code> · <code>2026-11-20</code> · "
            "<code>היום</code> · <code>מחר</code> · <code>+3</code> (בעוד 3 ימים) · <code>שישי</code>\n"
            "בלי שעה? אשים <b>23:59</b>."
        ),
        "ask_title": "✏️ מה המשימה? (למשל: <i>מטלה 4 במבני נתונים</i>)",
        "ask_date": "📅 מתי ההגשה? (למשל: <code>20/11 23:59</code> או <code>מחר</code>)",
        "bad_date": "🤔 לא הצלחתי להבין את התאריך. נסו <code>20/11 23:59</code>, <code>מחר</code> או <code>+3</code>.",
        "bad_add": "🤔 כתבו ככה:\n<code>/add 20/11 23:59 מטלה 3 באלגוריתמים</code>\nאו רק /add ואני אשאל.",
        "past": "⌛ הזמן הזה כבר עבר. בחרו תאריך עתידי.",
        "added": "✅ <b>נשמר!</b>\n📌 {title}\n🗓 {when}\n⏳ {left}\n\nאזכיר לך {count}.",
        "count_one": "עוד פעם אחת",
        "count_many": "{n} פעמים",
        "cancelled": "👌 בוטל.",
        "empty": "🎉 אין דדליינים פתוחים. תהנו מהזמן הפנוי!\nאפשר להוסיף עם /add",
        "list_head": "🗂 <b>הדדליינים שלך</b> ({n})",
        "today_head": "☀️ <b>להגשה היום</b>",
        "week_head": "📆 <b>7 הימים הקרובים</b>",
        "none_today": "☀️ אין הגשות היום.",
        "none_week": "📆 אין הגשות ב־7 הימים הקרובים.",
        "btn_done": "✅ הוגש",
        "btn_delete": "🗑 מחיקה",
        "btn_snooze": "⏰ תזכיר לי בעוד שעה",
        "marked_done": "🎉 כל הכבוד! <s>{title}</s> הושלם. ({n} הושלמו עד עכשיו)",
        "deleted": "🗑 נמחק: {title}",
        "gone": "הדדליין הזה כבר לא קיים.",
        "snoozed": "⏰ בסדר, אזכיר שוב בעוד שעה.",
        "remind_3d": "🔔 <b>נשארו 3 ימים</b>\n📌 {title}\n🗓 {when}",
        "remind_1d": "🔔 <b>זה מחר!</b>\n📌 {title}\n🗓 {when}",
        "remind_3h": "⏰ <b>נשארו רק 3 שעות</b>\n📌 {title}\n🗓 {when}",
        "remind_due": "🚨 <b>הגיע הזמן</b>\n📌 {title}\nהגשת?",
        "remind_snooze": "🔔 <b>תזכורת</b>\n📌 {title}\n🗓 {when}",
        "lang_pick": "🌍 בחרו שפה:",
        "lang_set": "✅ מעכשיו אדבר איתך בעברית.",
        "left": "נשארו {d} ימים, {h} שעות ו־{m} דקות",
        "left_hours": "נשארו {h} שעות ו־{m} דקות",
        "passed": "כבר עבר",
        "days": "ב׳ ג׳ ד׳ ה׳ ו׳ ש׳ א׳",
    },
}


def t(lang: str, key: str, **kw) -> str:
    text = T.get(lang, T["en"]).get(key) or T["en"][key]
    return text.format(**{k: escape(str(v)) if k in ("title", "name") else v for k, v in kw.items()})


def fmt_when(due: datetime, lang: str) -> str:
    day = T[lang]["days"].split()[due.weekday()]
    return f"{day} {due:%d/%m} · {due:%H:%M}"


def fmt_left(due: datetime, now: datetime, lang: str) -> str:
    d, h, m = remaining(due, now)
    if d < 0:
        return T[lang]["passed"]
    if d == 0:
        return T[lang]["left_hours"].format(h=h, m=m)
    return T[lang]["left"].format(d=d, h=h, m=m)


def urgency(due: datetime, now: datetime) -> str:
    """A colored dot that shows how close a deadline is."""
    hours = (due - now).total_seconds() / 3600
    if hours < 24:
        return "🔴"
    if hours < 72:
        return "🟠"
    if hours < 168:
        return "🟡"
    return "🟢"
