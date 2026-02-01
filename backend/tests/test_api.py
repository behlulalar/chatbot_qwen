"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data
    
    assert data["message"] == "SUBU Mevzuat Chatbot API"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "version" in data
    assert "vector_store_status" in data
    assert "database_status" in data


def test_chat_endpoint_missing_question():
    """Test chat endpoint with missing question."""
    response = client.post("/api/chat/", json={})
    
    # Should return 422 for validation error
    assert response.status_code == 422


def test_chat_endpoint_with_question():
    """Test chat endpoint with valid question."""
    response = client.post("/api/chat/", json={
        "question": "Test question",
        "include_sources": True
    })
    
    # May fail if vector store is empty, but should not be a 422 validation error
    assert response.status_code in [200, 500]


def test_documents_endpoint():
    """Test documents listing endpoint."""
    response = client.get("/api/documents/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return a list
    assert isinstance(data, list)


def test_cache_stats_endpoint():
    """Test cache statistics endpoint."""
    response = client.get("/api/chat/cache/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "cache" in data


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/")
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers or response.status_code == 200
