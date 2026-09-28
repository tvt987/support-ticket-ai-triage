"""SQLite queue stores decisions, never raw customer messages."""
import json
import sqlite3
from pathlib import Path


class ReviewQueue:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY, decision_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending_review','ready','approved','rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def connect(self):
        return sqlite3.connect(self.path)

    def save(self, ticket_id: str, decision: dict) -> dict:
        status = "pending_review" if decision["needs_human_review"] else "ready"
        with self.connect() as db:
            db.execute("INSERT INTO tickets (ticket_id, decision_json, status) VALUES (?, ?, ?)",
                       (ticket_id, json.dumps(decision), status))
        return {"ticket_id": ticket_id, "status": status, **decision}

    def get(self, ticket_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT decision_json, status FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        return {"ticket_id": ticket_id, "status": row[1], **json.loads(row[0])} if row else None

    def list_pending(self, limit: int = 50) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT ticket_id, decision_json, status FROM tickets WHERE status='pending_review' ORDER BY created_at, ticket_id LIMIT ?", (limit,)).fetchall()
        return [{"ticket_id": id_, "status": status, **json.loads(data)} for id_, data, status in rows]

    def review(self, ticket_id: str, status: str) -> bool:
        if status not in {"approved", "rejected"}:
            raise ValueError("Invalid review status")
        with self.connect() as db:
            changed = db.execute("UPDATE tickets SET status=? WHERE ticket_id=? AND status='pending_review'", (status, ticket_id)).rowcount
        return bool(changed)
