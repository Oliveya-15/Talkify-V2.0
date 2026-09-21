"""
Stage 8: citation mapping.

Turns retrieved chunks (which the model was shown as numbered excerpts)
into structured citation records the frontend can render as clickable
"source.pdf, page 4" links — and that get persisted as MessageSource
rows so a citation is never just a string, it's a real link to a real
DocumentChunk row. Nothing here is invented: if a chunk wasn't actually
retrieved and shown to the model, it cannot appear as a citation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Citation:
    index: int          # matches the [1], [2] markers in the prompt/answer
    chunk_id: str
    document_id: str
    source_name: str
    page: int
    excerpt: str
    relevance_score: float


def build_citations(retrieved_chunks: list[dict]) -> list[Citation]:
    """
    retrieved_chunks: ordered list of dicts with keys
        chunk_id, document_id, source_name, page, text, final_score
    (produced by services/retrieval_service.py after hybrid ranking)
    """
    citations = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        citations.append(Citation(
            index=i,
            chunk_id=chunk["chunk_id"],
            document_id=chunk["document_id"],
            source_name=chunk["source_name"],
            page=chunk["page"],
            excerpt=chunk["text"][:280],
            relevance_score=chunk["final_score"],
        ))
    return citations


def excerpts_for_prompt(retrieved_chunks: list[dict]) -> list[dict]:
    """Same ordering as build_citations, formatted for prompt_builder.build_context_block."""
    return [
        {"index": i, "source": c["source_name"], "page": c["page"], "text": c["text"]}
        for i, c in enumerate(retrieved_chunks, start=1)
    ]
