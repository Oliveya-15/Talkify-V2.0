"""
Stage 2 of the RAG pipeline: chunking.

This is a from-scratch reimplementation of the "recursive character
splitter" idea (the same one LangChain ships), kept here instead of
imported so the actual splitting logic is visible and explainable
rather than hidden inside a framework.

Why chunk at all? Embedding models and LLM context windows both have
size limits, and retrieval works better over small, focused pieces of
text than over whole documents — a 40-page PDF chunked into ~1000-char
pieces lets us hand the LLM just the 3-5 pieces that are actually
relevant to a question, instead of the whole document.

Why these separators, in this order? We try to split on the biggest
structural boundary first (paragraph breaks), and only fall back to
smaller boundaries (sentences, then words, then raw characters) if a
piece is still too big. This avoids cutting a sentence in half whenever
a paragraph boundary is available.

Defaults: chunk_size=1000, overlap=200 characters. These aren't proven
optimal — they're a reasonable starting point recommended by the docs
(800-1200 / 150-250). backend/evaluation/ is where you'd actually test
different values against the evaluation dataset and pick the best one.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    text: str
    page: int


def _split_text(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Recursively split `text` using the first separator that actually
    breaks it into pieces small enough to satisfy chunk_size, falling
    back to the next separator (and eventually raw slicing) otherwise.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        # Base case: no separator left, hard-slice the text.
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, *rest_separators = separators
    pieces = text.split(sep) if sep else list(text)

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = current + (sep if current else "") + piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(piece) > chunk_size:
                # This single piece is still too big — recurse with a smaller separator.
                chunks.extend(_split_text(piece, chunk_size, rest_separators))
                current = ""
            else:
                current = piece
    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Prepend the tail of the previous chunk to each chunk so context
    isn't lost right at a chunk boundary (e.g. a sentence split between
    two chunks is now fully readable in the second one too).
    """
    if overlap <= 0 or len(chunks) < 2:
        return chunks
    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-overlap:]
        overlapped.append(tail + chunks[i])
    return overlapped


def chunk_pages(
    pages: list[dict],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    Chunk each page independently (so a chunk never silently spans two
    pages and loses citation accuracy), then flatten into one list.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    result: list[Chunk] = []
    for page in pages:
        raw_chunks = _split_text(page["text"], chunk_size, DEFAULT_SEPARATORS)
        raw_chunks = _add_overlap(raw_chunks, overlap)
        for text in raw_chunks:
            result.append(Chunk(text=text.strip(), page=page["page"]))
    return result
