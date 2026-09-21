"""
Analytics: only ever returns numbers computed from real database rows.
No invented percentages, no placeholder "94% accuracy" — per the spec,
if a metric isn't actually measured, it doesn't appear here.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Conversation, Message
from app.models.document import Document, ProcessingStatus
from app.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_documents = db.query(Document).filter(Document.user_id == current_user.id).count()
    completed_documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.processing_status == ProcessingStatus.COMPLETED)
        .count()
    )
    failed_documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.processing_status == ProcessingStatus.FAILED)
        .count()
    )
    total_conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == current_user.id)
        .count()
    )

    return {
        "total_documents": total_documents,
        "completed_documents": completed_documents,
        "failed_documents": failed_documents,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
    }
