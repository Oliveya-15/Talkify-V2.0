import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base


class ProcessingStatus:
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf | docx | txt | md | csv
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=True)

    processing_status = Column(String, default=ProcessingStatus.UPLOADED)
    processing_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """
    One retrievable unit of text. `vector_ref` is the row index of this
    chunk's embedding inside the FAISS index for its document (see
    rag/vector_store.py) — this is what makes every retrieved vector
    traceable back to real source text, as the spec requires.
    """
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    vector_ref = Column(Integer, nullable=True)  # position in the FAISS index

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
