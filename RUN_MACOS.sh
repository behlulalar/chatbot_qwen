#!/bin/bash
# macOS/Linux için başlatma script'i

echo "========================================"
echo "SUBU Mevzuat Chatbot Başlatılıyor..."
echo "========================================"
echo ""

cd backend

# Virtual environment'i aktif et
source venv/bin/activate

# Sunucuyu başlat
echo "Sunucu başlatılıyor..."
python run_server.py
