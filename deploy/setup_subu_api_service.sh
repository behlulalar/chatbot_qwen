#!/bin/bash
# Sunucuda çalıştırın: subu-api.service dosyasını oluşturur.
# Kullanım: Sunucuda ~/behlul içindeyken: bash deploy/setup_subu_api_service.sh
# Veya: USER=behlulalar BACKEND=/home/behlulalar/behlul/backend bash setup_subu_api_service.sh

set -e
USER="${USER:-$(whoami)}"
# Script deploy/ altındaysa proje kökü bir üst dizin
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_ROOT="${BACKEND:-$(cd "$SCRIPT_DIR/.." && pwd)/backend}"
BACKEND_ROOT="$(cd "$BACKEND_ROOT" && pwd)"

echo "User: $USER"
echo "Backend: $BACKEND_ROOT"
echo ""

SERVICE_FILE="/etc/systemd/system/subu-api.service"
sudo tee "$SERVICE_FILE" << EOF
[Unit]
Description=SUBU Mevzuat Chatbot API (Gunicorn + Uvicorn)
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$BACKEND_ROOT
Environment="PATH=$BACKEND_ROOT/venv/bin"
ExecStart=$BACKEND_ROOT/venv/bin/gunicorn app.main:app \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 0.0.0.0:8000 \\
    --access-logfile $BACKEND_ROOT/logs/access.log \\
    --error-logfile $BACKEND_ROOT/logs/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

mkdir -p "$BACKEND_ROOT/logs"
sudo systemctl daemon-reload
sudo systemctl enable subu-api
sudo systemctl start subu-api
echo ""
echo "Durum:"
sudo systemctl status subu-api --no-pager || true
