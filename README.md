# SUBU Mevzuat Chatbot v2

Sakarya Uygulamalı Bilimler Üniversitesi mevzuat ve yönergeleri icin gelistirilen RAG (Retrieval-Augmented Generation) tabanli yapay zeka chatbotu.

QDMS sistemindeki 77+ yonerge ve yonetmeligi otomatik olarak toplayip, isleyip, kullanicilarin dogal dilde sordugu sorulara kaynak gostererek cevap verir.

## Mimari

```
Frontend (React + TypeScript)
│   ChatInterface ── mesajlasma, streaming, session yonetimi
│   Sidebar ── sohbet gecmisi, otomatik yenileme
│
Backend (FastAPI + Python)
├── API Layer
│   ├── /chat          ── soru-cevap endpoint (streaming SSE)
│   └── /documents     ── dokuman yonetimi
│
├── RAG Pipeline
│   ├── Hybrid Retrieval   ── BM25 (keyword) + ChromaDB (semantic)
│   ├── RRF Fusion         ── Reciprocal Rank Fusion ile skor birlestirme
│   ├── Article Dedup      ── ayni maddenin chunk'larini birlestirme
│   ├── Score Cutoff       ── adaptive esik ile alakasiz sonuc filtreleme
│   └── LLM Judge          ── tek LLM cagrisinda hem alaka filtresi hem ozet
│
├── LLM Layer
│   ├── OpenAI Handler     ── OpenAI & Ollama uyumlu istemci
│   ├── Response Generator ── Hybrid RAG orkestrator
│   └── Prompts            ── sistem/kullanici/judge prompt sablonlari
│
├── Data Pipeline
│   ├── QDMS Scraper       ── Selenium ile PDF indirme
│   ├── PDF Processor      ── PyMuPDF ile yapi cikarma (madde/fikra/bent)
│   ├── MevzuatChunker     ── Turk hukuk metni icin akilli parcalama
│   ├── Document Loader    ── JSON → LangChain Document + metadata
│   └── Vector Store       ── ChromaDB embedding yonetimi
│
├── Background Jobs
│   └── APScheduler        ── 24 saatlik otomatik guncelleme
│
└── Storage
    ├── PostgreSQL          ── dokuman metadata, izleme
    ├── ChromaDB            ── vektor embedding'ler
    └── Redis/LRU Cache     ── iki katmanli onbellek
```

## Temel Ozellikler

- **Hybrid RAG**: BM25 keyword arama + ChromaDB semantic arama + RRF fusion
- **LLM Judge**: Tek bir LLM cagrisinda hem alaka filtresi hem kisa ozet uretimi
- **Dogrudan Kaynak Gosterimi**: LLM cevabinin altinda birebir mevzuat metni
- **Akilli PDF Isleme**: QDMS header/footer temizleme, madde/fikra/bent ayrimi
- **Turk Hukuk Metni Chunking**: Fikra sinirlarinda parcalama, madde basligi koruma
- **QDMS Metadata Temizleme**: Sayfa gecislerindeki meta-veri bloklarini silme
- **Article Deduplication**: Ayni maddenin birden fazla chunk'ini birlestirme
- **Otomatik Guncelleme**: 24 saatlik QDMS tarama ve delta guncelleme
- **Streaming Yanit**: SSE ile gercek zamanli token akisi
- **Session Yonetimi**: Sohbet gecmisi, sidebar'da aninda gozukme
- **Ollama Destegi**: Qwen 2.5 14B/32B ile yerel calisma

---

## v2 Degisiklik Gunlugu

Asagida v1'den v2'ye yapilan tum mimari degisiklikler, bug fix'ler ve iyilestirmeler listelenmistir.

### 1. Hybrid RAG Mimarisi (Yeni)

**Onceki**: Sadece ChromaDB semantic search
**Sonraki**: BM25 keyword + ChromaDB semantic + RRF fusion

| Dosya | Degisiklik |
|-------|-----------|
| `backend/app/rag/retrieval.py` | **Yeni dosya** - Hybrid retrieval motoru |
| `backend/app/rag/keyword_search.py` | **Yeni dosya** - BM25Okapi keyword arama |
| `backend/app/rag/text_utils.py` | **Yeni dosya** - Turkce metin normalizasyon |

- BM25 + Vector search sonuclari Reciprocal Rank Fusion (RRF) ile birlestiriliyor
- `retrieval_k=7` ile genis aday havuzu, ardindan LLM Judge filtrelemesi
- `_deduplicate_by_article`: Ayni (kaynak, madde_no) ciftine ait chunk'lar tek Document'ta birlestiriliyor
- `_merge_chunk_contents`: Chunk iceriklerini birlestirirken tekrar eden madde basliklarini temizliyor
- `invalidate_bm25_index()`: Embedding rebuild sonrasi BM25 index'ini sifirliyor

### 2. LLM Judge — Tek Cagri ile Filtre + Ozet (Yeni)

**Onceki**: LLM sadece metin uretimi icin kullaniliyordu veya hic kullanilmiyordu
**Sonraki**: LLM tek cagri ile hem alaka filtresi hem kisa ozet uretiyor

| Dosya | Degisiklik |
|-------|-----------|
| `backend/app/llm/response_generator.py` | `_llm_judge()` fonksiyonu eklendi |
| `backend/app/llm/prompts.py` | `_LLM_JUDGE_SYSTEM` prompt eklendi |

- Retrieve edilen tum adaylara tek LLM cagrisinda:
  - Hangi dokumanlarin soruyla alakali oldugunu belirler (indeks listesi)
  - Alakali dokumanlardan kisa bir ozet/giris cevabi uretir
- Sonuc: ozet + birebir kaynak metin birlesik cevap olarak sunulur
- Off-topic sorularda (ornegin "sizde iPhone var mi?") bos sonuc doner

### 3. Response Generator — Tam Yeniden Yazim

**Onceki**: Basit retrieve → LLM generate akisi
**Sonraki**: Cok katmanli pipeline: retrieve → dedup → score cutoff → LLM judge → format

| Fonksiyon | Aciklama |
|-----------|----------|
| `_retrieve_documents()` | Hybrid retrieval + dedup + cutoff + LLM judge orkestrasyonu |
| `_apply_score_cutoff()` | Adaptive esik ile dusuk skorlu sonuclari eliyor |
| `_build_combined_answer()` | LLM ozeti + programatik kaynak metin birlestirme |
| `_format_article_text()` | Madde icerigini temiz Markdown formatina donusturme |
| `_remove_qdms_blocks()` | QDMS sayfa basligi meta-veri bloklarini silme |
| `_clean_embedded_titles()` | Sayfa gecislerinde gomulu dokuman basliklarini silme |
| `_build_retrieval_query()` | Konusma gecmisinden sorgu zenginlestirme (tutucu mod) |
| `_no_context_response()` | Sonuc bulunamadiginda bilgilendirici statik yanit |

### 4. Metin Formatlama Pipeline (Yeni)

**Sorun**: PDF'lerden cikarilan metin QDMS header/footer'lari, kirik satirlar, yanlis bent algilamalari iceriyordu
**Cozum**: 7 adimli formatlama pipeline

`_format_article_text()` pipeline:

```
Ham metin
  → 1. QDMS meta-veri bloklarini sil (Dokuman No: ... Sayfa: N/M)
  → 2. Gomulu dokuman basliklarini sil
  → 3. Tum satir kiriklarini birlestir (PDF line-wrap → duz metin)
  → 4. Turkce sayi referanslarini koru: "uc (3) isgu" → bozma
  → 5. Fikra numaralarini cevir: (N) → N. + yeni satir
  → 6. Bent isaretlerini girintile: a), b), c) → 6 bosluk + yeni satir
  → 7. Son temizlik: bos satirlari azalt, ilk fikra numarasi ekle
```

**Duzeltilen bug'lar**:
- `"(ucak modu dahil)"` → `"dahi    l)"` olarak bolunuyordu (kelime sonu bent olarak algilaniyordu)
- `"(sifir)"` → `"sifi    r)"` olarak bolunuyordu
- `"uc (3) isgunu"` → `(3)` fikra numarasi olarak algilaniyordu
- QDMS bloklar madde ortasinda goruntuleri bozuyordu
- Sayfa gecislerinde cumle ortasi kiriliyordu

### 5. PDF Processor Iyilestirmeleri

| Degisiklik | Detay |
|-----------|-------|
| `_clean_text()` | Cok asamali QDMS header/footer temizleme, fuzzy baslik eslestirme |
| `_parse_articles()` | `_is_valid_article_title` ile baslik dogrulama, 70 karakter siniri |
| Fikra (1) Fix | MADDE basliginin ayni satirinda baslayan `(1)` artik doğru yakalaniyor |
| Baslik Temizleme | `is_exact`, `is_contained`, `is_fuzzy` ile cok katmanli baslik temizligi |

### 6. MevzuatChunker — Turkce Hukuk Metni Icin Yeniden Yazim

**Onceki**: Sabit boyutlu RecursiveCharacterTextSplitter
**Sonraki**: Fikra sinirlarinda akilli parcalama

| Kural | Aciklama |
|-------|----------|
| Madde <= 1500 karakter | Tek chunk olarak sakla |
| Madde > 1500 karakter | Oncelikle fikra `(N)` sinirlarinda bol |
| Fallback | RecursiveCharacterTextSplitter ile ikincil bolme |
| Header koruma | Her chunk orijinal madde basligini tasir |

### 7. Document Loader Iyilestirmeleri

| Degisiklik | Detay |
|-----------|-------|
| `_normalize_for_filter()` | Hizli Turkce normalizasyon (lokalize) |
| `_should_skip_article()` | Icerik derinligi olmayan maddeleri filtreleme |
| Metadata zenginlestirme | `title_normalized`, `article_title_normalized` eklendi |

### 8. OpenAI Handler Degisiklikleri

| Degisiklik | Detay |
|-----------|-------|
| `_calculate_cost()` | gpt-4o-mini ve diger modeller icin guncellendi |
| `count_tokens()` | tiktoken ile token sayma, fallback ile |
| Ollama uyumluluk | `max_tokens=2000` sert limiti kaldirildi |
| Model metadata | Yanit detaylarinda gercek model adi gosterimi |

### 9. Prompt Optimizasyonu

| Prompt | Degisiklik |
|--------|-----------|
| `SYSTEM_PROMPT` | LLM'e sadece kisa giris/analiz yazmasi talimat verildi; tam metin programatik ekleniyor |
| `NO_CONTEXT_PROMPT` | Bilgilendirici; botu tanitir, cevaplayabilecegi soru ornekleri verir |
| `_LLM_JUDGE_SYSTEM` | **Yeni** - Alaka filtresi + ozet uretici, katı cikti formati |

### 10. Frontend Degisiklikleri

| Dosya | Degisiklik |
|-------|-----------|
| `ChatInterface.tsx` | `sessionRefreshTrigger` state'i eklendi; mesaj gonderildikten sonra sidebar'i tetikler |
| `Sidebar.tsx` | `sessionRefreshTrigger` prop'u ile otomatik session listesi yenileme |
| `index.html` | Baslik ve meta bilgileri guncellendi |
| `.env.production` | Uretim ortami yapilandirmasi guncellendi |

### 11. Konfigürasyon ve Altyapi

| Dosya | Degisiklik |
|-------|-----------|
| `backend/app/config.py` | Yeni ayarlar: `RETRIEVAL_K`, `LLM_BASE_URL`, model yapilandirmasi |
| `backend/.env.example` | Ollama, model ve retrieval parametreleri eklendi |
| `backend/.env.server` | **Yeni** - Sunucu ortami icin ozel yapilandirma |
| `backend/requirements.txt` | rank_bm25, tiktoken ve diger bagimliliklar eklendi |
| `backend/app/main.py` | Startup event'leri, CORS ve endpoint kaydi guncellendi |

### 12. Yeni Script ve Araclar

| Dosya | Aciklama |
|-------|----------|
| `backend/rebuild_embeddings.py` | ChromaDB embedding'lerini sifirdan olusturma |
| `backend/run_vector_search.py` | Vector store uzerinde test aramalari |
| `backend/vector_store_search.py` | ChromaDB debug ve arama araci |
| `backend/scrape_yonetmelikler_only.py` | Sadece yonetmelikleri toplama scripti |
| `backend/chroma_olustur.sh` | ChromaDB olusturma shell scripti |
| `backend/tests/fixtures/eval_qa.json` | 50 soruluk test veri seti (kolay→zor) |
| `restart_on_server.sh` | Sunucu yeniden baslatma |
| `start_on_server.sh` | Sunucu ilk baslatma |
| `sunucuya_gonder.sh` | Dosyalari sunucuya SCP ile gonderme |
| `sunucuya_degisiklikleri_gonder.sh` | Sadece degisen dosyalari gonderme |

### 13. Dokumantasyon

| Dosya | Aciklama |
|-------|----------|
| `DEPLOYMENT_UBUNTU.md` | Ubuntu 22.04 deployment talimatlari (guncellendi) |
| `SUNUCUYA_ALMA.md` | Sunucuya alma adim adim kilavuz (guncellendi) |
| `SUNUCUYA_GONDER.md` | Dosya transferi talimatlari |
| `SUNUCU_README.md` | Sunucu uzerinde isletme kilavuzu |
| `SUNUCU_NODE_KURULUM.md` | Node.js kurulum talimatlari |
| `CHROMA_SUNUCU.md` | ChromaDB sunucu yapilandirmasi |
| `backend/7B_KURULUM.md` | Qwen 7B model kurulumu |
| `backend/CACHE_TEMIZLEME.md` | Onbellek temizleme talimatlari |
| `backend/PERFORMANS_YONETIMI.md` | Performans ayarlama kilavuzu |

### 14. Production: Gunicorn + systemd (12 Mart Roadmap)

**Hedef:** 150–200 kullanici kapasitesi icin API katmaninda Gunicorn ile 4 worker, systemd ile otomatik baslatma.

| Degisiklik | Detay |
|------------|--------|
| `backend/requirements.txt` | **gunicorn** eklendi (uvicorn ile birlikte production WSGI/ASGI sunucusu) |
| `deploy/README.md` | **Yeni** — Gunicorn kurulumu, 4 worker komutu, systemd adimlari, Gunicorn vs Uvicorn dogrulama |
| `deploy/subu-api.service` | **Yeni** — systemd unit sablonu; sunucuda `/etc/systemd/system/subu-api.service` olarak kopyalanir |
| `DEPLOYMENT_UBUNTU.md` | Systemd bolumu **subu-api.service** ve `deploy/` referansi ile guncellendi |

- Calistirma: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` (backend dizininden)
- Servis: `systemctl enable subu-api && systemctl start subu-api`

---

## Duzeltilen Kritik Bug'lar

| Bug | Cozum |
|-----|-------|
| BM25 normalizasyonunda cift `max(scores)` hesabi | Tek hesap ile duzeltildi |
| `hybrid_retrieve` icinde `search_k` 4x carpim hatasi | `retrieval_k * 3` ile duzeltildi |
| PDF parser'da fikra (1) basinin yakalanamamasi | `inline_is_content` kontrolu eklendi |
| Bent regex false positive: `dahil)`, `sifir)`, `gibi)` | `(?<=\s)` lookbehind ile sadece bagimsiz harfler eslesir |
| Turkce sayi + (N) pattern: `uc (3) isgunu` | Turkce sayi kelime korumasi eklendi |
| QDMS header/footer madde ortasinda gorunme | `_remove_qdms_blocks()` ile otomatik silme |
| Onceki sorunun cevabi yeni soruda goruntuleme | `_build_retrieval_query()` tutucu moda alindi |
| `strip()` non-breaking space girintilerini siliyordu | `re.sub(r'^\n+', '', out).rstrip()` ile duzeltildi |
| Alakasiz sorularda sonuc donme (ornegin "iPhone var mi?") | LLM Judge alaka filtresi ile cozuldu |

---

## Kurulum

### Gereksinimler

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- ChromeDriver (Selenium icin)
- Ollama (yerel LLM icin) veya OpenAI API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env dosyasini duzenle
python run_server.py
# Production: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

### Veri Pipeline (ilk kurulum)

```bash
cd backend
source venv/bin/activate
python setup_data_pipeline.py    # PDF indir + JSON isle
python rebuild_embeddings.py     # ChromaDB olustur
```

## Sunucu Deployment

Detayli talimatlar: [DEPLOYMENT_UBUNTU.md](DEPLOYMENT_UBUNTU.md)

**Production (12 Mart Roadmap):** API, Gunicorn (4 worker) + Uvicorn worker ile calistirilir; systemd servisi `subu-api.service` olarak tanimlidir. Kurulum ve komutlar: [deploy/README.md](deploy/README.md). Repoda `deploy/subu-api.service` sablonu sunucuda `/etc/systemd/system/subu-api.service` olarak kopyalanip yapilandirilir.

```bash
# Dosyalari sunucuya gonder
./sunucuya_gonder.sh

# Sunucuda baslat
ssh behlulalar@10.80.0.175
cd ~/behlul
./start_on_server.sh
```

## Test

```bash
cd backend
source venv/bin/activate
pytest -v

# 50 soruluk eval seti ile test
# backend/tests/fixtures/eval_qa.json
```

## Teknolojiler

| Katman | Teknoloji |
|--------|----------|
| Backend | Python 3.10, FastAPI, LangChain |
| LLM | Ollama (Qwen 2.5 14B/32B) / OpenAI (GPT-4o-mini) |
| Vector DB | ChromaDB |
| Keyword Search | BM25Okapi (rank_bm25) |
| PDF Isleme | PyMuPDF (fitz) |
| Web Scraping | Selenium + ChromeDriver |
| Database | PostgreSQL + SQLAlchemy |
| Cache | Redis + LRU Cache |
| Frontend | React 18, TypeScript |
| Scheduler | APScheduler |
| Token Sayma | tiktoken |

## Gelistirici

**Muhammed Behlul Alar**
- Proje: SUBU Mevzuat Chatbot v2
- Kurum: Sakarya Uygulamali Bilimler Universitesi
- Tarih: 2025-2026
