"""
Document model - tracks downloaded PDFs and their metadata.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.database import Base


class DocumentStatus(str, Enum):
    """Document processing status."""
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Document(Base):
    """
    Model for tracking mevzuat documents.
    
    This table stores:
    - QDMS link and PDF metadata
    - Processing status
    - Content hash for change detection
    - File paths
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Document identification
    title = Column(String(500), nullable=False, index=True)
    qdms_link = Column(String(1000), unique=True, nullable=False, index=True)
    pdf_hash = Column(String(64), index=True)  # SHA-256 hash for change detection
    
    # File paths
    pdf_path = Column(String(500))
    json_path = Column(String(500))
    
    # Status tracking
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DOWNLOADED, index=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    file_size = Column(Integer)  # in bytes
    page_count = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked_at = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"
