"""
Pytest configuration and fixtures.
"""
import pytest
import os
import tempfile
from pathlib import Path

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["OPENAI_API_KEY"] = "test-key-for-unit-tests"
os.environ["DEBUG"] = "True"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pdf_text():
    """Sample PDF text for testing."""
    return """
    MADDE 1 - Amaç
    Bu yönergenin amacı, üniversite personelinin ödüllendirilmesine ilişkin 
    usul ve esasları belirlemektir.
    
    MADDE 2 - Kapsam
    (1) Bu yönerge, akademik ve idari personeli kapsar.
    (2) Ödüller yılda bir kez verilir.
    
    a) Bilimsel çalışma ödülü
    b) Başarı ödülü
    
    MADDE 3 - Tanımlar
    Bu yönergede geçen terimler şunlardır:
    (1) Ödül: Başarılı çalışmalara verilen teşvik.
    """


@pytest.fixture
def sample_chunk():
    """Sample document chunk for testing."""
    from langchain.schema import Document
    
    return Document(
        page_content="MADDE 1 - Amaç\nBu yönergenin amacı, ödüllendirme esaslarını belirlemektir.",
        metadata={
            "source": "test_yonerge.json",
            "title": "Test Yönergesi",
            "article_number": "1",
            "article_title": "Amaç"
        }
    )


@pytest.fixture
def sample_chunks(sample_chunk):
    """Multiple sample chunks for testing."""
    from langchain.schema import Document
    
    return [
        sample_chunk,
        Document(
            page_content="MADDE 2 - Kapsam\nBu yönerge tüm personeli kapsar.",
            metadata={
                "source": "test_yonerge.json",
                "title": "Test Yönergesi",
                "article_number": "2",
                "article_title": "Kapsam"
            }
        ),
        Document(
            page_content="MADDE 3 - Tanımlar\nBu yönergede geçen tanımlar...",
            metadata={
                "source": "test_yonerge.json",
                "title": "Test Yönergesi",
                "article_number": "3",
                "article_title": "Tanımlar"
            }
        )
    ]
