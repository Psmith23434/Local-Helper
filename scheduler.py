"""Background task scheduler using APScheduler."""

import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import database as db
import ai_client
import search
import file_context
from config import DEFAULT_MODEL

_scheduler = BackgroundScheduler()
_started = False


def start():
    global _started
    if not _started:
        _scheduler.start()
        _started = True
        _load_all_tasks()


def stop():
    if _started:
        _scheduler.shutdown(wait=False)


def _run_task(space_id: int, task_id: int, prompt: str):
    """Execute a scheduled AI task and save result as a new thread."""
    space = db.get_space(space_id)
    if not space:
        return

    model = space["model"] or DEFAULT_MODEL
    system = space["instructions"] or "You are a helpful assistant."

    # Build context
    extra_context = ""
    if space["web_search"]:
        extra_context += search.web_search(prompt)

    files = db.get_space_files(space_id)
    if files:
        paths = [f["filepath"] for f in files]
        extra_context += "\n\n" + file_context.build_file_context(paths)

    if extra_context:
        system += f"\n\n--- Context ---\n{extra_context}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    reply = ai_client.chat(messages, model=model)

    # Save result as a new thread
    thread_id = db.create_thread(space_id, title=f"[Scheduled] {prompt[:40]}")
    db.add_message(thread_id, "user", prompt)
    db.add_message(thread_id, "assistant", reply)


def _load_all_tasks():
    """Load all enabled scheduled tasks from the database."""
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM scheduled_tasks WHERE enabled=1").fetchall()
    conn.close()
    for row in rows:
        t = dict(row)
        args = json.loads(t["trigger_args"])
        _add_job(t["id"], t["space_id"], t["prompt"], t["trigger"], args)


def _add_job(task_id, space_id, prompt, trigger, trigger_args):
    job_id = f"task_{task_id}"
    if trigger == "cron":
        trig = CronTrigger(**trigger_args)
    else:
        trig = IntervalTrigger(**trigger_args)
    _scheduler.add_job(
        _run_task,
        trigger=trig,
        args=[space_id, task_id, prompt],
        id=job_id,
        replace_existing=True,
    )


def register_task(task_id, space_id, prompt, trigger, trigger_args):
    _add_job(task_id, space_id, prompt, trigger, trigger_args)


def remove_task(task_id):
    job_id = f"task_{task_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
