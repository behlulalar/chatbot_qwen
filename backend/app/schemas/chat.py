"""
Chat API schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_history: Optional[List[dict]] = Field(default=None, description="Previous conversation")
    include_sources: bool = Field(default=True, description="Include source documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Akademik personele nasıl ödül verilir?",
                "include_sources": True
            }
        }


class Source(BaseModel):
    """Source document information."""
    title: str
    article_number: str
    article_title: Optional[str] = None
    relevance_score: float
    preview: str


class ChatMetadata(BaseModel):
    """Response metadata."""
    retrieved_docs: int
    tokens: int
    cost: float
    response_time: float
    model: str
    no_context: Optional[bool] = False
    cached: Optional[bool] = Field(default=False, description="True if response was served from cache (Redis/LRU)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default=[], description="Source documents")
    metadata: ChatMetadata = Field(..., description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Akademik personele ödül verilmesi...",
                "sources": [
                    {
                        "title": "Akademik ve İdari Personel Ödül Yönergesi",
                        "article_number": "5",
                        "relevance_score": 0.85,
                        "preview": "Ödüllendirme yıllık olarak yapılır..."
                    }
                ],
                "metadata": {
                    "retrieved_docs": 5,
                    "tokens": 1500,
                    "cost": 0.0015,
                    "response_time": 2.5,
                    "model": "gpt-3.5-turbo"
                }
            }
        }


class DocumentInfo(BaseModel):
    """Document information."""
    id: int
    title: str
    status: str
    page_count: Optional[int]
    article_count: Optional[int] = None
    processed_at: Optional[str]


class DocumentListResponse(BaseModel):
    """Response for document list endpoint."""
    total: int
    documents: List[DocumentInfo]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    vector_store_status: str
    database_status: str
