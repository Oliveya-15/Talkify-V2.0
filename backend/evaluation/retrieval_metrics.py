"""
Retrieval evaluation harness.

Measures whether hybrid retrieval actually finds the right source chunk
for a set of manually-verified questions, instead of assuming it does.
This is what backs up any "evaluation" claim in the README — the
numbers here are computed, not invented, and will be near-meaningless
until you fill in evaluation/dataset.json with real questions about
your own real uploaded documents (see the docstring in dataset.py).

Usage (after uploading documents and noting real document_id/page values):
    python -m evaluation.run_evaluation
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.services import retrieval_service

DATASET_PATH = Path(__file__).parent / "dataset.json"


@dataclass
class EvalCase:
    question: str
    document_ids: list[str]
    expected_document_id: str
    expected_page: int
    notes: str = ""


@dataclass
class EvalResult:
    question: str
    hit_at_k: bool
    rank_of_correct_chunk: int | None  # 1-indexed, None if not found in top_k
    retrieved_count: int


def load_dataset() -> list[EvalCase]:
    if not DATASET_PATH.exists():
        return []
    raw = json.loads(DATASET_PATH.read_text())
    return [EvalCase(**item) for item in raw]


def evaluate_case(db: Session, case: EvalCase, top_k: int = 5) -> EvalResult:
    retrieved = retrieval_service.retrieve(db, case.document_ids, case.question, top_k=top_k)
    rank = None
    for i, chunk in enumerate(retrieved, start=1):
        if chunk["document_id"] == case.expected_document_id and chunk["page"] == case.expected_page:
            rank = i
            break
    return EvalResult(
        question=case.question,
        hit_at_k=rank is not None,
        rank_of_correct_chunk=rank,
        retrieved_count=len(retrieved),
    )


def run_evaluation(db: Session, top_k: int = 5) -> dict:
    cases = load_dataset()
    if not cases:
        return {
            "cases_evaluated": 0,
            "note": "evaluation/dataset.json is empty. Add real questions about "
                    "your own uploaded documents to get meaningful numbers — "
                    "see dataset.json's comment block for the format.",
        }

    results = [evaluate_case(db, c, top_k=top_k) for c in cases]
    hits = sum(1 for r in results if r.hit_at_k)
    precision_at_k = hits / len(results)

    reciprocal_ranks = [1 / r.rank_of_correct_chunk for r in results if r.rank_of_correct_chunk]
    mrr = sum(reciprocal_ranks) / len(results) if results else 0.0

    return {
        "cases_evaluated": len(results),
        f"recall_at_{top_k}": round(precision_at_k, 3),
        "mean_reciprocal_rank": round(mrr, 3),
        "per_question": [
            {"question": r.question, "hit": r.hit_at_k, "rank": r.rank_of_correct_chunk}
            for r in results
        ],
    }


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        print(json.dumps(run_evaluation(db), indent=2))
    finally:
        db.close()
