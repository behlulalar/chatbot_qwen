"""
Tests for document chunking.
"""
import pytest
from langchain_core.documents import Document
from app.rag.chunker import DocumentChunker


def test_chunker_initialization():
    """Test chunker initialization with default parameters."""
    chunker = DocumentChunker()
    
    assert chunker.chunk_size == 800
    assert chunker.chunk_overlap == 150


def test_chunker_custom_parameters():
    """Test chunker initialization with custom parameters."""
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    
    assert chunker.chunk_size == 1000
    assert chunker.chunk_overlap == 200


def test_chunk_small_document():
    """Test chunking a small document (single chunk)."""
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    
    doc = Document(
        page_content="MADDE 1 - Bu kısa bir maddedir.",
        metadata={
            "source": "test.json",
            "article_number": "1"
        }
    )
    
    chunks = chunker.chunk_document(doc)
    
    # Small content should result in single chunk
    assert len(chunks) == 1
    assert chunks[0].page_content == doc.page_content
    assert chunks[0].metadata["source"] == "test.json"


def test_chunk_large_document():
    """Test chunking a large document (multiple chunks)."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    # Create a large document
    content = " ".join([f"Cümle {i}." for i in range(100)])
    doc = Document(
        page_content=content,
        metadata={
            "source": "test.json",
            "article_number": "1"
        }
    )
    
    chunks = chunker.chunk_document(doc)
    
    # Should create multiple chunks
    assert len(chunks) > 1
    
    # All chunks should have metadata
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "article_number" in chunk.metadata


def test_chunk_multiple_documents(sample_chunks):
    """Test chunking multiple documents."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    chunks = chunker.chunk_documents(sample_chunks)
    
    # Should return a list of chunks
    assert isinstance(chunks, list)
    assert len(chunks) >= len(sample_chunks)
    
    # All chunks should have content
    for chunk in chunks:
        assert len(chunk.page_content) > 0


def test_chunk_preserves_metadata():
    """Test that chunking preserves document metadata."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    doc = Document(
        page_content="Test content " * 50,  # Large enough to split
        metadata={
            "source": "test.json",
            "title": "Test Document",
            "article_number": "5",
            "custom_field": "value"
        }
    )
    
    chunks = chunker.chunk_document(doc)
    
    # All chunks should preserve metadata
    for chunk in chunks:
        assert chunk.metadata["source"] == "test.json"
        assert chunk.metadata["title"] == "Test Document"
        assert chunk.metadata["article_number"] == "5"
        assert chunk.metadata["custom_field"] == "value"
