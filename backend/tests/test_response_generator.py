"""
Tests for response generator utilities.
"""
import pytest
from app.llm.response_generator import normalize_turkish


def test_normalize_turkish_lowercase():
    """Test Turkish character normalization to lowercase."""
    text = "İstanbul Üniversitesi"
    normalized = normalize_turkish(text)
    
    # İ should become i, Ü should become u
    assert "i" in normalized.lower()
    assert "u" in normalized.lower()


def test_normalize_turkish_special_characters():
    """Test normalization of all Turkish special characters."""
    text = "ÇĞİÖŞÜ çğıöşü"
    normalized = normalize_turkish(text)
    
    # Should convert to ASCII equivalents
    assert "c" in normalized.lower()
    assert "g" in normalized.lower()
    assert "i" in normalized.lower()
    assert "o" in normalized.lower()
    assert "s" in normalized.lower()
    assert "u" in normalized.lower()


def test_normalize_turkish_preserves_numbers():
    """Test that normalization preserves numbers."""
    text = "Madde 123"
    normalized = normalize_turkish(text)
    
    assert "123" in normalized


def test_normalize_turkish_empty_string():
    """Test normalization of empty string."""
    text = ""
    normalized = normalize_turkish(text)
    
    assert normalized == ""


def test_normalize_turkish_ascii_only():
    """Test that ASCII text remains unchanged."""
    text = "hello world 123"
    normalized = normalize_turkish(text)
    
    assert normalized == text.lower()


def test_normalize_turkish_mixed_text():
    """Test normalization of mixed Turkish and ASCII text."""
    text = "SUBU Ödül Yönergesi - Article 5"
    normalized = normalize_turkish(text)
    
    # Should be lowercase and Turkish chars normalized
    assert normalized == "subu odul yonergesi - article 5"
