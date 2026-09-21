from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.conversation import Conversation, Feedback, Message
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import (
    AskRequest, ConversationResponse, FeedbackRequest, MessageResponse, NewConversationRequest,
)
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _owned_conversation_or_404(db: Session, conversation_id: str, user: User) -> Conversation:
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return convo


def _serialize_conversation(convo: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=convo.id,
        title=convo.title,
        document_ids=[d for d in (convo.document_ids or "").split(",") if d],
        created_at=convo.created_at,
        updated_at=convo.updated_at,
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(
    payload: NewConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # verify every document actually belongs to this user before scoping a chat to it
    if payload.document_ids:
        owned_count = (
            db.query(Document)
            .filter(Document.id.in_(payload.document_ids), Document.user_id == current_user.id)
            .count()
        )
        if owned_count != len(set(payload.document_ids)):
            raise HTTPException(status_code=400, detail="One or more documents were not found.")

    convo = Conversation(
        user_id=current_user.id,
        title=payload.title or "New conversation",
        document_ids=",".join(payload.document_ids),
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return _serialize_conversation(convo)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convos = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_serialize_conversation(c) for c in convos]


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convo = _owned_conversation_or_404(db, conversation_id, current_user)
    db.delete(convo)
    db.commit()
    return None


def _serialize_message(msg: Message) -> MessageResponse:
    citation_data = getattr(msg, "citation_data", None)
    if citation_data is None:
        citation_data = [
            {
                "index": s.citation_order,
                "document_id": s.chunk.document_id if s.chunk else "",
                "source_name": s.chunk.document.file_name if s.chunk and s.chunk.document else "unknown",
                "page": s.chunk.page_number if s.chunk else 1,
                "excerpt": (s.chunk.content[:280] if s.chunk else ""),
                "relevance_score": s.relevance_score,
            }
            for s in sorted(msg.sources, key=lambda s: s.citation_order)
        ]
    return MessageResponse(
        id=msg.id, role=msg.role, content=msg.content, created_at=msg.created_at,
        citations=citation_data,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convo = _owned_conversation_or_404(db, conversation_id, current_user)
    messages = sorted(convo.messages, key=lambda m: m.created_at)
    return [_serialize_message(m) for m in messages]


@router.post("/conversations/{conversation_id}/ask", response_model=MessageResponse)
def ask(conversation_id: str, payload: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    convo = _owned_conversation_or_404(db, conversation_id, current_user)

    user_message = Message(conversation_id=convo.id, role="user", content=payload.question)
    db.add(user_message)
    db.commit()

    assistant_message = chat_service.ask_question(db, convo, payload.question)

    if convo.title == "New conversation":
        convo.title = payload.question[:60]
        db.commit()

    return _serialize_message(assistant_message)


@router.post("/messages/{message_id}/feedback", status_code=204)
def give_feedback(message_id: str, payload: FeedbackRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    feedback = Feedback(
        user_id=current_user.id, message_id=message_id,
        rating=payload.rating, comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return None
