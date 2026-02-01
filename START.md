# 🚀 SUBU Mevzuat Chatbot - Başlangıç Rehberi

## 📋 Hızlı Başlangıç

### 1. Backend Sunucusunu Başlat

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python run_server.py
```

Server başlayacak:
- 🌐 API: http://localhost:8000
- 📖 Docs: http://localhost:8000/docs
- ⏰ Otomatik güncelleme: Her 24 saatte bir

### 2. React UI'yi Başlat (Yeni Terminal)

```bash
cd frontend
npm install  # İlk kez
npm start
```

UI açılacak:
- 🖥️ URL: http://localhost:3000
- 💬 Modern chat arayüzü
- 📊 Real-time istatistikler
- 📚 Doküman listesi

---

## 🧪 Test Senaryoları

### Backend'i Test Et (API olmadan)

```bash
cd backend

# Chatbot'u doğrudan test et
python test_chatbot.py
# Seçenek 3: Interactive mode

# Örnek sorular:
# - Akademik personele ödül nasıl verilir?
# - Lisansüstü öğrencilerin azami süreleri nedir?
# - Bilimsel araştırma projesi başvurusu nasıl yapılır?
```

### API'yi Test Et

```bash
# Terminal 1: Server başlat
python run_server.py

# Terminal 2: API test et
python test_api.py
# Seçenek 4: Interactive chat
```

### UI'yi Test Et

```bash
# Terminal 1: Server çalışıyor olmalı
# Terminal 2:
cd frontend
npm start
```

Browser'da aç ve soru sor!

---

## 📊 Proje Yapısı

```
subu_chatbot_v2/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints ✅
│   │   ├── llm/              # OpenAI integration ✅
│   │   ├── rag/              # RAG pipeline ✅
│   │   ├── scraper/          # Web scraping ✅
│   │   ├── converter/        # PDF processing ✅
│   │   ├── scheduler/        # Auto updates ✅
│   │   └── models/           # Database models ✅
│   ├── data/
│   │   ├── raw_pdfs/         # 77 PDFs ✅
│   │   ├── processed_json/   # 77 JSONs ✅
│   │   └── chroma_db/        # Vector store ✅
│   └── run_server.py         # Main entry ✅
└── frontend/                 # React + TypeScript ✅
    ├── src/
    │   ├── components/       # UI components
    │   └── App.tsx           # Main app
    ├── Dockerfile            # Docker config
    └── nginx.conf            # Nginx config
```

---

## 🔄 Güncellemeler

### Manuel Güncelleme

```bash
cd backend
python -c "from app.scheduler import UpdateScheduler; scheduler = UpdateScheduler(); scheduler.run_now()"
```

### Otomatik Güncelleme

`run_server.py` çalıştığında otomatik olarak her 24 saatte bir:
1. QDMS sitesini tarar
2. Değişen PDF'leri tespit eder
3. Yeniden işler
4. Vector store'u günceller

---

## 💡 Faydalı Komutlar

### Backend

```bash
# Database'deki dokümanları gör
python -c "from app.database import SessionLocal; from app.models import Document; db = SessionLocal(); docs = db.query(Document).all(); print(f'Toplam: {len(docs)}')"

# Vector store istatistikleri
python -c "from app.rag import VectorStoreManager; m = VectorStoreManager(); m.create_or_load(); print(m.get_collection_stats())"

# Logs'ları izle
tail -f logs/server.log
```

### Frontend

```bash
# Development build
npm start

# Production build
npm run build

# Serve production
npx serve -s build
```

---

## ⚙️ Ayarlar

### Backend (.env)
```env
MODEL_NAME=gpt-3.5-turbo        # GPT modeli
TEMPERATURE=0.3                  # Yaratıcılık
CHUNK_SIZE=800                   # Chunk boyutu
UPDATE_INTERVAL=24               # Güncelleme (saat)
```

### Frontend (.env.development)
```env
REACT_APP_API_URL=http://localhost:8000
```

---

## 🎯 Endpoint'ler

### POST /api/chat/
Soru sor, cevap al

**Request:**
```json
{
  "question": "Akademik personele ödül nasıl verilir?",
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "cost": 0.0015,
    "tokens": 1500
  }
}
```

### GET /api/documents/
Doküman listesi

### GET /health
Sistem durumu

---

## 🐛 Sorun Giderme

### Backend Sorunları

**API bağlanamıyor:**
```bash
# Backend çalışıyor mu?
curl http://localhost:8000/health
```

**ChromaDB hatası:**
```bash
# Vector store'u yeniden oluştur
rm -rf data/chroma_db
python test_rag_pipeline.py  # Seçenek 3
```

**OpenAI hatası:**
```bash
# API key kontrol
echo $OPENAI_API_KEY
```

### Frontend Sorunları

**npm install hatası:**
```bash
# Node version kontrol (18+ gerekli)
node --version

# Cache temizle
rm -rf node_modules package-lock.json
npm install
```

**API bağlanamıyor:**
```bash
# .env dosyasını kontrol
cat .env.development

# Backend çalışıyor mu?
curl http://localhost:8000/health
```

**Build hatası:**
```bash
# TypeScript hatalarını görmezden gel (geliştirme)
npm start

# Production build
npm run build
```

---

## 🚀 Production Deployment

### Option 1: Docker Compose

```bash
# .env dosyalarını hazırla
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# API key ekle
nano backend/.env

# Build & run
docker-compose up -d

# Logları izle
docker-compose logs -f
```

Açık:
- Frontend: http://localhost
- Backend: http://localhost:8000

### Option 2: Manuel Deployment

**Backend:**
```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
cd frontend
npm run build
npx serve -s build -p 3000
```

### Option 3: Windows Server

Detaylı bilgi: [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md)

---

## 🎨 UI Özellikleri

### Modern Tasarım
- 🌈 Gradient background
- 💬 Smooth message bubbles
- 📚 Collapsible sources
- 📊 Real-time statistics
- 🎯 One-click example questions

### Responsive
- 💻 Desktop: Full sidebar
- 📱 Tablet: Collapsible
- 📱 Mobile: Overlay sidebar

---

## 📞 İletişim

**Proje:** SUBU Mevzuat Chatbot  
**Versiyon:** 1.0.0  
**Teknolojiler:**
- Backend: Python, FastAPI, LangChain, OpenAI
- Frontend: React, TypeScript
- Database: PostgreSQL
- Vector Store: ChromaDB
- Deployment: Docker, Nginx

## 🎯 Sonraki Adımlar

1. ✅ Backend çalıştır
2. ✅ Frontend aç
3. ✅ Soru sor
4. ✅ Kaynaklara bak
5. ✅ İstatistikleri izle
6. 🚀 Production'a deploy et!

**Başarılar!** 🎉
