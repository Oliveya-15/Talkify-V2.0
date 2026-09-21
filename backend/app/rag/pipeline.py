"""
Stage-tying module: the full ingestion pipeline from a saved file on
disk to a searchable document. This is the function
services/document_service.py calls after a file is uploaded.

    load_document -> chunk_pages -> embed_texts -> build_index (FAISS)
                                                  -> index_chunks (FTS5)

Returns the list of chunks (with their assigned vector_ref) so the
caller can persist DocumentChunk rows with the right vector_ref values.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.rag import chunking, embeddings, keyword_search, vector_store
from app.rag.loaders import load_document


@dataclass
class IngestedChunk:
    text: str
    page: int
    vector_ref: int


@dataclass
class IngestionResult:
    page_count: int
    chunks: list[IngestedChunk]


def ingest_document(document_id: str, file_path: str, file_type: str) -> IngestionResult:
    pages = load_document(file_path, file_type)
    raw_chunks = chunking.chunk_pages(pages)

    if not raw_chunks:
        return IngestionResult(page_count=len(pages), chunks=[])

    texts = [c.text for c in raw_chunks]
    vectors = embeddings.embed_texts(texts)
    vector_store.build_index(document_id, vectors)

    ingested = [
        IngestedChunk(text=c.text, page=c.page, vector_ref=i)
        for i, c in enumerate(raw_chunks)
    ]
    return IngestionResult(page_count=len(pages), chunks=ingested)


def index_for_keyword_search(document_id: str, chunk_ids: list[str], texts: list[str]) -> None:
    keyword_search.index_chunks(document_id, chunk_ids, texts)


def delete_document_indexes(document_id: str) -> None:
    vector_store.delete_index(document_id)
    keyword_search.delete_document(document_id)
