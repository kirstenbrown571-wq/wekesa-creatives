"""
TERRA Database Layer
Uses SQLite for development / single-server deployment.
For production scale: swap connection string to PostgreSQL.

Security hardening:
  - All queries use parameterised statements (no string interpolation)
  - Sensitive columns (password_hash) never returned in SELECT *
  - Audit log table for all auth events
  - Soft-delete pattern for user accounts
"""
import sqlite3
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = os.environ.get("TERRA_DB_PATH", "terra_data.db")


class Database:
    def __init__(self):
        self.path = DB_PATH
        self._init_schema()

    # ── Connection helper ─────────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Schema bootstrap ──────────────────────────────────────────
    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT    NOT NULL,
                email            TEXT    NOT NULL UNIQUE,
                password_hash    TEXT    NOT NULL,
                org              TEXT    NOT NULL,
                plan             TEXT    NOT NULL DEFAULT 'starter',
                agreed_terms     INTEGER NOT NULL DEFAULT 0,
                agreed_privacy   INTEGER NOT NULL DEFAULT 0,
                agreed_at        TEXT,
                marketing        INTEGER NOT NULL DEFAULT 0,
                esg_score        INTEGER,
                active           INTEGER NOT NULL DEFAULT 1,
                created_at       TEXT    NOT NULL,
                last_login       TEXT
            );

            CREATE TABLE IF NOT EXISTS calculations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                inputs_json TEXT    NOT NULL,
                results_json TEXT   NOT NULL,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                event       TEXT    NOT NULL,
                ip_hash     TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS data_consent (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                consent_type TEXT   NOT NULL,
                granted     INTEGER NOT NULL,
                ip_hash     TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_calc_user   ON calculations(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user  ON audit_log(user_id);
            """)

    # ── User CRUD ─────────────────────────────────────────────────
    def create_user(self, name, email, password_hash, org, plan,
                    agreed_terms, agreed_privacy, marketing=False):
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO users
                   (name,email,password_hash,org,plan,
                    agreed_terms,agreed_privacy,agreed_at,marketing,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (name, email, password_hash, org, plan,
                 int(agreed_terms), int(agreed_privacy),
                 now if agreed_terms else None,
                 int(marketing), now)
            )
            # record consent
            uid = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()['id']
            for ctype, granted in [("terms", agreed_terms), ("privacy", agreed_privacy),
                                   ("marketing", marketing)]:
                conn.execute(
                    "INSERT INTO data_consent (user_id,consent_type,granted,created_at) VALUES (?,?,?,?)",
                    (uid, ctype, int(granted), now)
                )
        return True

    def get_user_by_email(self, email):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id,name,email,password_hash,org,plan,esg_score,active FROM users WHERE email=? AND active=1",
                (email,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id,name,email,org,plan,esg_score,agreed_terms,agreed_privacy,created_at FROM users WHERE id=? AND active=1",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_user(self, user_id, **kwargs):
        allowed = {"name", "org", "esg_score", "last_login"}
        sets  = ", ".join(f"{k}=?" for k in kwargs if k in allowed)
        vals  = [v for k, v in kwargs.items() if k in allowed]
        if not sets:
            return
        with self._conn() as conn:
            conn.execute(f"UPDATE users SET {sets} WHERE id=?", (*vals, user_id))

    def update_password_hash(self, user_id, new_hash):
        with self._conn() as conn:
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))

    def delete_user(self, user_id):
        """Soft delete — preserves audit trail, anonymises PII."""
        anon_email = f"deleted_{user_id}@terra-deleted.local"
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET active=0, name='[DELETED]', email=?, org='[DELETED]' WHERE id=?",
                (anon_email, user_id)
            )

    # ── Calculations ──────────────────────────────────────────────
    def save_calculation(self, user_id, inputs, results):
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO calculations (user_id,inputs_json,results_json,created_at) VALUES (?,?,?,?)",
                (user_id, json.dumps(inputs), json.dumps(results), now)
            )

    def get_calculations(self, user_id, limit=50):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id,inputs_json,results_json,created_at FROM calculations WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            return [{"id": r['id'], "inputs": json.loads(r['inputs_json']),
                     "results": json.loads(r['results_json']),
                     "created_at": r['created_at']} for r in rows]

    # ── Audit log ─────────────────────────────────────────────────
    def log_event(self, user_id, event, ip=None):
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else None
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO audit_log (user_id,event,ip_hash,created_at) VALUES (?,?,?,?)",
                (user_id, event, ip_hash, now)
            )

    # ── Data export (GDPR right of portability) ───────────────────
    def export_user_data(self, user_id):
        user = self.get_user_by_id(user_id)
        calcs = self.get_calculations(user_id)
        with self._conn() as conn:
            consents = [dict(r) for r in conn.execute(
                "SELECT consent_type,granted,created_at FROM data_consent WHERE user_id=?",
                (user_id,)).fetchall()]
        return {
            "export_date": datetime.utcnow().isoformat(),
            "platform": "TERRA Carbon Intelligence Platform",
            "user_profile": {k: v for k, v in user.items() if k not in ("password_hash",)},
            "calculations": calcs,
            "consents": consents,
            "data_controller": "Terra Climate Technologies Ltd",
            "contact": "privacy@terra-carbon.io"
        }