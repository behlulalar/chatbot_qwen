# 🪟 Windows Server Deployment Guide

Bu rehber, SUBU Mevzuat Chatbot'unun Windows Server'a deployment edilmesi için adımları içerir.

## 📋 Gereksinimler

### Yazılımlar
- ✅ Windows Server 2016+ veya Windows 10+
- ✅ Python 3.9+
- ✅ PostgreSQL 14+
- ✅ Git (opsiyonel)
- ✅ Chrome Browser + ChromeDriver

### Donanım (Minimum)
- CPU: 2 core
- RAM: 4GB
- Disk: 10GB

### Donanım (Önerilen)
- CPU: 4 core
- RAM: 8GB
- Disk: 20GB
- SSD önerilir

---

## 🔧 Kurulum Adımları

### 1. Python Kurulumu

1. [Python 3.9.6 İndir](https://www.python.org/downloads/)
2. Kurulum sırasında "Add Python to PATH" seçeneğini işaretle
3. Kurulumu doğrula:
```powershell
python --version
```

### 2. PostgreSQL Kurulumu

1. [PostgreSQL İndir](https://www.postgresql.org/download/windows/)
2. Kurulum sırasında şifre belirle
3. pgAdmin ile database oluştur:
```sql
CREATE DATABASE subu_chatbot;
CREATE USER subu_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE subu_chatbot TO subu_user;
```

### 3. Chrome ve ChromeDriver

1. Google Chrome yükle
2. [ChromeDriver İndir](https://chromedriver.chromium.org/)
3. Chrome versiyonunla uyumlu olanı seç
4. `chromedriver.exe`'yi `C:\Windows\System32\` veya proje klasörüne koy

### 4. Proje Kurulumu

```powershell
# Proje dizinine git
cd C:\inetpub\subu_chatbot_v2

# Git ile indir (opsiyonel)
git clone <repository_url> .

# Backend kurulumu
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env
notepad .env
```

### 5. .env Dosyası Düzenleme

```env
DATABASE_URL=postgresql://subu_user:your_password@localhost:5432/subu_chatbot
OPENAI_API_KEY=sk-your-actual-api-key
DEBUG=False
```

### 6. İlk Veri Yükleme

```powershell
# Database tablolarını oluştur
python -c "from app.database import init_db; init_db()"

# PDF'leri indir ve işle
python test_scraper.py  # Seçenek 3
python test_pdf_processor.py  # Seçenek 2
python test_rag_pipeline.py  # Seçenek 3
```

---

## 🚀 Sunucuyu Başlatma

### Geliştirme Modu

```powershell
cd backend
venv\Scripts\activate
python run_server.py
```

### Production Modu (Windows Service)

#### Option 1: NSSM (Non-Sucking Service Manager)

1. [NSSM İndir](https://nssm.cc/download)
2. Service oluştur:

```powershell
# NSSM ile service oluştur
nssm install SUBUChatbot

# Ayarlar:
Path: C:\inetpub\subu_chatbot_v2\backend\venv\Scripts\python.exe
Startup directory: C:\inetpub\subu_chatbot_v2\backend
Arguments: run_server.py

# Service'i başlat
nssm start SUBUChatbot
```

#### Option 2: Task Scheduler

1. Task Scheduler'ı aç
2. "Create Task" tıkla
3. Ayarlar:
   - Name: SUBU Chatbot
   - Trigger: At system startup
   - Action: Start a program
   - Program: `C:\inetpub\subu_chatbot_v2\backend\venv\Scripts\python.exe`
   - Arguments: `run_server.py`
   - Start in: `C:\inetpub\subu_chatbot_v2\backend`

---

## 🌐 Nginx / IIS Kurulumu (Opsiyonel)

### IIS Reverse Proxy

1. IIS'e URL Rewrite ve ARR modüllerini yükle
2. Yeni site oluştur
3. Reverse proxy kuralı ekle:
```xml
<rewrite>
  <rules>
    <rule name="API Proxy" stopProcessing="true">
      <match url="api/(.*)" />
      <action type="Rewrite" url="http://localhost:8000/api/{R:1}" />
    </rule>
  </rules>
</rewrite>
```

---

## 🔒 Güvenlik

### Firewall Kuralları

```powershell
# Port 8000'i aç (internal)
New-NetFirewallRule -DisplayName "SUBU Chatbot API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Port 8501'i aç (Streamlit)
New-NetFirewallRule -DisplayName "SUBU Chatbot UI" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

### SSL Sertifikası (Production)

1. SSL sertifikası al (Let's Encrypt veya kurum sertifikası)
2. IIS'e yükle
3. HTTPS binding ekle

---

## 📊 Monitoring ve Logging

### Log Dosyaları

```
backend/logs/
├── server.log          # Ana sunucu
├── scheduler.log       # Otomatik güncelleme
├── api_chat.log        # Chat endpoint
└── scraper.log         # PDF indirme
```

### Log İzleme (PowerShell)

```powershell
# Real-time log izleme
Get-Content logs\server.log -Wait -Tail 50
```

---

## 🔄 Bakım ve Güncelleme

### Manuel Güncelleme Kontrolü

```powershell
cd backend
venv\Scripts\activate
python -c "from app.scheduler import UpdateScheduler; scheduler = UpdateScheduler(); scheduler.run_now()"
```

### Vector Store Yenileme

```powershell
# Vector store'u sil ve yeniden oluştur
Remove-Item -Recurse -Force data\chroma_db
python test_rag_pipeline.py  # Seçenek 3
```

### Database Backup

```powershell
# PostgreSQL backup
pg_dump -U subu_user -d subu_chatbot > backup_%date%.sql

# Restore
psql -U subu_user -d subu_chatbot < backup_YYYYMMDD.sql
```

---

## 🐛 Sorun Giderme

### Port Zaten Kullanımda

```powershell
# Port 8000'i kullanan process'i bul
netstat -ano | findstr :8000

# Process'i sonlandır
taskkill /PID <PID> /F
```

### ChromeDriver Hatası

```powershell
# Chrome versiyonunu kontrol et
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version

# Uyumlu ChromeDriver'ı indir
```

### PostgreSQL Bağlantı Hatası

```powershell
# PostgreSQL servisini kontrol et
Get-Service postgresql*

# Servisi başlat
Start-Service postgresql-x64-14
```

---

## 📞 Destek

Hata durumunda log dosyalarını kontrol edin:
- `backend/logs/server.log`
- `backend/logs/scheduler.log`

## 🎯 Production Checklist

- [ ] PostgreSQL şifresi güçlü
- [ ] .env dosyası güvenli
- [ ] Firewall kuralları yapılandırıldı
- [ ] SSL sertifikası kuruldu (HTTPS)
- [ ] Log rotation ayarlandı
- [ ] Backup stratejisi belirlendi
- [ ] Monitoring kuruldu
- [ ] Service olarak çalışıyor
- [ ] Otomatik başlatma aktif
