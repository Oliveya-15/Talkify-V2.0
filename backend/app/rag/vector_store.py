"""
Stage 4: vector indexing and semantic search, backed by FAISS.

Design choice: one FAISS index per document (stored at
VECTOR_INDEX_DIR/{document_id}.index) rather than one giant index for
the whole app. This keeps per-document processing independent (deleting
a document just deletes its file), and multi-document search is done by
querying each relevant document's index and merging results — simple
and easy to reason about, at the cost of being slower than a single
index at very large scale (a fine trade-off for a student project).

We use IndexFlatIP (exact inner-product search). Since embeddings are
L2-normalized, inner product == cosine similarity. FlatIP does a brute
force scan, which is exact (no approximation) and plenty fast for the
number of chunks a single document produces.
"""
from __future__ import annotations

import os

import faiss
import numpy as np

from app.config import settings


def _index_path(document_id: str) -> str:
    os.makedirs(settings.VECTOR_INDEX_DIR, exist_ok=True)
    return os.path.join(settings.VECTOR_INDEX_DIR, f"{document_id}.index")


def build_index(document_id: str, vectors: np.ndarray) -> None:
    """Builds and persists a FAISS index for one document's chunk vectors.
    The row order of `vectors` must match `DocumentChunk.vector_ref` values.
    """
    index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
    if len(vectors) > 0:
        index.add(vectors)
    faiss.write_index(index, _index_path(document_id))


def load_index(document_id: str) -> faiss.Index | None:
    path = _index_path(document_id)
    if not os.path.exists(path):
        return None
    return faiss.read_index(path)


def delete_index(document_id: str) -> None:
    path = _index_path(document_id)
    if os.path.exists(path):
        os.remove(path)


def search(document_id: str, query_vector: np.ndarray, top_k: int) -> list[tuple[int, float]]:
    """Returns [(vector_ref, similarity_score), ...] sorted by score desc."""
    index = load_index(document_id)
    if index is None or index.ntotal == 0:
        return []
    top_k = min(top_k, index.ntotal)
    scores, indices = index.search(query_vector.reshape(1, -1), top_k)
    return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx != -1]
