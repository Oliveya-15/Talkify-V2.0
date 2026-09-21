import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, default="New conversation")

    # comma-separated document IDs this conversation is scoped to (multi-doc chat)
    document_ids = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    sources = relationship("MessageSource", back_populates="message", cascade="all, delete-orphan")


class MessageSource(Base):
    """Links an assistant message to the real chunk(s) it was grounded in."""
    __tablename__ = "message_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, index=True)
    chunk_id = Column(String, ForeignKey("document_chunks.id"), nullable=False)
    relevance_score = Column(Float, nullable=False)
    citation_order = Column(Integer, nullable=False)

    message = relationship("Message", back_populates="sources")
    chunk = relationship("DocumentChunk")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    rating = Column(String, nullable=False)  # "helpful" | "not_helpful"
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
