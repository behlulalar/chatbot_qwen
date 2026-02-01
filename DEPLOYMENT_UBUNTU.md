# 🐧 Ubuntu 22.04 Deployment Rehberi

Bu rehber, SUBU Mevzuat Chatbot'u Ubuntu 22.04 sunucuya deploy etmek için adım adım talimatlar içerir.

## 📋 Gereksinimler

- Ubuntu 22.04 LTS sunucu
- Root veya sudo yetkisi
- Domain adı (opsiyonel, nginx için)
- OpenAI API key

## 🚀 Hızlı Deployment (Docker ile)

### 1. Sunucu Hazırlığı

```bash
# Sistem güncellemesi
sudo apt update && sudo apt upgrade -y

# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose kurulumu
sudo apt install docker-compose-plugin -y

# Git kurulumu
sudo apt install git -y
```

### 2. Projeyi Klonla

```bash
# Projeyi indir
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/subu_chatbot_v2.git
cd subu_chatbot_v2

# Dosya sahipliğini ayarla
sudo chown -R $USER:$USER /opt/subu_chatbot_v2
```

### 3. Environment Dosyalarını Ayarla

```bash
# Backend .env
cd /opt/subu_chatbot_v2/backend
cp .env.example .env
nano .env
```

**Backend .env içeriği:**
```env
# Database
DATABASE_URL=postgresql://subu_user:STRONG_PASSWORD_HERE@postgres:5432/subu_chatbot

# OpenAI
OPENAI_API_KEY=sk-your-actual-openai-key-here

# App Settings
APP_NAME=SUBU Mevzuat Chatbot
DEBUG=False

# LLM
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.1

# CORS (production domain ekle)
CORS_ORIGINS=http://your-domain.com,https://your-domain.com,http://your-ip-address

# Cache (opsiyonel - Redis kullanmak için)
REDIS_ENABLED=False
```

```bash
# Frontend .env
cd /opt/subu_chatbot_v2/frontend
cp .env.example .env.production
nano .env.production
```

**Frontend .env.production içeriği:**
```env
REACT_APP_API_URL=http://your-domain.com:8000
# veya
REACT_APP_API_URL=http://your-ip-address:8000
```

### 4. Docker ile Başlat

```bash
cd /opt/subu_chatbot_v2

# Docker Compose ile başlat
docker-compose up -d

# Logları izle
docker-compose logs -f
```

### 5. İlk Veri Yükleme

```bash
# Backend container'a gir
docker exec -it subu_backend bash

# Data pipeline'ı çalıştır
python setup_data_pipeline.py

# Container'dan çık
exit
```

### 6. Servis Kontrolü

```bash
# Servislerin durumunu kontrol et
docker-compose ps

# Logları kontrol et
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Yeniden başlat (gerekirse)
docker-compose restart
```

## 🔧 Manuel Deployment (Production için)

### 1. Sistem Hazırlığı

```bash
# Temel paketler
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql nginx nodejs npm git

# PostgreSQL başlat
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. PostgreSQL Ayarları

```bash
# PostgreSQL'e gir
sudo -u postgres psql

# Database ve user oluştur
CREATE DATABASE subu_chatbot;
CREATE USER subu_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE subu_chatbot TO subu_user;
\q
```

### 3. Backend Kurulumu

```bash
# Proje dizini
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/subu_chatbot_v2.git
cd subu_chatbot_v2/backend

# Sahiplik ayarla
sudo chown -R $USER:$USER /opt/subu_chatbot_v2

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt
pip install gunicorn

# .env dosyası
cp .env.example .env
nano .env
# DATABASE_URL ve OPENAI_API_KEY'i ayarla

# Data pipeline
python setup_data_pipeline.py
```

### 4. Systemd Service (Backend)

```bash
sudo nano /etc/systemd/system/subu-backend.service
```

**Service dosyası:**
```ini
[Unit]
Description=SUBU Chatbot Backend
After=network.target postgresql.service

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/opt/subu_chatbot_v2/backend
Environment="PATH=/opt/subu_chatbot_v2/backend/venv/bin"
ExecStart=/opt/subu_chatbot_v2/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /opt/subu_chatbot_v2/backend/logs/access.log \
    --error-logfile /opt/subu_chatbot_v2/backend/logs/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service'i başlat
sudo systemctl daemon-reload
sudo systemctl start subu-backend
sudo systemctl enable subu-backend
sudo systemctl status subu-backend
```

### 5. Frontend Kurulumu

```bash
cd /opt/subu_chatbot_v2/frontend

# Node.js 18+ kurulumu (gerekirse)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build
npm install
REACT_APP_API_URL=http://your-domain.com:8000 npm run build
```

### 6. Nginx Konfigürasyonu

```bash
sudo nano /etc/nginx/sites-available/subu-chatbot
```

**Nginx config:**
```nginx
# Backend API
upstream backend_api {
    server 127.0.0.1:8000;
}

# Frontend
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (React)
    location / {
        root /opt/subu_chatbot_v2/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://backend_api/health;
    }

    # Logs
    access_log /var/log/nginx/subu-chatbot-access.log;
    error_log /var/log/nginx/subu-chatbot-error.log;
}
```

```bash
# Nginx'i aktifleştir
sudo ln -s /etc/nginx/sites-available/subu-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL/HTTPS (Let's Encrypt)

```bash
# Certbot kurulumu
sudo apt install certbot python3-certbot-nginx -y

# SSL sertifikası al
sudo certbot --nginx -d your-domain.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

## 🔄 Güncelleme (Update)

### Docker ile:
```bash
cd /opt/subu_chatbot_v2
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Manuel:
```bash
cd /opt/subu_chatbot_v2

# Backend
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart subu-backend

# Frontend
cd ../frontend
npm install
REACT_APP_API_URL=http://your-domain.com:8000 npm run build
sudo systemctl restart nginx
```

## 📊 Monitoring

### Logs
```bash
# Backend logs
tail -f /opt/subu_chatbot_v2/backend/logs/server.log

# Systemd logs
sudo journalctl -u subu-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/subu-chatbot-access.log
```

### Health Check
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://your-domain.com
```

## 🔐 Güvenlik

### Firewall (UFW)
```bash
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

### Fail2Ban (SSH koruması)
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### PostgreSQL Güvenlik
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
# local   all   all   peer -> md5
sudo systemctl restart postgresql
```

## 🐛 Sorun Giderme

### Backend çalışmıyor
```bash
# Logs kontrol
sudo journalctl -u subu-backend -n 50

# Manuel test
cd /opt/subu_chatbot_v2/backend
source venv/bin/activate
python run_server.py
```

### Frontend boş sayfa
```bash
# Build kontrol
cd /opt/subu_chatbot_v2/frontend
npm run build
# Console'da error var mı kontrol et

# Nginx test
sudo nginx -t
sudo systemctl status nginx
```

### Vector store boş
```bash
cd /opt/subu_chatbot_v2/backend
source venv/bin/activate
python setup_data_pipeline.py --rebuild
```

### Database bağlantısı yok
```bash
# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql

# Database var mı?
sudo -u postgres psql -c "\l" | grep subu_chatbot

# Connection test
psql -h localhost -U subu_user -d subu_chatbot
```

## 📈 Performance Optimization

### Gunicorn Workers
```bash
# CPU sayısını öğren
nproc

# Workers = (2 x CPU) + 1
# 4 CPU için: (2 x 4) + 1 = 9 workers
```

### PostgreSQL Tuning
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf

# Ayarlar (4GB RAM için örnek)
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 10MB
```

### Nginx Caching
```nginx
# /etc/nginx/nginx.conf içine ekle
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
```

## 🔄 Backup

### Otomatik Backup Script
```bash
sudo nano /opt/backup-subu.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/subu"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U subu_user subu_chatbot > "$BACKUP_DIR/db_$DATE.sql"

# Data files backup
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /opt/subu_chatbot_v2/backend/data

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Çalıştırılabilir yap
sudo chmod +x /opt/backup-subu.sh

# Cron job ekle (her gün 2:00'da)
sudo crontab -e
# Ekle: 0 2 * * * /opt/backup-subu.sh >> /var/log/subu-backup.log 2>&1
```

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. GitHub Issues'a bildirin
3. Dokümantasyonu inceleyin

**Başarılar!** 🎉
