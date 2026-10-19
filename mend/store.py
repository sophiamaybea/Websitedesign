"""Durable SQLite job queue and verified repair library (single-instance deployment)."""
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager


def _path():
    return os.getenv("MEND_DB_PATH", "data/mend.sqlite3")


@contextmanager
def database():
    path = _path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    cx = sqlite3.connect(path, timeout=15, isolation_level=None)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA journal_mode=WAL")
    cx.execute("PRAGMA busy_timeout=15000")
    try:
        yield cx
    finally:
        cx.close()


def initialise():
    with database() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, kind TEXT NOT NULL, url TEXT NOT NULL,
          brief TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT 'queued',
          result TEXT, error TEXT, created REAL NOT NULL, updated REAL NOT NULL,
          lease_until REAL, approved_by TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_jobs_queue ON jobs(state, created);
        CREATE TABLE IF NOT EXISTS recipes (
          id TEXT PRIMARY KEY, symptom TEXT NOT NULL,
          environment TEXT NOT NULL, repair TEXT NOT NULL,
          verification TEXT NOT NULL, source_job TEXT NOT NULL,
          approved INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_events (
          id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
          provider TEXT NOT NULL, units REAL NOT NULL,
          unit_type TEXT NOT NULL, estimated_cost_usd REAL NOT NULL,
          created REAL NOT NULL
        );
        """)


def create_job(kind, url, brief=""):
    job_id = str(uuid.uuid4())
    now = time.time()
    with database() as db:
        db.execute("""INSERT INTO jobs (id,kind,url,brief,created,updated)
                      VALUES (?,?,?,?,?,?)""", (job_id, kind, url, brief, now, now))
    return job_id


def _decode(row):
    if row is None:
        return None
    data = dict(row)
    data["result"] = json.loads(data["result"]) if data["result"] else None
    return data


def get_job(job_id):
    with database() as db:
        return _decode(db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())


def claim_job(lease_seconds=300):
    """Atomic claim; reclaim crashed workers. Jobs are idempotent and never deploy."""
    now = time.time()
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("""SELECT * FROM jobs
              WHERE state = 'queued' OR (state = 'running' AND lease_until < ?)
              ORDER BY created LIMIT 1""", (now,)).fetchone()
        if row:
            db.execute("""UPDATE jobs SET state='running', lease_until=?, updated=?
                          WHERE id=?""", (now + lease_seconds, now, row["id"]))
        db.execute("COMMIT")
        return _decode(row)


def finish_job(job_id, result):
    with database() as db:
        db.execute("""UPDATE jobs SET state='proposal',result=?,error=NULL,
                      lease_until=NULL,updated=? WHERE id=? AND state='running'""",
                   (json.dumps(result), time.time(), job_id))


def fail_job(job_id, message):
    with database() as db:
        db.execute("""UPDATE jobs SET state='failed',error=?,lease_until=NULL,updated=?
                      WHERE id=?""", (str(message)[:600], time.time(), job_id))


def approve_job(job_id, approved_by):
    with database() as db:
        cur = db.execute("""UPDATE jobs SET state='approved',approved_by=?,updated=?
                            WHERE id=? AND state='proposal'""",
                         (approved_by, time.time(), job_id))
        return bool(cur.rowcount)


def add_recipe(symptom, environment, repair, verification, source_job, approved=False):
    recipe_id = str(uuid.uuid4())
    with database() as db:
        db.execute("""INSERT INTO recipes VALUES (?,?,?,?,?,?,?,?)""",
                   (recipe_id, symptom, environment, repair, verification,
                    source_job, int(approved), time.time()))
    return recipe_id


def find_recipes(text, limit=3):
    """Cheap lexical retrieval. Only human-verified solutions are eligible."""
    words = {w for w in __import__("re").findall(r"[a-z0-9]{3,}", text.lower())}
    with database() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM recipes WHERE approved = 1")]
    ranked = []
    for row in rows:
        content = (row["symptom"] + " " + row["environment"]).lower()
        score = sum(1 for word in words if word in content)
        if score:
            ranked.append((score, row))
    return [r for _, r in sorted(ranked, key=lambda x: -x[0])[:limit]]


def record_usage(job_id, provider, units, unit_type, estimated_cost_usd=0):
    with database() as db:
        db.execute("INSERT INTO usage_events VALUES (?,?,?,?,?,?,?)",
                   (str(uuid.uuid4()), job_id, provider, units, unit_type,
                    estimated_cost_usd, time.time()))


def stats():
    with database() as db:
        states = {r["state"]: r["n"] for r in db.execute(
            "SELECT state,COUNT(*) n FROM jobs GROUP BY state")}
        row = db.execute("SELECT COALESCE(SUM(estimated_cost_usd),0) cost FROM usage_events").fetchone()
        verified = db.execute("SELECT COUNT(*) n FROM recipes WHERE approved=1").fetchone()["n"]
        return {"jobs_by_state": states, "estimated_ai_cost_usd": row["cost"],
                "verified_repairs": verified}
