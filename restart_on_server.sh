#!/bin/bash
# Sunucuda (10.80.0.175) backend ve frontend'i durdurup tekrar başlatır.
# Kullanım: ./restart_on_server.sh

set -e
cd "$(dirname "$0")"

echo "→ Mevcut süreçler durduruluyor..."

# Backend: run_server.py veya uvicorn
if pgrep -f "run_server.py" > /dev/null || pgrep -f "uvicorn.*app.main" > /dev/null; then
  pkill -f "run_server.py" 2>/dev/null || true
  pkill -f "uvicorn.*app.main" 2>/dev/null || true
  echo "  Backend durduruldu."
  sleep 2
else
  echo "  Backend zaten çalışmıyor."
fi

# Frontend: serve (port 3001)
if pgrep -f "serve.*3001" > /dev/null || lsof -i :3001 > /dev/null 2>&1; then
  pkill -f "serve.*3001" 2>/dev/null || true
  fuser -k 3001/tcp 2>/dev/null || true
  echo "  Frontend (port 3001) durduruldu."
  sleep 1
else
  echo "  Frontend zaten çalışmıyor."
fi

echo ""
echo "→ Sistem yeniden başlatılıyor..."
echo ""
exec ./start_on_server.sh
