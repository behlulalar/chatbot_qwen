#!/bin/bash
# Sunucuda (10.80.0.175) tek komutla başlatma.
# Kullanım: ./start_on_server.sh

set -e
cd "$(dirname "$0")"
SERVER_IP="10.80.0.175"

# 1. Backend .env: yoksa .env.sunucu veya .env.server'dan oluştur
if [ ! -f backend/.env ]; then
  if [ -f backend/.env.sunucu ]; then
    cp backend/.env.sunucu backend/.env
    echo "  → backend/.env, .env.sunucu'dan oluşturuldu."
  else
    cp backend/.env.server backend/.env
    echo "  → backend/.env oluşturuldu. Lütfen DATABASE_URL ve OPENAI_API_KEY düzenleyin."
    echo "  Sonra tekrar: ./start_on_server.sh"
    exit 1
  fi
fi

# 2. Backend venv
if [ ! -d backend/venv ]; then
  echo "→ Backend sanal ortam oluşturuluyor..."
  python3 -m venv backend/venv
  backend/venv/bin/pip install --upgrade pip
  backend/venv/bin/pip install -r backend/requirements.txt
fi

# 3. Log ve data klasörleri
mkdir -p backend/logs
mkdir -p backend/data/chroma_db backend/data/raw_pdfs backend/data/processed_json

# 4. Backend'i arka planda başlat (zaten çalışmıyorsa)
if ! (pgrep -f "run_server.py" > /dev/null || pgrep -f "uvicorn.*app.main" > /dev/null); then
  echo "→ Backend başlatılıyor (http://${SERVER_IP}:8000)..."
  (cd backend && ./venv/bin/python run_server.py) &
  sleep 4
else
  echo "→ Backend zaten çalışıyor."
fi

# 5. Frontend (Node 14+ gerekir; Node 12 ise SUNUCU_NODE_KURULUM.md'ye bakın)
NEEDED=14
CURRENT=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [ -z "$CURRENT" ] || [ "$CURRENT" -lt "$NEEDED" ]; then
  echo ""
  echo "  ⚠️  Node.js 14+ gerekli. Şu an: $(node -v 2>/dev/null || echo 'yok')."
  echo "  Sunucuda: SUNUCU_NODE_KURULUM.md dosyasındaki adımları uygulayın."
  echo ""
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "→ Frontend bağımlılıkları yükleniyor..."
  (cd frontend && npm install)
fi
echo "→ Frontend derleniyor (tek port için)..."
(cd frontend && npm run build)
echo ""
echo "=============================================="
echo "  Tek adres: http://${SERVER_IP}:8000  (arayüz + API)"
echo "  Durdurmak için: pkill -f run_server.py"
echo "=============================================="
echo ""
echo "→ Backend çalışıyor; arayüz ve API aynı portta."
echo "  Tarayıcıda: http://${SERVER_IP}:8000"
