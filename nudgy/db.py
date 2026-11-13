"""A tiny SQLite store, so deadlines survive a restart of the bot."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    lang    TEXT NOT NULL DEFAULT 'en'
);
CREATE TABLE IF NOT EXISTS tasks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id  INTEGER NOT NULL,
    title    TEXT    NOT NULL,
    due_utc  TEXT    NOT NULL,
    done     INTEGER NOT NULL DEFAULT 0,
    created  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS tasks_chat ON tasks(chat_id, done, due_utc);
"""


@dataclass
class Task:
    id: int
    chat_id: int
    title: str
    due: datetime  # always timezone aware (UTC)
    done: bool


def _row(r: sqlite3.Row) -> Task:
    return Task(r["id"], r["chat_id"], r["title"], datetime.fromisoformat(r["due_utc"]), bool(r["done"]))


class Store:
    def __init__(self, path: str = "nudgy.db") -> None:
        self.con = sqlite3.connect(path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    # ---- users ----
    def get_lang(self, chat_id: int) -> str | None:
        r = self.con.execute("SELECT lang FROM users WHERE chat_id=?", (chat_id,)).fetchone()
        return r["lang"] if r else None

    def set_lang(self, chat_id: int, lang: str) -> None:
        with self.con:
            self.con.execute(
                "INSERT INTO users(chat_id, lang) VALUES(?, ?) "
                "ON CONFLICT(chat_id) DO UPDATE SET lang=excluded.lang",
                (chat_id, lang),
            )

    # ---- tasks ----
    def add(self, chat_id: int, title: str, due: datetime) -> Task:
        due_utc = due.astimezone(timezone.utc)
        with self.con:
            cur = self.con.execute(
                "INSERT INTO tasks(chat_id, title, due_utc, created) VALUES(?, ?, ?, ?)",
                (chat_id, title, due_utc.isoformat(), datetime.now(timezone.utc).isoformat()),
            )
        return Task(cur.lastrowid, chat_id, title, due_utc, False)

    def get(self, task_id: int) -> Task | None:
        r = self.con.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return _row(r) if r else None

    def open_tasks(self, chat_id: int | None = None) -> list[Task]:
        if chat_id is None:
            rows = self.con.execute("SELECT * FROM tasks WHERE done=0 ORDER BY due_utc")
        else:
            rows = self.con.execute(
                "SELECT * FROM tasks WHERE done=0 AND chat_id=? ORDER BY due_utc", (chat_id,)
            )
        return [_row(r) for r in rows]

    def mark_done(self, task_id: int, chat_id: int) -> bool:
        with self.con:
            cur = self.con.execute(
                "UPDATE tasks SET done=1 WHERE id=? AND chat_id=? AND done=0", (task_id, chat_id)
            )
        return cur.rowcount == 1

    def delete(self, task_id: int, chat_id: int) -> bool:
        with self.con:
            cur = self.con.execute("DELETE FROM tasks WHERE id=? AND chat_id=?", (task_id, chat_id))
        return cur.rowcount == 1

    def count_done(self, chat_id: int) -> int:
        r = self.con.execute("SELECT COUNT(*) c FROM tasks WHERE done=1 AND chat_id=?", (chat_id,)).fetchone()
        return r["c"]
