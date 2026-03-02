# 📚 SUBU Mevzuat Chatbot

Sakarya Uygulamalı Bilimler Üniversitesi için yapay zeka destekli mevzuat chatbotu. Bu chatbot, üniversitenin QDMS sistemindeki yönerge ve mevzuatları RAG (Retrieval-Augmented Generation) pipeline kullanarak yanıtlar.

## ✨ Özellikler

- ✅ **Otomatik Veri Toplama**: QDMS sisteminden 77 PDF otomatik indirme
- ✅ **Akıllı Güncelleme**: 24 saatlik otomatik kontrol ve delta update
- ✅ **Semantic Search**: 2,719 chunk üzerinde anlam bazlı arama
- ✅ **RAG Pipeline**: LangChain + ChromaDB + OpenAI
- ✅ **Doğru Kaynak Gösterimi**: Her cevap kaynak madde ile
- ✅ **REST API**: FastAPI ile modern API
- ✅ **Web Arayüzü**: Streamlit ile kolay kullanım
- ✅ **Maliyet Tracking**: Query başına $0.001-0.002
- ✅ **Çift Dil Desteği**: Türkçe ve İngilizce mevzuatlar

## 🏗️ Mimari

```
Backend (FastAPI)
├── Scraper Module (Selenium)
├── PDF Processor (PyMuPDF)
├── RAG Pipeline (LangChain + ChromaDB)
├── LLM Handler (OpenAI)
└── Scheduler (APScheduler)

Frontend (Phase 1: Streamlit / Phase 2: React)

Database
├── PostgreSQL (metadata, logs)
└── ChromaDB (vector embeddings)
```

## 🚀 Kurulum

### 1. Python Ortamı

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Çevre Değişkenleri

```bash
cp .env.example .env
# .env dosyasını düzenle:
# - DATABASE_URL (PostgreSQL connection string)
# - OPENAI_API_KEY (OpenAI API anahtarı)
```

### 3. Veritabanı Oluşturma

```bash
# PostgreSQL'de database oluştur
createdb subu_chatbot

# Migration çalıştır (veya init_db kullan)
python -c "from app.database import init_db; init_db()"
```

### 4. ChromeDriver Kurulumu

Selenium için ChromeDriver gerekli:
- [ChromeDriver İndir](https://chromedriver.chromium.org/)
- PATH'e ekle veya proje klasörüne koy

## 🚀 Hızlı Başlangıç

### Adım 1: Backend Sunucusunu Başlat

```bash
cd backend
source venv/bin/activate
python run_server.py
```

✅ API: http://localhost:8000  
✅ Docs: http://localhost:8000/docs  
✅ Otomatik güncelleme: Aktif

### Adım 2: React UI'yi Başlat

Yeni terminal aç:

```bash
cd frontend
npm install
npm start
```

✅ UI: http://localhost:3000

### Hazır! 🎉

Artık web arayüzünden mevzuat sorularını sorabilirsiniz!

---

## 📖 Detaylı Kullanım

Daha fazla bilgi için bakınız: [START.md](START.md)

## 📂 Proje Yapısı

```
subu_chatbot_v2/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints ✅
│   │   ├── llm/              # OpenAI GPT integration ✅
│   │   ├── rag/              # RAG pipeline (LangChain + ChromaDB) ✅
│   │   ├── scraper/          # Selenium web scraping ✅
│   │   ├── converter/        # PDF → JSON processing ✅
│   │   ├── scheduler/        # APScheduler (24h updates) ✅
│   │   ├── models/           # SQLAlchemy models ✅
│   │   ├── schemas/          # Pydantic schemas ✅
│   │   └── utils/            # Logger & helpers ✅
│   ├── data/
│   │   ├── raw_pdfs/         # 77 downloaded PDFs ✅
│   │   ├── processed_json/   # 77 parsed JSONs ✅
│   │   ├── chroma_db/        # 2,719 vector embeddings ✅
│   │   └── archive/          # Old versions
│   ├── logs/                 # Application logs
│   ├── run_server.py         # Main server entry ✅
│   └── test_*.py             # Test scripts ✅
├── frontend/
│   └── streamlit_app.py      # Web UI ✅
├── docker-compose.yml        # Docker deployment ✅
├── START.md                  # Quick start guide ✅
├── DEPLOYMENT_WINDOWS.md     # Windows deployment ✅
└── DEVELOPMENT.md            # Developer guide ✅
```

## 🔧 Geliştirme Aşamaları

- [x] **Sprint 1**: Proje yapısı ve scraper ✅
- [x] **Sprint 2**: PDF processing ve JSON dönüşümü ✅
- [x] **Sprint 3**: RAG pipeline ve embeddings ✅
- [x] **Sprint 4**: LLM integration ✅
- [x] **Sprint 5**: FastAPI endpoints ✅
- [x] **Sprint 6**: Scheduler (otomatik güncelleme) ✅
- [x] **Sprint 7**: Streamlit UI ✅
- [ ] **Sprint 8**: Deployment (Windows Server)

## 📊 Proje İstatistikleri

- ✅ **77 Mevzuat** dokümanı işlendi
- ✅ **1,419 Madde** ayrıştırıldı
- ✅ **2,719 Chunk** vektörleştirildi
- ✅ **%100 Başarı** oranı
- ✅ **~$0.001** per query maliyet
- ✅ **2-3 saniye** ortalama cevap süresi

## 🎯 Proje Hedefleri

### Teknik Hedefler ✅
- [x] End-to-end RAG pipeline
- [x] Production-ready architecture
- [x] Automatic update system
- [x] Cost-efficient (<$1/day)
- [x] Fast response time (<5s)
- [x] Source citation
- [x] Bilingual support (TR/EN)

### Öğrenme Hedefleri ✅
- [x] Web scraping mastery
- [x] PDF processing techniques
- [x] Vector database operations
- [x] LLM prompt engineering
- [x] RAG pipeline implementation
- [x] API development (FastAPI)
- [x] Database design (PostgreSQL)
- [x] Background job scheduling

## 🐧 Deployment

### Docker ile (Önerilen)
```bash
# Projeyi klonla
git clone https://github.com/YOUR_USERNAME/subu_chatbot_v2.git
cd subu_chatbot_v2

# .env dosyalarını ayarla
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Docker Compose ile başlat
docker-compose up -d
```

### Ubuntu 22.04'e Manuel Deployment
Detaylı talimatlar için: [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md)

## 🧪 Testing

```bash
cd backend
pytest -v
```

## 🤝 Katkıda Bulunma

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👨‍💻 Geliştirici

**Muhammed Behlül Alar**
- Proje: SUBU Mevzuat Chatbot
- Teknolojiler: Python, LangChain, OpenAI, FastAPI, PostgreSQL, ChromaDB, React, TypeScript
- Tarih: 2026

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
# local_chatbot_subu
# chatbot_qwen
# chatbot_qwen
# chatbot_qwen
