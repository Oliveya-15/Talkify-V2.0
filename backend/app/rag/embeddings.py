"""
Stage 3 of the RAG pipeline: embeddings.

An embedding model turns text into a fixed-length vector of numbers
such that semantically similar text ends up with vectors that are
close together (measured by cosine similarity).

ARCHITECTURE NOTE — why this calls a hosted API instead of running a
model locally:
The original design ran a small sentence-transformers model locally via
PyTorch, specifically to avoid any per-call cost or external dependency.
In practice, PyTorch itself — independent of which model you load into
it — needs somewhere between 200MB and 1GB+ of resident memory once it's
actually running, and every genuinely free, card-free hosting tier in
2026 caps out around 512MB. No amount of thread-limiting, batching, or
memory-trimming changes the fact that a transformer model has to
physically exist in RAM to do anything; several rounds of exactly that
tuning still weren't enough. Removing PyTorch from the backend entirely
— rather than continuing to fight its footprint — is what actually
makes free-tier deployment reliable.

The trade-off, stated plainly: embedding generation now requires
internet access and a free Google AI Studio API key (GEMINI_API_KEY).
Unlike LLM generation (which has a genuine extractive fallback when no
Groq key is set — see chat_service.py), there is no meaningful local
fallback for embeddings in a semantic-search pipeline. If GEMINI_API_KEY
isn't set, document processing fails clearly and immediately (see
_require_api_key below) rather than hanging or silently doing nothing.

Everything downstream of this module — FAISS indexing, hybrid search,
citations — is completely unchanged: EMBEDDING_DIM is still 384, Gemini
is just asked to produce vectors at that dimensionality via its
outputDimensionality parameter.
"""
from __future__ import annotations

import time

import numpy as np
import requests

from app.config import settings

_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:batchEmbedContents"
)

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2  # doubles each retry: 2s, 4s, 8s


class EmbeddingConfigError(Exception):
    """Raised when GEMINI_API_KEY is missing — a configuration problem,
    not a transient failure, so callers shouldn't retry this one."""


class EmbeddingAPIError(Exception):
    """Raised when the Gemini API call itself fails after retries
    (network error, rate limit, invalid key, etc.)."""


def _require_api_key() -> str:
    if not settings.GEMINI_API_KEY:
        raise EmbeddingConfigError(
            "GEMINI_API_KEY is not configured. Document processing requires it "
            "— there is no local embedding fallback. Get a free key (no card) "
            "at https://aistudio.google.com/apikey and set it in your "
            "environment variables."
        )
    return settings.GEMINI_API_KEY


def _embed_batch(texts: list[str], task_type: str) -> list[list[float]]:
    """
    Calls Gemini's batchEmbedContents for one batch of texts (size bounded
    by settings.EMBEDDING_BATCH_SIZE by the caller), with retries on
    transient failures (network errors, HTTP 429/5xx).
    """
    api_key = _require_api_key()
    model = settings.GEMINI_EMBEDDING_MODEL
    url = _EMBED_URL.format(model=model)

    payload = {
        "requests": [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]},
                "taskType": task_type,
                "outputDimensionality": settings.EMBEDDING_DIM,
            }
            for text in texts
        ]
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 429 or response.status_code >= 500:
                # Rate limited or a transient server error — worth retrying.
                last_error = EmbeddingAPIError(
                    f"Gemini API returned {response.status_code}: {response.text[:300]}"
                )
            elif not response.ok:
                # A 4xx other than 429 (bad request, invalid key, etc.) won't
                # fix itself on retry — fail immediately with the real reason.
                raise EmbeddingAPIError(
                    f"Gemini API returned {response.status_code}: {response.text[:300]}"
                )
            else:
                data = response.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) != len(texts):
                    raise EmbeddingAPIError(
                        f"Gemini API returned {len(embeddings)} embeddings for "
                        f"{len(texts)} requested texts — response did not match request."
                    )
                return [e["values"] for e in embeddings]
        except requests.RequestException as e:
            last_error = EmbeddingAPIError(f"Network error calling Gemini API: {e}")

        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_BACKOFF_SECONDS * (2 ** attempt))

    raise last_error or EmbeddingAPIError("Gemini API call failed for an unknown reason.")


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """FAISS's IndexFlatIP (see vector_store.py) treats inner product as
    cosine similarity only when every vector is unit-length — Gemini's
    embeddings aren't guaranteed to already be normalized, so this is
    done explicitly rather than assumed.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # avoid division by zero for a (theoretical) all-zero vector
    return vectors / norms


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """
    Returns a (len(texts), EMBEDDING_DIM) float32 array, L2-normalized so
    that a dot product between two rows equals their cosine similarity.

    task_type: "RETRIEVAL_DOCUMENT" for chunks being indexed (the
    default — this is what pipeline.py calls), "RETRIEVAL_QUERY" for a
    user's search question (see embed_query below). Gemini's embedding
    model is trained to produce better-matched vectors for these two
    roles when told which one it's embedding, rather than treating
    every input identically.
    """
    if not texts:
        return np.empty((0, settings.EMBEDDING_DIM), dtype="float32")

    batch_size = settings.EMBEDDING_BATCH_SIZE
    all_vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        all_vectors.extend(_embed_batch(batch, task_type))

    result = np.array(all_vectors, dtype="float32")
    return _l2_normalize(result)


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]