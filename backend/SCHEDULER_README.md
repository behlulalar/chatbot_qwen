# 🔄 Otomatik Güncelleme Sistemi

Bu doküman, SUBU Chatbot'un otomatik güncelleme sistemini açıklar.

## 📋 Genel Bakış

Otomatik güncelleme sistemi, QDMS web sitesinden mevzuat dokümanlarını periyodik olarak kontrol eder ve değişiklikleri otomatik olarak işler.

## 🎯 Özellikler

- ✅ **Otomatik Tarama**: Her 24 saatte bir QDMS'i tarar
- ✅ **Akıllı Güncelleme**: Sadece değişen dosyaları işler (hash comparison)
- ✅ **Delta Update**: Tüm sistemi yeniden işlemez, sadece değişiklikleri günceller
- ✅ **Vector Store Sync**: Değişiklikleri otomatik olarak vector store'a ekler
- ✅ **Hata Yönetimi**: Hata durumunda log kaydeder ve devam eder
- ✅ **Background Process**: Sunucu çalışırken arka planda çalışır

## 🚀 Nasıl Çalışır?

### 1. Otomatik Mod (Önerilen)

Server başlatıldığında otomatik olarak aktif olur:

```bash
cd backend
python run_server.py
```

**Çıktı:**
```
🚀 SUBU Mevzuat Chatbot v1.0.0
================================================================================

📍 API Server: http://localhost:8000
📖 API Docs: http://localhost:8000/docs
⏰ Update Interval: 24 hours

✅ Scheduler started
   Next update: 2026-02-02 12:00:00

✅ API Server starting...
```

### 2. Manuel Güncelleme

Scheduler beklemeden hemen güncelleme yapmak için:

```bash
cd backend
python manual_update.py
```

### 3. Test Modu

Scheduler'ın doğru çalıştığını test etmek için:

```bash
cd backend
python test_scheduler.py
```

## ⚙️ Konfigürasyon

`.env` dosyasında ayarlanabilir:

```env
# Güncelleme aralığı (saat cinsinden)
UPDATE_INTERVAL=24

# QDMS URL (değişirse buradan güncelleyin)
QDMS_URL=https://hukuk.subu.edu.tr/yonergeler
```

**Önerilen değerler:**
- `UPDATE_INTERVAL=24` - Günde bir kez (önerilen)
- `UPDATE_INTERVAL=12` - Günde iki kez
- `UPDATE_INTERVAL=6` - 6 saatte bir (sık güncelleme)

## 📊 Güncelleme Süreci

```
┌─────────────────────────────────────────────────────────────┐
│ 1. QDMS Web Sitesini Tara                                   │
│    → Selenium ile PDF linklerini çıkar                      │
│    → 77 PDF linkini tespit et                               │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Değişiklikleri Tespit Et                                 │
│    → Her PDF'in hash'ini hesapla (SHA-256)                  │
│    → Veritabanındaki eski hash ile karşılaştır             │
│    → Değişen dosyaları işaretle                             │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Değişen PDF'leri İşle                                    │
│    → PDF → Text extraction (PyMuPDF)                        │
│    → MADDE/ARTICLE parsing                                  │
│    → JSON formatına dönüştür                                │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Vector Store'u Güncelle                                  │
│    → JSON'ları yükle                                         │
│    → Chunk'lara böl (800 char, 150 overlap)                │
│    → Embeddings oluştur (OpenAI)                            │
│    → ChromaDB'ye ekle                                        │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Loglar

Tüm güncelleme aktiviteleri log'lanır:

```bash
# Ana scheduler log
tail -f logs/scheduler.log

# Son güncellemeyi göster
grep "UPDATE JOB" logs/scheduler.log | tail -20

# Hataları göster
grep "ERROR" logs/scheduler.log
```

**Log Formatı:**
```
2026-02-01 12:00:00,123 - scheduler - INFO - ================================================================================
2026-02-01 12:00:00,124 - scheduler - INFO - UPDATE JOB STARTED: 2026-02-01T12:00:00
2026-02-01 12:00:00,125 - scheduler - INFO - Step 1: Scraping QDMS website...
2026-02-01 12:05:23,456 - scheduler - INFO - Scraping complete: 77 PDFs
2026-02-01 12:05:23,457 - scheduler - INFO - Step 2: Syncing with database...
2026-02-01 12:05:24,789 - scheduler - INFO - Sync stats: {'new': 2, 'updated': 3, 'unchanged': 72}
2026-02-01 12:05:24,790 - scheduler - INFO - Step 3: Processing 5 new/updated documents...
2026-02-01 12:08:15,123 - scheduler - INFO - Processing complete: 5 successful
2026-02-01 12:08:15,124 - scheduler - INFO - Step 4: Updating vector store...
2026-02-01 12:10:45,678 - scheduler - INFO - Vector store updated successfully: 247 chunks added
2026-02-01 12:10:45,679 - scheduler - INFO - ================================================================================
2026-02-01 12:10:45,680 - scheduler - INFO - UPDATE JOB COMPLETED: 2026-02-01T12:10:45
2026-02-01 12:10:45,681 - scheduler - INFO - Duration: 645.56 seconds
2026-02-01 12:10:45,682 - scheduler - INFO - Summary: 2 new, 3 updated, 72 unchanged
2026-02-01 12:10:45,683 - scheduler - INFO - ================================================================================
```

## 🔍 Monitoring

### Health Check

```bash
# Scheduler'ın çalışıp çalışmadığını kontrol et
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vector_store_status": "healthy",
  "database_status": "healthy"
}
```

### Sonraki Güncelleme Zamanı

Python'dan kontrol:
```python
from app.scheduler import UpdateScheduler

scheduler = UpdateScheduler()
scheduler.start()

# Sonraki çalışma zamanını göster
jobs = scheduler.scheduler.get_jobs()
if jobs:
    print(f"Next run: {jobs[0].next_run_time}")
```

## 🐛 Sorun Giderme

### Scheduler Çalışmıyor

**Problem:** Server başladı ama scheduler çalışmıyor.

**Çözüm:**
```bash
# Logs kontrol et
tail -f logs/server.log

# Manuel test yap
python test_scheduler.py
```

### QDMS'e Bağlanamıyor

**Problem:** Scraper QDMS web sitesine erişemiyor.

**Çözüm:**
```bash
# URL'i kontrol et
echo $QDMS_URL

# Manuel test
python -c "from app.scraper import QDMSScraper; s = QDMSScraper(); links = s.extract_qdms_links(); print(f'Found {len(links)} links')"
```

### ChromeDriver Hatası

**Problem:** Selenium ChromeDriver bulamıyor.

**Çözüm:**
```bash
# ChromeDriver kur
# macOS
brew install chromedriver

# Ubuntu
sudo apt install chromium-chromedriver

# Manuel indirme
# https://chromedriver.chromium.org/
```

### Vector Store Hatası

**Problem:** Vector store güncellenemiyor.

**Çözüm:**
```bash
# Vector store'u yeniden oluştur
cd backend
python -c "from app.rag import VectorStoreManager; m = VectorStoreManager(); m.create_or_load(); print('OK')"
```

### Database Bağlantı Hatası

**Problem:** PostgreSQL'e bağlanamıyor.

**Çözüm:**
```bash
# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql

# Connection string doğru mu?
echo $DATABASE_URL

# Test bağlantı
psql $DATABASE_URL -c "SELECT 1"
```

## 🎛️ İleri Seviye Kullanım

### Özel Interval

Farklı bir interval ile çalıştırma:

```python
from app.scheduler import UpdateScheduler

# 6 saatte bir çalışacak scheduler
scheduler = UpdateScheduler(interval_hours=6)
scheduler.start()
```

### Belirli Saatte Çalıştırma

Her gün saat 02:00'da çalışacak şekilde:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.scheduler import UpdateScheduler

scheduler_obj = UpdateScheduler()
scheduler = BackgroundScheduler()

# Her gün 02:00'da çalış
scheduler.add_job(
    func=scheduler_obj.update_job,
    trigger=CronTrigger(hour=2, minute=0),
    id='update_mevzuat',
    name='Daily Update at 2 AM'
)

scheduler.start()
```

### Hemen Çalıştır (Startup)

Server başladığında hemen bir kez güncelleme yap:

`run_server.py` içinde uncomment et:

```python
# print("\n🔄 Running initial update check...")
# scheduler.run_now()
# print("✅ Initial update complete")
```

## 📈 İstatistikler

Güncellemeler hakkında istatistik:

```bash
# Son 10 güncellemeyi göster
grep "UPDATE JOB COMPLETED" logs/scheduler.log | tail -10

# Ortalama süre hesapla
grep "Duration:" logs/scheduler.log | awk '{sum+=$NF; count++} END {print "Average:", sum/count, "seconds"}'

# Toplam yeni/güncellenen doküman
grep "Summary:" logs/scheduler.log | tail -20
```

## 🔐 Güvenlik Notları

- ⚠️ QDMS sitesi değişirse `QDMS_URL` güncellenmeli
- ⚠️ Scraping rate limiting olabilir (dikkatli kullanın)
- ✅ Hash comparison ile gereksiz işlem yapılmaz
- ✅ Başarısız güncellemeler log'lanır ama sistemi kilitlemez

## 📞 Destek

Sorun yaşarsanız:

1. **Logs kontrol et**: `logs/scheduler.log`
2. **Manuel test yap**: `python test_scheduler.py`
3. **Health check**: `curl http://localhost:8000/health`
4. **GitHub Issues**: Bug bildirin

---

**Son Güncelleme:** 2026-02-01  
**Versiyon:** 1.0.0
