"""SQLite database layer for Local Helper."""

import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS spaces (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            instructions TEXT DEFAULT '',
            model       TEXT DEFAULT '',
            github_repo TEXT DEFAULT '',
            web_search  INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS threads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id   INTEGER NOT NULL,
            title      TEXT DEFAULT 'New Thread',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(space_id) REFERENCES spaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id  INTEGER NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS space_files (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            FOREIGN KEY(space_id) REFERENCES spaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id    INTEGER NOT NULL,
            name        TEXT NOT NULL,
            prompt      TEXT NOT NULL,
            trigger     TEXT NOT NULL,
            trigger_args TEXT NOT NULL DEFAULT '{}',
            enabled     INTEGER DEFAULT 1,
            FOREIGN KEY(space_id) REFERENCES spaces(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# ── Spaces ────────────────────────────────────
def create_space(name, instructions="", model="", github_repo="", web_search=True):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO spaces (name, instructions, model, github_repo, web_search) VALUES (?,?,?,?,?)",
        (name, instructions, model, github_repo, int(web_search))
    )
    conn.commit()
    space_id = c.lastrowid
    conn.close()
    return space_id


def get_spaces():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM spaces ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_space(space_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM spaces WHERE id=?", (space_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_space(space_id, name, instructions, model, github_repo, web_search):
    conn = get_conn()
    conn.execute(
        "UPDATE spaces SET name=?, instructions=?, model=?, github_repo=?, web_search=? WHERE id=?",
        (name, instructions, model, github_repo, int(web_search), space_id)
    )
    conn.commit()
    conn.close()


def delete_space(space_id):
    conn = get_conn()
    conn.execute("DELETE FROM spaces WHERE id=?", (space_id,))
    conn.commit()
    conn.close()


# ── Threads ───────────────────────────────────
def create_thread(space_id, title="New Thread"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO threads (space_id, title) VALUES (?,?)", (space_id, title))
    conn.commit()
    thread_id = c.lastrowid
    conn.close()
    return thread_id


def get_threads(space_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM threads WHERE space_id=? ORDER BY created_at DESC", (space_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rename_thread(thread_id, title):
    conn = get_conn()
    conn.execute("UPDATE threads SET title=? WHERE id=?", (title, thread_id))
    conn.commit()
    conn.close()


def delete_thread(thread_id):
    conn = get_conn()
    conn.execute("DELETE FROM threads WHERE id=?", (thread_id,))
    conn.commit()
    conn.close()


# ── Messages ──────────────────────────────────
def add_message(thread_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?,?,?)",
        (thread_id, role, content)
    )
    conn.commit()
    conn.close()


def get_messages(thread_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE thread_id=? ORDER BY created_at ASC", (thread_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Space Files ───────────────────────────────
def add_space_file(space_id, filepath):
    conn = get_conn()
    conn.execute("INSERT INTO space_files (space_id, filepath) VALUES (?,?)", (space_id, filepath))
    conn.commit()
    conn.close()


def get_space_files(space_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM space_files WHERE space_id=?", (space_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_space_file(file_id):
    conn = get_conn()
    conn.execute("DELETE FROM space_files WHERE id=?", (file_id,))
    conn.commit()
    conn.close()


# ── Scheduled Tasks ───────────────────────────
def add_scheduled_task(space_id, name, prompt, trigger, trigger_args):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO scheduled_tasks (space_id, name, prompt, trigger, trigger_args) VALUES (?,?,?,?,?)",
        (space_id, name, prompt, trigger, json.dumps(trigger_args))
    )
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id


def get_scheduled_tasks(space_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM scheduled_tasks WHERE space_id=?", (space_id,)).fetchall()
    conn.close()
    tasks = []
    for r in rows:
        t = dict(r)
        t["trigger_args"] = json.loads(t["trigger_args"])
        tasks.append(t)
    return tasks


def delete_scheduled_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM scheduled_tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
