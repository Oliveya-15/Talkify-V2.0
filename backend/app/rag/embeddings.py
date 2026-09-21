"""
Stage 3 of the RAG pipeline: embeddings.

An embedding model turns text into a fixed-length vector of numbers
such that semantically similar text ends up with vectors that are
close together (measured by cosine similarity). We use a small, free,
local model (sentence-transformers/all-MiniLM-L6-v2 — 384 dimensions,
~90MB, runs fine on CPU) instead of a hosted embedding API, so
embedding never costs money or requires internet at inference time.

The model is loaded lazily and cached at module level: loading it is
the slow part (reading ~90MB of weights from disk into memory), so we
want to pay that cost once per process, not once per request.
"""
from __future__ import annotations

import threading

import numpy as np

from app.config import settings

_model = None
_model_lock = threading.Lock()


def get_embedding_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # re-check inside the lock (double-checked locking)
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns a (len(texts), EMBEDDING_DIM) float32 array, L2-normalized
    so that a dot product between two rows equals their cosine similarity.
    """
    if not texts:
        return np.empty((0, settings.EMBEDDING_DIM), dtype="float32")
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vectors.astype("float32")


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])[0]
