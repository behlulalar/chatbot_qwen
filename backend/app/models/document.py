"""
Document model - tracks downloaded PDFs and their metadata.
"""
from typing import Optional
from datetime import datetime
from enum import Enum

from sqlalchemy import Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Document identification
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    qdms_link: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    pdf_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)  # SHA-256 for change detection

    # File paths
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    json_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status tracking
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus), default=DocumentStatus.DOWNLOADED, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"
