from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import SessionLocal, get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _owned_document_or_404(db: Session, document_id: str, user: User) -> Document:
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not doc:
        # 404, not 403 — we don't want to reveal whether a document ID exists
        # for another user at all.
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


def _process_in_background(document_id: str) -> None:
    """
    Runs in a background task, after the upload response has already been
    sent — this is what keeps the UI responsive during upload instead of
    the whole request (and page) hanging for however long embedding takes.

    Uses its own fresh DB session because the request's session is closed
    by the time this runs (FastAPI's get_db dependency closes it right
    after the response is returned).
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document_service.process_document(db, document)
    finally:
        db.close()


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    try:
        document_service.validate_upload(file.filename, len(content))
    except document_service.UploadValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    file_path, ext = document_service.save_upload(current_user.id, file.filename, content)
    document = document_service.create_document_record(
        db, current_user.id, file.filename, ext, file_path, len(content)
    )

    # Return immediately with status "uploaded"; the frontend polls
    # GET /api/documents/{id} until processing finishes. See
    # Documents.jsx's pollUntilDone for the other half of this.
    background_tasks.add_task(_process_in_background, document.id)
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_document_or_404(db, document_id, current_user)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _owned_document_or_404(db, document_id, current_user)
    document_service.delete_document(db, doc)
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _owned_document_or_404(db, document_id, current_user)
    return document_service.process_document(db, doc)
