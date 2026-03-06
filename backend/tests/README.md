# Unit Tests

Bu klasör, SUBU Chatbot backend'i için unit testleri içerir.

## Çalıştırma

### Tüm testleri çalıştır
```bash
cd backend
pytest
```

### Belirli bir test dosyasını çalıştır
```bash
pytest tests/test_config.py
```

### Verbose mode ile çalıştır
```bash
pytest -v
```

### Coverage raporu ile çalıştır
```bash
pytest --cov=app --cov-report=html
```

## Test Yapısı

- `conftest.py` - Pytest fixtures ve konfigürasyon
- `test_config.py` - Configuration yönetimi testleri
- `test_chunker.py` - Document chunking testleri
- `test_response_generator.py` - Response generator utility testleri
- `test_api.py` - API endpoint testleri

## Test Ekleme

Yeni test eklerken:

1. `test_` prefix'i ile başlayın
2. Docstring ekleyin
3. Assert'leri açıklayıcı yapın
4. Fixtures kullanın (conftest.py)

Örnek:
```python
def test_my_function():
    \"\"\"Test that my_function works correctly.\"\"\"
    result = my_function("input")
    assert result == "expected_output"
```

## Fixtures

Ortak test verileri için `conftest.py`'de fixtures tanımlı:

- `temp_dir` - Geçici dizin
- `sample_pdf_text` - Örnek PDF metni
- `sample_chunk` - Örnek document chunk
- `sample_chunks` - Çoklu örnek chunks

## Coverage Hedefi

- Unit tests: >80% coverage
- Integration tests: Kritik akışlar
- E2E tests: Ana kullanım senaryoları
