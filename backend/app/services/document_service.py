"""
Handles everything about a document's lifecycle: validating an upload,
saving it to disk, running the RAG ingestion pipeline, and persisting
the resulting chunks. Kept separate from the API route so the route
stays thin (parse request -> call service -> return response) and this
logic is reusable/testable without spinning up FastAPI.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk, ProcessingStatus
from app.rag import pipeline
from app.rag.loaders import EmptyDocumentError, UnsupportedFileError


class UploadValidationError(Exception):
    pass


def validate_upload(filename: str, size_bytes: int) -> str:
    """Returns the lowercase extension if valid, else raises UploadValidationError."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"'{ext or 'unknown'}' is not supported. Allowed types: "
            f"{', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise UploadValidationError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit.")
    if size_bytes == 0:
        raise UploadValidationError("File is empty.")
    return ext


def save_upload(user_id: str, filename: str, content: bytes) -> tuple[str, str]:
    """Saves the raw bytes to disk under a random name (never trust the
    original filename for a path — that's a classic path-traversal risk)
    and returns (stored_file_path, safe_extension).
    """
    ext = Path(filename).suffix.lower()
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(user_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path, ext


def create_document_record(db: Session, user_id: str, file_name: str, file_type: str,
                            file_path: str, file_size: int) -> Document:
    document = Document(
        user_id=user_id,
        file_name=file_name,
        file_type=file_type.lstrip("."),
        file_path=file_path,
        file_size=file_size,
        processing_status=ProcessingStatus.UPLOADED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def process_document(db: Session, document: Document) -> Document:
    """Runs the full ingestion pipeline synchronously. For a student
    project this keeps things simple to explain; a production system
    would push this to a background task queue (Celery/RQ) so upload
    requests return instantly.
    """
    document.processing_status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        result = pipeline.ingest_document(document.id, document.file_path, f".{document.file_type}")

        document.page_count = result.page_count

        chunk_rows = []
        for ingested in result.chunks:
            chunk_rows.append(DocumentChunk(
                document_id=document.id,
                chunk_index=ingested.vector_ref,
                content=ingested.text,
                page_number=ingested.page,
                vector_ref=ingested.vector_ref,
            ))
        db.add_all(chunk_rows)
        db.commit()

        # keyword index needs real chunk_ids, which only exist after commit
        for row in chunk_rows:
            db.refresh(row)
        pipeline.index_for_keyword_search(
            document.id,
            [row.id for row in chunk_rows],
            [row.content for row in chunk_rows],
        )

        document.processing_status = ProcessingStatus.COMPLETED
        document.processing_error = None

    except (UnsupportedFileError, EmptyDocumentError) as e:
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = str(e)
    except Exception as e:  # noqa: BLE001 - we want to record *any* failure, not crash the request
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = f"Unexpected processing error: {e}"

    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document: Document) -> None:
    pipeline.delete_document_indexes(document.id)
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    db.delete(document)
    db.commit()
