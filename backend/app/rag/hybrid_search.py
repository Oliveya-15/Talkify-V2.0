"""
Stage 6: hybrid retrieval — merges semantic and keyword results.

This module is deliberately pure (no DB, no FAISS, no embedding calls)
so it can be unit-tested with plain Python dicts (see
tests/test_hybrid_search.py). The actual wiring to the database and
FAISS lives in services/retrieval_service.py.

Score combination: scores from the two methods are on different scales
(cosine similarity is roughly 0-1; BM25 is unbounded), so each is
min-max normalized to 0-1 within its own result set before combining.
The combined score is a weighted sum:

    final_score = SEMANTIC_WEIGHT * semantic_norm + KEYWORD_WEIGHT * keyword_norm

Defaults (0.7 / 0.3, from settings) are a starting point from the docs,
not a proven-optimal split — see backend/evaluation/ for how to measure
retrieval quality and tune these weights against real questions rather
than assuming they're right.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass
class RetrievedChunk:
    chunk_id: str
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    final_score: float = 0.0


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 1.0 for k in scores}  # all equal → treat as equally relevant
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def merge_results(
    semantic_hits: dict[str, float],
    keyword_hits: dict[str, float],
    semantic_weight: float | None = None,
    keyword_weight: float | None = None,
) -> list[RetrievedChunk]:
    """
    semantic_hits / keyword_hits: {chunk_id: raw_score}
    Returns chunks sorted by final_score descending, deduplicated by chunk_id
    (a chunk found by both methods gets credit from both, not counted twice).
    """
    semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
    keyword_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

    sem_norm = _normalize(semantic_hits)
    key_norm = _normalize(keyword_hits)

    all_ids = set(sem_norm) | set(key_norm)
    merged = []
    for chunk_id in all_ids:
        s = sem_norm.get(chunk_id, 0.0)
        k = key_norm.get(chunk_id, 0.0)
        final = semantic_weight * s + keyword_weight * k
        merged.append(RetrievedChunk(
            chunk_id=chunk_id,
            semantic_score=semantic_hits.get(chunk_id, 0.0),
            keyword_score=keyword_hits.get(chunk_id, 0.0),
            final_score=final,
        ))

    merged.sort(key=lambda c: c.final_score, reverse=True)
    return merged
