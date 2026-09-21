"""
Stage 5: keyword search.

Semantic search (vector_store.py) is great at matching meaning but can
miss questions that hinge on an exact term (a product name, a specific
number, an acronym) that doesn't have a strong semantic "neighbor".
Keyword search covers that gap.

We use SQLite's FTS5 extension as a separate, tiny full-text index
(distinct from the app's main database) — it's free, ships with
Python's stdlib sqlite3 build, and needs no extra service to run. If
DATABASE_URL is Postgres in production, this module still works
unchanged: it's an independent search index, not the system of record.
"""
from __future__ import annotations

import os
import sqlite3

from app.config import settings


def _fts_db_path() -> str:
    os.makedirs(settings.VECTOR_INDEX_DIR, exist_ok=True)
    return os.path.join(settings.VECTOR_INDEX_DIR, "keyword_index.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_fts_db_path())
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5("
        "chunk_id UNINDEXED, document_id UNINDEXED, content"
        ")"
    )
    return conn


def index_chunks(document_id: str, chunk_ids: list[str], texts: list[str]) -> None:
    conn = _connect()
    with conn:
        conn.execute("DELETE FROM chunks_fts WHERE document_id = ?", (document_id,))
        conn.executemany(
            "INSERT INTO chunks_fts (chunk_id, document_id, content) VALUES (?, ?, ?)",
            [(cid, document_id, text) for cid, text in zip(chunk_ids, texts)],
        )
    conn.close()


def delete_document(document_id: str) -> None:
    conn = _connect()
    with conn:
        conn.execute("DELETE FROM chunks_fts WHERE document_id = ?", (document_id,))
    conn.close()


def _sanitize_query(query: str) -> str:
    """FTS5 query syntax treats punctuation specially; we quote each
    word so a question like "What's RAG?" doesn't raise a syntax error.
    """
    words = [w for w in query.replace('"', "").split() if w]
    return " OR ".join(f'"{w}"' for w in words) if words else '""'


def search(document_ids: list[str], query: str, top_k: int) -> list[tuple[str, float]]:
    """Returns [(chunk_id, bm25_score), ...] sorted by relevance desc.
    FTS5's bm25() returns *lower is better*, so we negate it to make
    higher-is-better consistent with the semantic search scores.
    """
    if not document_ids:
        return []
    conn = _connect()
    placeholders = ",".join("?" for _ in document_ids)
    fts_query = _sanitize_query(query)
    try:
        rows = conn.execute(
            f"""
            SELECT chunk_id, bm25(chunks_fts) AS rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ? AND document_id IN ({placeholders})
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, *document_ids, top_k),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return [(chunk_id, -score) for chunk_id, score in rows]
