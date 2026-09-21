"""
Stage 1 of the RAG pipeline: text extraction.

Each loader takes a file path and returns a list of "pages":
    [{"text": "...", "page": 1}, {"text": "...", "page": 2}, ...]

Page numbers matter even for formats that don't really have pages
(txt/csv use page=1) because everything downstream — chunking,
citations, the document viewer's "jump to page" — depends on every
piece of text being traceable back to a page number.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import fitz  # PyMuPDF
import docx  # python-docx


class UnsupportedFileError(Exception):
    pass


class EmptyDocumentError(Exception):
    """Raised when no extractable text was found (e.g. a scanned PDF with no text layer)."""


def load_pdf(file_path: str) -> list[dict]:
    pages = []
    with fitz.open(file_path) as pdf:
        for page_num, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if text and text.strip():
                pages.append({"text": text, "page": page_num})
    if not pages:
        raise EmptyDocumentError(
            "No text could be extracted from this PDF. It may be a scanned "
            "document with no text layer (OCR would be required)."
        )
    return pages


def load_docx(file_path: str) -> list[dict]:
    document = docx.Document(file_path)
    # python-docx has no real page concept (pagination happens at render time),
    # so we treat the whole document as page 1 and are explicit about that
    # limitation rather than inventing fake page numbers.
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    if not text.strip():
        raise EmptyDocumentError("No text content found in this DOCX file.")
    return [{"text": text, "page": 1}]


def load_txt_or_md(file_path: str) -> list[dict]:
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise EmptyDocumentError("This file appears to be empty.")
    return [{"text": text, "page": 1}]


def load_csv(file_path: str) -> list[dict]:
    """
    CSV is turned into a compact readable text block (one line per row,
    "column: value" pairs) so it can go through the same chunking /
    embedding pipeline as everything else, rather than needing a
    separate code path just for tabular data.
    """
    rows_text = []
    with open(file_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            line = ", ".join(f"{k}: {v}" for k, v in row.items())
            rows_text.append(f"Row {i}: {line}")
    text = "\n".join(rows_text)
    if not text.strip():
        raise EmptyDocumentError("This CSV file has no rows.")
    return [{"text": text, "page": 1}]


LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_txt_or_md,
    ".md": load_txt_or_md,
    ".csv": load_csv,
}


def load_document(file_path: str, file_type: str) -> list[dict]:
    """file_type is the lowercase extension including the dot, e.g. '.pdf'."""
    loader = LOADERS.get(file_type.lower())
    if loader is None:
        raise UnsupportedFileError(f"Unsupported file type: {file_type}")
    return loader(file_path)
