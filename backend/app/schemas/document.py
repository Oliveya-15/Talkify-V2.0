from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    page_count: int | None
    processing_status: str
    processing_error: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkPreview(BaseModel):
    chunk_index: int
    page_number: int | None
    content: str

    class Config:
        from_attributes = True
