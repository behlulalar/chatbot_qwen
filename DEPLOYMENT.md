# 🚀 SUBU Mevzuat Chatbot v2.0 - Deployment Guide

## 📋 İçindekiler

1. [Gereksinimler](#gereksinimler)
2. [Docker ile Deployment (Önerilen)](#docker-ile-deployment)
3. [Manuel Deployment](#manuel-deployment)
4. [Windows Server Deployment](#windows-server-deployment)
5. [Production Checklist](#production-checklist)

---

## 🛠️ Gereksinimler

### Yazılımlar

**Docker ile Deployment:**
- Docker Desktop (Windows/Mac) veya Docker Engine (Linux)
- Docker Compose

**Manuel Deployment:**
- Python 3.9.6+
- Node.js 16+
- PostgreSQL 14+
- Nginx veya IIS (reverse proxy için)

### Donanım (Minimum)
- CPU: 2 core
- RAM: 4GB
- Disk: 10GB SSD

### Donanım (Önerilen)
- CPU: 4 core
- RAM: 8GB
- Disk: 20GB SSD
- Redis (optional, for caching)

---

## 🐳 Docker ile Deployment (Önerilen)

### 1. Proje Hazırlığı

```bash
# Repository'yi clone et
git clone <your-repo-url>
cd subu_chatbot_v2

# .env dosyasını oluştur
cp backend/.env.example backend/.env
```

### 2. .env Dosyasını Düzenle

```bash
# backend/.env
DATABASE_URL=postgresql://subu_user:SecurePassword123!@postgres:5432/subu_chatbot
OPENAI_API_KEY=sk-your-actual-openai-api-key
MODEL_NAME=gpt-4o-mini
DEBUG=False
REDIS_ENABLED=false

# İsteğe bağlı: Redis kullanmak için
# REDIS_ENABLED=true
# REDIS_HOST=redis
```

### 3. Docker Compose ile Başlat

```bash
# Container'ları build et ve başlat
docker-compose up -d --build

# Logları izle
docker-compose logs -f

# Durum kontrolü
docker-compose ps
```

### 4. İlk Veri Yükleme

```bash
# Backend container'a gir
docker exec -it subu_chatbot_backend bash

# Database tablolarını oluştur
python -c "from app.database import init_db; init_db()"

# PDF'leri indir ve vector store oluştur
python setup.py

# Container'dan çık
exit
```

### 5. Erişim

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📦 Manuel Deployment

### Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Dependencies yükle
pip install -r requirements.txt

# .env dosyasını yapılandır
cp .env.example .env
nano .env  # veya notepad .env

# Database'i hazırla
python -c "from app.database import init_db; init_db()"

# İlk veri yükleme
python setup.py

# Sunucuyu başlat
python run_server.py
```

### Frontend Kurulumu

```bash
cd frontend

# Dependencies yükle
npm install

# Production build
npm run build

# Build dosyalarını serve et (Nginx veya başka bir web server ile)
```

### Nginx Kurulumu (Frontend için)

```nginx
# /etc/nginx/sites-available/subu-chatbot
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (React build)
    location / {
        root /path/to/subu_chatbot_v2/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Nginx'i aktive et
sudo ln -s /etc/nginx/sites-available/subu-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🪟 Windows Server Deployment

### 1. Python ve PostgreSQL Kurulumu

```powershell
# Python 3.9.6 indir ve kur
# https://www.python.org/downloads/

# PostgreSQL 14+ indir ve kur
# https://www.postgresql.org/download/windows/

# Node.js 16+ indir ve kur
# https://nodejs.org/
```

### 2. PostgreSQL Database Oluştur

```sql
-- pgAdmin veya psql ile çalıştır
CREATE DATABASE subu_chatbot;
CREATE USER subu_user WITH PASSWORD 'SecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE subu_chatbot TO subu_user;
```

### 3. Backend Kurulumu

```powershell
cd C:\inetpub\subu_chatbot_v2\backend

# Virtual environment
python -m venv venv
venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# .env dosyasını düzenle
copy .env.example .env
notepad .env

# Database setup
python -c "from app.database import init_db; init_db()"

# İlk veri yükleme
python setup.py
```

### 4. Frontend Build

```powershell
cd C:\inetpub\subu_chatbot_v2\frontend

# Dependencies
npm install

# Production build
npm run build

# Build klasörü: frontend\build
```

### 5. Windows Service Olarak Çalıştırma (NSSM ile)

```powershell
# NSSM indir: https://nssm.cc/download

# Backend service oluştur
nssm install SUBUChatbotBackend
# Path: C:\inetpub\subu_chatbot_v2\backend\venv\Scripts\python.exe
# Startup directory: C:\inetpub\subu_chatbot_v2\backend
# Arguments: run_server.py

# Service'i başlat
nssm start SUBUChatbotBackend

# Service durumunu kontrol et
nssm status SUBUChatbotBackend
```

### 6. IIS ile Frontend Kurulumu

```powershell
# IIS Manager'ı aç
# Yeni Site oluştur:
# - Site name: SUBU Chatbot
# - Physical path: C:\inetpub\subu_chatbot_v2\frontend\build
# - Port: 80

# URL Rewrite modülünü yükle (gerekirse)
# https://www.iis.net/downloads/microsoft/url-rewrite

# web.config dosyası frontend\build\ klasörüne ekle
```

**web.config:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <!-- API proxy -->
        <rule name="API Proxy" stopProcessing="true">
          <match url="^api/(.*)" />
          <action type="Rewrite" url="http://localhost:8000/api/{R:1}" />
        </rule>
        
        <!-- React Router -->
        <rule name="React Router" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

---

## 🔒 Production Güvenlik

### 1. Güvenlik Ayarları

```bash
# .env dosyası izinleri
chmod 600 backend/.env  # Linux/Mac
# veya
icacls backend\.env /inheritance:r /grant:r "%USERNAME%:F"  # Windows

# DEBUG kapalı olmalı
DEBUG=False

# Güçlü database şifresi
DATABASE_URL=postgresql://subu_user:VeryStrongPassword!@localhost:5432/subu_chatbot
```

### 2. Firewall Kuralları (Windows)

```powershell
# Backend API port (internal)
New-NetFirewallRule -DisplayName "SUBU Chatbot API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Frontend (IIS ile çalışıyorsa port 80/443 zaten açık)
```

### 3. SSL Sertifikası

**Let's Encrypt (Ücretsiz):**
```bash
# Linux/Mac
sudo certbot --nginx -d your-domain.com

# Windows IIS
# https://www.win-acme.com/ kullan
```

---

## 📊 Monitoring ve Bakım

### Log Dosyaları

```
backend/logs/
├── server.log          # Ana sunucu
├── scheduler.log       # Otomatik güncelleme (24 saat)
├── api_chat.log        # Chat endpoint
└── scraper.log         # PDF indirme
```

### Log İzleme

```bash
# Linux/Mac
tail -f backend/logs/server.log

# Windows PowerShell
Get-Content backend\logs\server.log -Wait -Tail 50
```

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U subu_user -d subu_chatbot > backup_$(date +%Y%m%d).sql

# Restore
psql -U subu_user -d subu_chatbot < backup_20260201.sql
```

### Vector Store Yenileme

```bash
cd backend
source venv/bin/activate  # veya venv\Scripts\activate

# Vector store'u tamamen yenile
python rebuild_vectorstore_v2.py
```

### Cache Temizleme

```bash
# API endpoint ile
curl -X POST http://localhost:8000/api/chat/cache/clear

# veya Python ile
python -c "from app.utils.cache_manager import get_cache_manager; get_cache_manager().clear()"
```

---

## 🎯 Production Checklist

### Güvenlik
- [ ] DEBUG=False
- [ ] Güçlü database şifresi
- [ ] .env dosyası güvenli (chmod 600)
- [ ] Firewall kuralları yapılandırıldı
- [ ] SSL sertifikası kuruldu (HTTPS)
- [ ] CORS ayarları yapıldı

### Performance
- [ ] Redis cache aktif (opsiyonel)
- [ ] Nginx/IIS gzip compression aktif
- [ ] Static dosyalar CDN'den servis ediliyor (opsiyonel)
- [ ] Database index'ler oluşturuldu

### Monitoring
- [ ] Log rotation ayarlandı
- [ ] Disk alanı monitoring
- [ ] Uptime monitoring
- [ ] Error alerting

### Backup
- [ ] Günlük database backup
- [ ] Vector store backup
- [ ] .env dosyası backup
- [ ] Backup restore test edildi

### Servis
- [ ] Backend service/daemon olarak çalışıyor
- [ ] Otomatik başlatma aktif
- [ ] Scheduler çalışıyor (24 saat PDF update)
- [ ] Frontend web server ile servis ediliyor

---

## 🐛 Sorun Giderme

### Port Zaten Kullanımda

```bash
# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Bağlantı Hatası

```bash
# PostgreSQL servisini kontrol et
sudo systemctl status postgresql  # Linux
Get-Service postgresql*  # Windows

# Bağlantı test et
psql -U subu_user -d subu_chatbot -h localhost
```

### Vector Store Corruption

```bash
# Vector store'u sil ve yeniden oluştur
rm -rf backend/data/chroma_db  # Linux/Mac
Remove-Item -Recurse -Force backend\data\chroma_db  # Windows

# Yeniden oluştur
python backend/rebuild_vectorstore_v2.py
```

### Frontend Build Hatası

```bash
cd frontend

# node_modules temizle
rm -rf node_modules package-lock.json
npm install

# Yeniden build
npm run build
```

---

## 📞 Destek ve İletişim

- **Geliştirici:** BehlulAlar
- **LinkedIn:** [BehlulAlar](https://www.linkedin.com/in/behlulalar/)
- **Version:** 2.0.0

---

## 🔄 Güncelleme

```bash
# Yeni version'ı çek
git pull origin main

# Backend güncelle
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend güncelle
cd ../frontend
npm install
npm run build

# Servisleri yeniden başlat
# Docker:
docker-compose restart

# Manuel:
sudo systemctl restart subu-chatbot  # Linux
nssm restart SUBUChatbotBackend  # Windows
```

---

**🎉 Başarılı deployment sonrası chatbot'unuz kullanıma hazır!**
