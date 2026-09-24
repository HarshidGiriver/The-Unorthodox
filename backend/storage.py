"""SQLite storage for the local application. All writes use explicit transactions."""

from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS borrowers (
 customer_id TEXT PRIMARY KEY, payload TEXT NOT NULL, simulation INTEGER NOT NULL,
 email TEXT, phone TEXT, contact_verified INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS loans (
 customer_id TEXT PRIMARY KEY REFERENCES borrowers(customer_id), version INTEGER NOT NULL DEFAULT 1,
 principal REAL NOT NULL, emi REAL NOT NULL, tenure INTEGER NOT NULL, rate REAL NOT NULL,
 schedule TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
 username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('underwriter','borrower')),
 customer_id TEXT REFERENCES borrowers(customer_id), failed_attempts INTEGER NOT NULL DEFAULT 0,
 locked_until REAL NOT NULL DEFAULT 0,
 CHECK((role='borrower' AND customer_id IS NOT NULL) OR (role='underwriter' AND customer_id IS NULL))
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES users(username), expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS proposals (
 id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES borrowers(customer_id), version INTEGER NOT NULL,
 loan_version INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('draft','approved','rejected','consented','active')),
 terms TEXT NOT NULL, terms_hash TEXT NOT NULL, score_context TEXT NOT NULL,
 created_by TEXT NOT NULL REFERENCES users(username), created_at TEXT NOT NULL,
 UNIQUE(customer_id,version)
);
CREATE TABLE IF NOT EXISTS decisions (
 proposal_id TEXT PRIMARY KEY REFERENCES proposals(id), actor TEXT NOT NULL, decision TEXT NOT NULL,
 reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consents (
 proposal_id TEXT PRIMARY KEY REFERENCES proposals(id), actor TEXT NOT NULL,
 terms_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id TEXT REFERENCES proposals(id),
 actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
 id TEXT PRIMARY KEY, proposal_id TEXT NOT NULL REFERENCES proposals(id),
 channel TEXT NOT NULL CHECK(channel IN ('email','sms')), payload TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
 available_at REAL NOT NULL DEFAULT 0, claimed_at REAL, claim_token TEXT,
 receipt TEXT, last_error TEXT, UNIQUE(proposal_id, channel)
);
CREATE TABLE IF NOT EXISTS payments (
 reference TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES borrowers(customer_id),
 loan_version INTEGER NOT NULL, amount REAL NOT NULL, actor TEXT NOT NULL, paid_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("KINTSUGI_DB_PATH", Path.home() / ".kintsugi" / "app.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
