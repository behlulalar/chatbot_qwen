# 🛠️ Geliştirici Rehberi

Bu doküman, projeyi geliştirmek ve kodu anlamak isteyenler için detaylı açıklamalar içerir.

## 🏗️ Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘

1. QDMS Scraping (Selenium)
   ├─ Selenium WebDriver
   ├─ Link extraction
   ├─ PDF download
   └─ Hash calculation (SHA-256)
   
2. Storage (PostgreSQL)
   ├─ Document metadata
   ├─ Processing status
   ├─ Update tracking
   └─ Chat logs

3. PDF Processing (PyMuPDF)
   ├─ Text extraction
   ├─ Structure detection (MADDE/ARTICLE)
   ├─ Paragraph parsing
   └─ JSON export

4. RAG Pipeline (LangChain)
   ├─ Document loading
   ├─ Smart chunking (madde-based)
   ├─ OpenAI embeddings
   └─ ChromaDB storage

5. LLM Generation (OpenAI)
   ├─ Query processing
   ├─ Semantic search
   ├─ Context formatting
   └─ GPT-3.5 response

6. API Layer (FastAPI)
   ├─ REST endpoints
   ├─ CORS support
   ├─ Request validation
   └─ Error handling

7. UI Layer (Streamlit)
   ├─ Chat interface
   ├─ Source display
   ├─ Cost tracking
   └─ Document browser
```

---

## 📦 Modül Açıklamaları

### 1. Scraper Module (`app/scraper/`)

**`qdms_scraper.py`**
- Selenium ile dinamik sayfa scraping
- QDMS link pattern matching
- PDF indirme ve hash hesaplama
- Retry logic ve error handling

**Önemli Fonksiyonlar:**
```python
extract_qdms_links()  # Link bulma
download_pdf()         # PDF indirme
_calculate_file_hash() # SHA-256 hash
```

**`link_tracker.py`**
- Database CRUD operations
- Change detection (hash comparison)
- Document lifecycle management

**Önemli Fonksiyonlar:**
```python
sync_documents()        # DB senkronizasyonu
_update_document()      # Güncelleme
get_documents_to_process() # İşlenecekleri getir
```

---

### 2. Converter Module (`app/converter/`)

**`pdf_processor.py`**
- PyMuPDF (fitz) ile PDF okuma
- Regex-based structure parsing
- Hierarchical content extraction

**Parsing Stratejisi:**
```
PDF → Full Text
    ↓
    MADDE/ARTICLE Pattern Matching
    ↓
    Fıkra Detection (1), (2), (3)
    ↓
    Alt Madde Detection a), b), c)
    ↓
    JSON Export
```

**Regex Patterns:**
- Article: `(?:MADDE|Madde|ARTICLE|Article)\s*(\d+)`
- Paragraph: `\((\d+)\)\s*([^\(]+?)`
- Sub-item: `([a-zğüşıöç])\)\s+([^\n]+?)`

---

### 3. RAG Module (`app/rag/`)

**`document_loader.py`**
- JSON → LangChain Document
- Metadata enrichment
- Batch loading

**`chunker.py`**
- Intelligent chunking strategy
- Size-based splitting
- Overlap management
- Metadata preservation

**Chunking Mantığı:**
```python
if content_length <= chunk_size:
    # Küçük madde → Tek chunk
elif content_length <= max_chunk_size:
    # Orta madde → Tek chunk (biraz büyük)
else:
    # Büyük madde → Overlap ile böl
```

**`vector_store.py`**
- ChromaDB operations
- Embedding generation
- Similarity search
- Batch processing

**OpenAI Embeddings:**
- Model: text-embedding-3-small
- Dimension: 1536
- Cost: ~$0.02 per 1M tokens

---

### 4. LLM Module (`app/llm/`)

**`openai_handler.py`**
- OpenAI API wrapper
- Token counting
- Cost calculation
- Streaming support

**`response_generator.py`**
- RAG orchestration
- Context formatting
- Source citation
- Error handling

**RAG Flow:**
```python
Question
  ↓
Embedding (OpenAI)
  ↓
Similarity Search (ChromaDB)
  ↓
Top K Documents (k=5)
  ↓
Context Formatting
  ↓
LLM Generation (GPT)
  ↓
Response + Sources
```

**`prompts.py`**
- System prompts
- User prompt templates
- Context templates

**Prompt Engineering:**
- Strict instruction: "SADECE verilen kaynaklardaki bilgileri kullan"
- Format specification: Kaynak + Madde numarası
- Fallback handling: Bilgi bulunamadığında ne yapacak

---

### 5. Scheduler Module (`app/scheduler/`)

**`update_job.py`**
- APScheduler integration
- Periodic updates (24h)
- Delta processing
- Vector store sync

**Update Pipeline:**
```python
1. Scrape QDMS
   ↓
2. Compare hashes
   ↓
3. Download changed PDFs
   ↓
4. Process to JSON
   ↓
5. Update vector store
```

---

## 🧪 Test Stratejisi

### Unit Tests (Gelecek)
```python
tests/
├── test_scraper.py
├── test_pdf_processor.py
├── test_rag_pipeline.py
└── test_llm.py
```

### Integration Tests
```bash
# Mevcut test script'leri
python test_scraper.py      # Scraper
python test_pdf_processor.py # PDF processing
python test_rag_pipeline.py  # RAG
python test_chatbot.py       # LLM
python test_api.py           # API
```

---

## 📊 Performans Optimizasyonu

### Chunking Optimization
```python
# Chunk size vs quality trade-off
chunk_size = 800    # Küçük = daha hassas, fazla chunk
chunk_size = 1500   # Büyük = daha az chunk, daha fazla context
```

### Retrieval Optimization
```python
# Top K selection
k = 3   # Hızlı ama az context
k = 5   # Dengeli (önerilir)
k = 10  # Yavaş ama çok context
```

### Embedding Batch Size
```python
batch_size = 50   # Düşük = yavaş ama güvenli
batch_size = 100  # Orta (önerilir)
batch_size = 200  # Yüksek = hızlı ama memory intensive
```

---

## 🔐 Güvenlik Best Practices

1. **API Keys**
   - .env dosyasını .gitignore'a ekle ✅
   - Environment variables kullan ✅
   - Secrets manager kullan (production)

2. **Database**
   - Güçlü şifreler
   - SQL injection koruması (SQLAlchemy ORM ✅)
   - SSL connection (production)

3. **API**
   - Rate limiting (gelecek)
   - Authentication (gelecek)
   - CORS configuration ✅

---

## 🚀 Gelecek Geliştirmeler

### Phase 2 Features
- [ ] Kullanıcı authentication
- [ ] Chat history kaydetme
- [ ] Multi-model comparison (GPT vs Llama)
- [ ] Advanced analytics dashboard
- [ ] Model fine-tuning
- [ ] Caching layer (Redis)
- [ ] Rate limiting
- [ ] Webhook notifications

### Phase 3 Features
- [ ] React frontend
- [ ] Mobile app
- [ ] Voice interface
- [ ] Multi-language support
- [ ] Advanced filters
- [ ] Export chat to PDF

---

## 📚 Öğrenme Kaynakları

### LangChain RAG
- [LangChain Docs](https://python.langchain.com/)
- [RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)

### OpenAI
- [OpenAI API Docs](https://platform.openai.com/docs)
- [GPT Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)

### ChromaDB
- [ChromaDB Docs](https://docs.trychroma.com/)

### FastAPI
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🤝 Katkıda Bulunma

1. Feature branch oluştur
2. Kodunu yaz
3. Test et
4. Pull request aç

---

## 📝 Kod Standartları

- PEP 8 style guide
- Type hints kullan
- Docstring ekle (Google style)
- Loglama ekle
- Error handling yap

## 🎓 Proje Öğrenimi

Bu proje sayesinde öğrenilecekler:
1. ✅ Web scraping (Selenium)
2. ✅ PDF processing
3. ✅ RAG pipeline
4. ✅ Vector databases (ChromaDB)
5. ✅ LLM integration (OpenAI)
6. ✅ FastAPI development
7. ✅ Database design (PostgreSQL)
8. ✅ Scheduling (APScheduler)
9. ✅ Deployment strategies
