from datetime import datetime
from pydantic import BaseModel, Field


class NewConversationRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    title: str | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    document_ids: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CitationResponse(BaseModel):
    index: int
    document_id: str
    source_name: str
    page: int
    excerpt: str
    relevance_score: float


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    citations: list[CitationResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    rating: str = Field(pattern="^(helpful|not_helpful)$")
    comment: str | None = None
