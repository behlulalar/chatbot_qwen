#!/bin/bash
# Sunucuda (10.80.0.175) tek komutla başlatma.
# Kullanım: ./start_on_server.sh

cd "$(dirname "$0")"
SERVER_IP="10.80.0.175"

# 1. Backend .env: yoksa .env.sunucu veya .env.server'dan oluştur
if [ ! -f backend/.env ]; then
  if [ -f backend/.env.sunucu ]; then
    cp backend/.env.sunucu backend/.env
    echo "  → backend/.env, .env.sunucu'dan oluşturuldu."
  elif [ -f backend/.env.server ]; then
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

# 4. Backend'i arka planda başlat
if pgrep -f "run_server.py" > /dev/null 2>&1 || pgrep -f "uvicorn.*app.main" > /dev/null 2>&1; then
  echo "→ Backend zaten çalışıyor."
else
  echo "→ Backend başlatılıyor (http://${SERVER_IP}:8000)..."
  cd backend
  nohup ./venv/bin/python run_server.py > ../backend.log 2>&1 &
  disown
  cd ..
  sleep 3

  if pgrep -f "run_server.py" > /dev/null 2>&1; then
    echo "  ✅ Backend başarıyla başlatıldı."
  else
    echo "  ❌ Backend başlatılamadı! Log: tail -50 backend.log"
    exit 1
  fi
fi

# 5. Frontend build (opsiyonel — başarısız olsa bile backend çalışmaya devam eder)
NEEDED=14
CURRENT=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [ -z "$CURRENT" ] || [ "$CURRENT" -lt "$NEEDED" ]; then
  echo ""
  echo "  ⚠️  Node.js 14+ gerekli. Şu an: $(node -v 2>/dev/null || echo 'yok')."
  echo "  Frontend build atlanıyor. Backend çalışıyor."
  echo ""
else
  if [ ! -d frontend/node_modules ]; then
    echo "→ Frontend bağımlılıkları yükleniyor..."
    (cd frontend && npm install)
  fi
  echo "→ Frontend derleniyor..."
  (cd frontend && npm run build) || echo "  ⚠️  Frontend build başarısız, backend yine çalışıyor."
fi

echo ""
echo "=============================================="
echo "  Adres: http://${SERVER_IP}:8000"
echo "  Durdurmak: pkill -f run_server.py"
echo "  Log: tail -f backend.log"
echo "=============================================="
