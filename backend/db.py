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
"""


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
