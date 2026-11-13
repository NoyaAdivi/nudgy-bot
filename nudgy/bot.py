"""Nudgy: the Telegram side.

How it talks to Telegram:
1. The bot asks Telegram "any new messages?" (long polling, the getUpdates method).
2. For every message, python-telegram-bot calls the matching handler below.
3. Handlers answer with sendMessage, and edit buttons with editMessageText.
4. The JobQueue wakes up at each reminder time and sends the nudge.
"""
from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .db import Store, Task
from .parsing import parse_deadline, parse_when
from .schedule import reminder_times
from .texts import fmt_left, fmt_when, t, urgency

log = logging.getLogger("nudgy")
ASK_TITLE, ASK_DATE = range(2)


# ---------- setup ----------
def load_env(path: str = ".env") -> None:
    """Read KEY=value lines from .env into the environment (no extra library needed)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Jerusalem"))
store = Store(os.getenv("DB_PATH", "nudgy.db"))


def now() -> datetime:
    return datetime.now(timezone.utc)


def lang_of(update: Update) -> str:
    chat_id = update.effective_chat.id
    saved = store.get_lang(chat_id)
    if saved:
        return saved
    guess = "he" if (update.effective_user and update.effective_user.language_code == "he") else "en"
    store.set_lang(chat_id, guess)
    return guess


def task_buttons(task: Task, lang: str, snooze: bool = False) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(t(lang, "btn_done"), callback_data=f"done:{task.id}")]
    if snooze:
        row.append(InlineKeyboardButton(t(lang, "btn_snooze"), callback_data=f"snooze:{task.id}"))
    else:
        row.append(InlineKeyboardButton(t(lang, "btn_delete"), callback_data=f"del:{task.id}"))
    return InlineKeyboardMarkup([row])


# ---------- reminders (JobQueue) ----------
def schedule_task(app: Application, task: Task) -> int:
    times = reminder_times(task.due, now())
    for kind, when in times:
        app.job_queue.run_once(
            send_reminder, when=when, chat_id=task.chat_id,
            name=f"task-{task.id}", data={"task_id": task.id, "kind": kind},
        )
    return len(times)


def unschedule_task(app: Application, task_id: int) -> None:
    for job in app.job_queue.get_jobs_by_name(f"task-{task_id}"):
        job.schedule_removal()


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    task = store.get(data["task_id"])
    if not task or task.done:
        return
    lang = store.get_lang(task.chat_id) or "en"
    local = task.due.astimezone(TZ)
    await context.bot.send_message(
        task.chat_id,
        t(lang, f"remind_{data['kind']}", title=task.title, when=fmt_when(local, lang)),
        parse_mode=ParseMode.HTML,
        reply_markup=task_buttons(task, lang, snooze=True),
    )


async def reschedule_all(app: Application) -> None:
    """Runs once when the bot starts: bring back every saved reminder and set the menu."""
    tasks = store.open_tasks()
    for task in tasks:
        schedule_task(app, task)
    log.info("Rescheduled %d open deadlines", len(tasks))
    for lang_code, lang in ((None, "en"), ("he", "he")):
        await app.bot.set_my_commands(
            [
                BotCommand("add", "➕ " + ("הוספת דדליין" if lang == "he" else "Add a deadline")),
                BotCommand("list", "🗂 " + ("כל הדדליינים" if lang == "he" else "All deadlines")),
                BotCommand("today", "☀️ " + ("להגשה היום" if lang == "he" else "Due today")),
                BotCommand("week", "📆 " + ("השבוע הקרוב" if lang == "he" else "Next 7 days")),
                BotCommand("lang", "🌍 עברית / English"),
                BotCommand("help", "❓ " + ("עזרה" if lang == "he" else "Help")),
            ],
            language_code=lang_code,
        )


# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = lang_of(update)
    name = update.effective_user.first_name if update.effective_user else ""
    await update.message.reply_html(t(lang, "welcome", name=name))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(t(lang_of(update), "help"))


async def save_and_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, title: str, due: datetime) -> None:
    lang = lang_of(update)
    task = store.add(update.effective_chat.id, title, due)
    count = schedule_task(context.application, task)
    local = task.due.astimezone(TZ)
    count_text = t(lang, "count_one") if count == 1 else t(lang, "count_many", n=count)
    await update.message.reply_html(
        t(lang, "added", title=title, when=fmt_when(local, lang), left=fmt_left(task.due, now(), lang), count=count_text),
        reply_markup=task_buttons(task, lang),
    )


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = lang_of(update)
    if context.args:
        parsed = parse_deadline(" ".join(context.args), now(), TZ)
        if not parsed:
            await update.message.reply_html(t(lang, "bad_add"))
        elif parsed[0] <= now():
            await update.message.reply_html(t(lang, "past"))
        else:
            await save_and_confirm(update, context, parsed[1], parsed[0])
        return ConversationHandler.END
    await update.message.reply_html(t(lang, "ask_title"))
    return ASK_TITLE


async def got_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text.strip()[:200]
    await update.message.reply_html(t(lang_of(update), "ask_date"))
    return ASK_DATE


async def got_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = lang_of(update)
    found = parse_when(update.message.text, now(), TZ)
    if not found:
        await update.message.reply_html(t(lang, "bad_date"))
        return ASK_DATE
    if found[0] <= now():
        await update.message.reply_html(t(lang, "past"))
        return ASK_DATE
    await save_and_confirm(update, context, context.user_data.pop("title"), found[0])
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_html(t(lang_of(update), "cancelled"))
    return ConversationHandler.END


async def show(update: Update, head_key: str, empty_key: str, until: datetime | None) -> None:
    lang = lang_of(update)
    tasks = [x for x in store.open_tasks(update.effective_chat.id) if until is None or x.due <= until]
    if not tasks:
        await update.message.reply_html(t(lang, empty_key))
        return
    await update.message.reply_html(t(lang, head_key, n=len(tasks)))
    for task in tasks[:20]:
        local = task.due.astimezone(TZ)
        await update.message.reply_html(
            f"{urgency(task.due, now())} <b>{escape(task.title)}</b>\n"
            f"🗓 {fmt_when(local, lang)}\n"
            f"⏳ {fmt_left(task.due, now(), lang)}",
            reply_markup=task_buttons(task, lang),
        )


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show(update, "list_head", "empty", None)


async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    local_now = now().astimezone(TZ)
    end = local_now.replace(hour=23, minute=59, second=59)
    await show(update, "today_head", "none_today", end)


async def week_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show(update, "week_head", "none_week", now() + timedelta(days=7))


async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇮🇱 עברית", callback_data="lang:he"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
    ]])
    await update.message.reply_html(t(lang_of(update), "lang_pick"), reply_markup=buttons)


# ---------- buttons ----------
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, value = query.data.split(":", 1)
    chat_id = update.effective_chat.id

    if action == "lang":
        store.set_lang(chat_id, value)
        await query.edit_message_text(t(value, "lang_set"))
        return

    lang = lang_of(update)
    task = store.get(int(value))
    if not task or task.chat_id != chat_id:
        await query.edit_message_text(t(lang, "gone"))
        return

    if action == "done" and store.mark_done(task.id, chat_id):
        unschedule_task(context.application, task.id)
        await query.edit_message_text(
            t(lang, "marked_done", title=task.title, n=store.count_done(chat_id)), parse_mode=ParseMode.HTML
        )
    elif action == "del" and store.delete(task.id, chat_id):
        unschedule_task(context.application, task.id)
        await query.edit_message_text(t(lang, "deleted", title=task.title), parse_mode=ParseMode.HTML)
    elif action == "snooze":
        context.job_queue.run_once(
            send_reminder, when=timedelta(hours=1), chat_id=chat_id,
            name=f"task-{task.id}", data={"task_id": task.id, "kind": "snooze"},
        )
        await query.edit_message_reply_markup(None)
        await query.message.reply_text(t(lang, "snoozed"))


# ---------- run ----------
def build_app(token: str) -> Application:
    app = Application.builder().token(token).post_init(reschedule_all).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_title)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("week", week_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(on_button))
    return app


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # keep the token out of the logs
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env and paste your token from @BotFather.")
        asyncio.set_event_loop(asyncio.new_event_loop())
    log.info("Nudgy is running. Press Ctrl+C to stop.")
    build_app(token).run_polling(allowed_updates=Update.ALL_TYPES)
