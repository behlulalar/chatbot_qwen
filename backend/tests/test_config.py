"""
Tests for configuration management.
"""
import pytest
from app.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings(
        DATABASE_URL="sqlite:///./test.db",
        OPENAI_API_KEY="test-key"
    )
    
    assert settings.app_name == "SUBU Mevzuat Chatbot"
    assert settings.app_version == "1.0.0"
    assert settings.model_name == "gpt-4o-mini"
    assert settings.temperature == 0.1
    assert settings.chunk_size == 800
    assert settings.chunk_overlap == 150


def test_settings_from_env(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("APP_NAME", "Test Chatbot")
    monkeypatch.setenv("MODEL_NAME", "gpt-4")
    monkeypatch.setenv("CHUNK_SIZE", "1000")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    settings = Settings()
    
    assert settings.app_name == "Test Chatbot"
    assert settings.model_name == "gpt-4"
    assert settings.chunk_size == 1000


def test_cors_origins_parsing():
    """Test CORS origins parsing from comma-separated string."""
    settings = Settings(
        DATABASE_URL="sqlite:///./test.db",
        OPENAI_API_KEY="test-key",
        CORS_ORIGINS="http://localhost:3000,https://example.com,http://192.168.1.1"
    )
    
    origins = settings.get_cors_origins()
    
    assert len(origins) == 3
    assert "http://localhost:3000" in origins
    assert "https://example.com" in origins
    assert "http://192.168.1.1" in origins
