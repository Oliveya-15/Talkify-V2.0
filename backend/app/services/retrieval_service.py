"""
The database-and-index-aware half of retrieval. rag/hybrid_search.py is
pure score-merging logic; this module does the actual work of running
semantic + keyword search across one or more documents and turning the
results into fully-hydrated chunk dicts (with source file name, page,
text) ready for prompt_builder / citations.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.rag import embeddings, hybrid_search, keyword_search, vector_store


def retrieve(db: Session, document_ids: list[str], question: str, top_k: int | None = None) -> list[dict]:
    """
    Runs hybrid retrieval across all given documents and returns the
    top_k chunks as dicts: {chunk_id, document_id, source_name, page, text, final_score}
    """
    top_k = top_k or settings.TOP_K_FINAL
    if not document_ids:
        return []

    query_vector = embeddings.embed_query(question)

    # --- semantic search: per document (each has its own FAISS index) ---
    semantic_hits: dict[str, float] = {}
    vector_ref_to_doc: dict[tuple[str, int], str] = {}  # (document_id, vector_ref) -> chunk_id lookup helper
    for doc_id in document_ids:
        hits = vector_store.search(doc_id, query_vector, settings.TOP_K_SEMANTIC)
        if not hits:
            continue
        # map vector_ref -> chunk row for this document
        vector_refs = [ref for ref, _ in hits]
        rows = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc_id, DocumentChunk.vector_ref.in_(vector_refs))
            .all()
        )
        ref_to_chunk = {row.vector_ref: row for row in rows}
        for ref, score in hits:
            chunk = ref_to_chunk.get(ref)
            if chunk:
                semantic_hits[chunk.id] = score

    # --- keyword search: across all documents at once (single FTS index) ---
    keyword_raw = keyword_search.search(document_ids, question, settings.TOP_K_KEYWORD)
    keyword_hits: dict[str, float] = dict(keyword_raw)

    # --- merge ---
    merged = hybrid_search.merge_results(semantic_hits, keyword_hits)
    top_chunks = merged[:top_k]
    if not top_chunks:
        return []

    chunk_ids = [c.chunk_id for c in top_chunks]
    chunk_rows = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
    chunk_by_id = {row.id: row for row in chunk_rows}

    doc_rows = db.query(Document).filter(Document.id.in_(document_ids)).all()
    doc_by_id = {row.id: row for row in doc_rows}

    results = []
    for ranked in top_chunks:
        chunk = chunk_by_id.get(ranked.chunk_id)
        if not chunk:
            continue
        doc = doc_by_id.get(chunk.document_id)
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "source_name": doc.file_name if doc else "unknown",
            "page": chunk.page_number or 1,
            "text": chunk.content,
            "final_score": ranked.final_score,
        })
    return results
