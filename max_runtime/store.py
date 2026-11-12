from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

TERMINAL = {"succeeded", "failed", "canceled", "interrupted"}


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY, principal TEXT NOT NULL, session TEXT NOT NULL,
                  device TEXT NOT NULL, request_id TEXT NOT NULL, text TEXT NOT NULL,
                  status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
                  result TEXT, error TEXT,
                  UNIQUE(principal, request_id));
                CREATE INDEX IF NOT EXISTS jobs_scope ON jobs(principal, session, created);
                CREATE TABLE IF NOT EXISTS actions (
                  job TEXT NOT NULL, step INTEGER NOT NULL, status TEXT NOT NULL,
                  payload TEXT NOT NULL, evidence TEXT, updated REAL NOT NULL,
                  PRIMARY KEY(job, step));
                CREATE TABLE IF NOT EXISTS notes (
                  id TEXT PRIMARY KEY, principal TEXT NOT NULL, text TEXT NOT NULL,
                  created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS devices (
                  id TEXT PRIMARY KEY, principal TEXT NOT NULL, first_seen REAL NOT NULL,
                  last_seen REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS device_labels (
                  device TEXT PRIMARY KEY, principal TEXT NOT NULL, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS oauth_states (
                  hash TEXT PRIMARY KEY, expires REAL NOT NULL);
            """)
        path.chmod(0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def create(self, principal, session, device, request_id, text, max_pending=50):
        now = time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT * FROM jobs WHERE principal=? AND request_id=?", (principal, request_id)
            ).fetchone()
            if previous:
                return self.decode(previous), False
            pending = db.execute(
                "SELECT count(*) FROM jobs WHERE status IN ('queued','running')"
            ).fetchone()[0]
            if pending >= max_pending:
                raise OverflowError("La cola está llena; inténtalo más tarde")
            job_id = uuid.uuid4().hex[:16]
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (job_id, principal, session, device, request_id, text, "queued", now, now,
                        None, None))
            db.execute("INSERT INTO devices VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                       "last_seen=excluded.last_seen", (device, principal, now, now))
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return self.decode(row), True

    @staticmethod
    def decode(row):
        if row is None:
            return None
        value = dict(row)
        value["result"] = json.loads(value["result"]) if value["result"] else None
        return value

    def get(self, job_id, principal):
        with self.connection() as db:
            return self.decode(db.execute("SELECT * FROM jobs WHERE id=? AND principal=?",
                                          (job_id, principal)).fetchone())

    def latest(self, principal, device=None):
        with self.connection() as db:
            query = "SELECT * FROM jobs WHERE principal=?"
            args = [principal]
            if device:
                query += " AND device=?"
                args.append(device)
            return self.decode(db.execute(query + " ORDER BY created DESC LIMIT 1", args).fetchone())

    def recent(self, principal, limit=20):
        with self.connection() as db:
            return [self.decode(row) for row in db.execute(
                "SELECT * FROM jobs WHERE principal=? ORDER BY created DESC LIMIT ?",
                (principal, limit))]

    def history(self, principal, session, before):
        with self.connection() as db:
            rows = db.execute("SELECT text,result FROM jobs WHERE principal=? AND session=? "
                              "AND status='succeeded' AND created<? ORDER BY created DESC LIMIT 6",
                              (principal, session, before)).fetchall()
            return [{"user": r["text"], "assistant": json.loads(r["result"])["text"]}
                    for r in reversed(rows)]

    def claim(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT j.* FROM jobs j WHERE j.status='queued' AND NOT EXISTS "
                             "(SELECT 1 FROM jobs r WHERE r.status='running' AND "
                             "r.principal=j.principal AND r.session=j.session) "
                             "ORDER BY j.created LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE jobs SET status='running',updated=? WHERE id=?",
                           (time.time(), row["id"]))
            return self.decode(row)

    def finish(self, job_id, status, result=None, error=None):
        assert status in TERMINAL
        with self.connection() as db:
            db.execute("UPDATE jobs SET status=?,result=?,error=?,updated=? WHERE id=? "
                       "AND status='running'", (status, json.dumps(result, ensure_ascii=False)
                                                if result else None, error, time.time(), job_id))

    def cancel(self, job_id, principal):
        with self.connection() as db:
            r = db.execute("UPDATE jobs SET status='canceled',error=?,updated=? WHERE id=? "
                           "AND principal=? AND status IN ('queued','running')",
                           ("Cancelado. Las acciones ya enviadas pueden haberse ejecutado.",
                            time.time(), job_id, principal))
            return r.rowcount == 1

    def recover(self):
        with self.connection() as db:
            r = db.execute("UPDATE jobs SET status='interrupted',error=?,updated=? "
                           "WHERE status='running'",
                           ("Servicio reiniciado. No se repiten acciones de resultado incierto.",
                            time.time()))
            return r.rowcount

    def action_start(self, job_id, step, payload):
        with self.connection() as db:
            try:
                db.execute("INSERT INTO actions VALUES (?,?,?,?,?,?)",
                           (job_id, step, "sent", json.dumps(payload), None, time.time()))
            except sqlite3.IntegrityError:
                raise RuntimeError("Acción ya enviada; consulta su evidencia antes de repetir") from None

    def action_finish(self, job_id, step, status, evidence):
        with self.connection() as db:
            db.execute("UPDATE actions SET status=?,evidence=?,updated=? WHERE job=? AND step=?",
                       (status, json.dumps(evidence, ensure_ascii=False), time.time(), job_id, step))

    def evidence(self, job_id):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT step,status,payload,evidence,updated FROM actions WHERE job=? ORDER BY step",
                (job_id,))]

    def notes(self, principal):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT id,text,created FROM notes WHERE principal=? ORDER BY created LIMIT 100", (principal,))]

    def note(self, principal, text):
        key = uuid.uuid4().hex[:16]
        with self.connection() as db:
            if db.execute("SELECT count(*) FROM notes WHERE principal=?", (principal,)).fetchone()[0] >= 100:
                raise ValueError("Tienes cien notas; elimina una antes de guardar otra")
            db.execute("INSERT INTO notes VALUES (?,?,?,?)", (key, principal, text, time.time()))
        return key

    def forget(self, principal, key):
        with self.connection() as db:
            return db.execute("DELETE FROM notes WHERE principal=? AND id=?", (principal, key)).rowcount

    def prune(self, days):
        with self.connection() as db:
            cutoff = time.time() - days * 86400
            db.execute("DELETE FROM actions WHERE job IN (SELECT id FROM jobs WHERE created<? "
                       "AND status NOT IN ('queued','running'))", (cutoff,))
            db.execute("DELETE FROM jobs WHERE created<? AND status NOT IN ('queued','running')",
                       (cutoff,))

    def backup(self, target: Path):
        with self.connection() as db, sqlite3.connect(target) as dest:
            db.backup(dest)
        target.chmod(0o600)

    def oauth_issue(self, state):
        now = time.time()
        with self.connection() as db:
            db.execute("DELETE FROM oauth_states WHERE expires<?", (now,))
            db.execute("INSERT INTO oauth_states VALUES (?,?)",
                       (hashlib.sha256(state.encode()).hexdigest(), now + 600))

    def label_device(self, principal, device, name):
        with self.connection() as db:
            if not db.execute("SELECT 1 FROM devices WHERE id=? AND principal=?",
                              (device, principal)).fetchone():
                return False
            db.execute("INSERT INTO device_labels VALUES (?,?,?) ON CONFLICT(device) "
                       "DO UPDATE SET name=excluded.name", (device, principal, name[:100]))
            return True

    def devices(self, principal):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT d.id,d.first_seen,d.last_seen,l.name FROM devices d LEFT JOIN "
                "device_labels l ON l.device=d.id AND l.principal=d.principal "
                "WHERE d.principal=? ORDER BY d.last_seen DESC", (principal,))]

    def oauth_consume(self, state):
        key = hashlib.sha256(state.encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT expires FROM oauth_states WHERE hash=?", (key,)).fetchone()
            db.execute("DELETE FROM oauth_states WHERE hash=?", (key,))
            return bool(row and row["expires"] > time.time())
