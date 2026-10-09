"""SQLite persistence for documents and their extracted text chunks.

Everything stays on-device (PRD FR-07). Two tables:
  - documents: one row per ingested file, with provenance metadata.
  - text_chunks: passage-level rows carrying page + section metadata so
    citation badges can be built from REAL retrieval data, never from the
    model's invention (PRD section 15: "model invents citations" mitigation).
"""

from __future__ import annotations

import os
import sqlite3
from typing import Iterable, List, Optional

import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    source_path TEXT,
    media_type  TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS text_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page        INTEGER,
    section     TEXT,
    content     TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON text_chunks(document_id);

CREATE TABLE IF NOT EXISTS checklist_items (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    category  TEXT NOT NULL,
    label     TEXT NOT NULL,
    done      INTEGER NOT NULL DEFAULT 0,
    position  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    supported  INTEGER NOT NULL,
    citations  TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Vetted, general preparedness content (PRD FR-06). Deliberately generic: no
# single checklist fits every household or emergency, and the UI must say so.
_SEED_CHECKLIST = [
    ("Supplies", "3 liters of water per person per day for 3 days"),
    ("Supplies", "Non-perishable food and a manual can opener"),
    ("Supplies", "First-aid kit and any prescription medications"),
    ("Supplies", "Flashlight with extra batteries"),
    ("Supplies", "Battery or hand-crank radio"),
    ("Documents", "Copies of IDs and important papers in a waterproof bag"),
    ("Documents", "Cash in small bills"),
    ("Communication", "Household meeting point and out-of-area contact"),
    ("Communication", "Phones charged plus a power bank"),
    ("Household", "Plan and routes to the nearest evacuation center"),
    ("Household", "Check on elderly, disabled, or medical-needs members"),
]


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce FK cascade so removing a document clears its indexed content
    # (PRD FR-02 acceptance criterion).
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
        # Seed the preparedness checklist once (PRD FR-06).
        count = conn.execute("SELECT COUNT(*) FROM checklist_items").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO checklist_items (category, label, position) "
                "VALUES (?, ?, ?)",
                [(cat, lbl, i) for i, (cat, lbl) in enumerate(_SEED_CHECKLIST)],
            )


def insert_document(name: str, media_type: str, source_path: Optional[str],
                    chunks: Iterable[dict]) -> int:
    """Insert a document and its chunks atomically. Returns the document id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documents (name, media_type, source_path) VALUES (?, ?, ?)",
            (name, media_type, source_path),
        )
        doc_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO text_chunks (document_id, page, section, content) "
            "VALUES (?, ?, ?, ?)",
            [(doc_id, c.get("page"), c.get("section"), c["content"]) for c in chunks],
        )
        return int(doc_id)


def list_documents() -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.name, d.media_type, d.source_path, d.created_at,
                   COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN text_chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_chunks() -> List[dict]:
    """Full corpus for the in-memory BM25 index (demo corpus is small)."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.document_id, d.name AS doc_name,
                   c.page, c.section, c.content
            FROM text_chunks c
            JOIN documents d ON d.id = c.document_id
            """
        ).fetchall()
        return [dict(r) for r in rows]


def delete_document(doc_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cur.rowcount > 0


# --- Checklist (PRD FR-06) -------------------------------------------------
def list_checklist() -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category, label, done, position FROM checklist_items "
            "ORDER BY position ASC, id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_checklist_item(category: str, label: str) -> int:
    with get_conn() as conn:
        pos = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 "
                           "FROM checklist_items").fetchone()[0]
        cur = conn.execute(
            "INSERT INTO checklist_items (category, label, position) "
            "VALUES (?, ?, ?)", (category, label, pos),
        )
        return int(cur.lastrowid)


def set_checklist_done(item_id: int, done: bool) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE checklist_items SET done = ? WHERE id = ?",
            (1 if done else 0, item_id),
        )
        return cur.rowcount > 0


def delete_checklist_item(item_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0


# --- Chat history (PRD FR-07) ---------------------------------------------
def add_chat_message(question: str, answer: str, supported: bool,
                     citations_json: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO chat_messages (question, answer, supported, citations) "
            "VALUES (?, ?, ?, ?)",
            (question, answer, 1 if supported else 0, citations_json),
        )
        return int(cur.lastrowid)


def list_chat(limit: int = 50) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, question, answer, supported, citations, created_at "
            "FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["supported"] = bool(d["supported"])
            out.append(d)
        return out


def clear_chat() -> int:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM chat_messages")
        return cur.rowcount
