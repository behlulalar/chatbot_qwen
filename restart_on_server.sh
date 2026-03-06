#!/bin/bash
# Backend'i durdurup tekrar başlatır.
cd "$(dirname "$0")"

# Durdur
pkill -f "run_server.py" 2>/dev/null
pkill -f "uvicorn.*app.main" 2>/dev/null
sleep 2

# Başlat
cd backend
source venv/bin/activate
export DEBUG=false
nohup python3 run_server.py >> ../backend.log 2>&1 &
disown
sleep 3

if pgrep -f "run_server.py" > /dev/null 2>&1; then
  echo "✅ Backend çalışıyor (PID: $(pgrep -f run_server.py | head -1))"
  echo "   http://10.80.0.175:8000"
  echo "   Log: tail -f ~/behlul/backend.log"
else
  echo "❌ Backend başlatılamadı!"
  echo "   Hata için: tail -50 ~/behlul/backend.log"
fi
