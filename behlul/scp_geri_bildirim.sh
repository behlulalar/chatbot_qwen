#!/bin/bash
# Geri bildirim değişikliklerini scp ile behlulalar@10.80.0.175:~/behlul/ adresine gönderir.
# Kullanım: Proje kökünden (subu_chatbot_v2) çalıştırın: ./behlul/scp_geri_bildirim.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
HOST="behlulalar@10.80.0.175"
BASE="~/behlul"

echo "→ Hedef: ${HOST}:${BASE}"
echo ""

# Backend
echo "Backend dosyaları..."
scp backend/app/models/response_feedback.py   "${HOST}:${BASE}/backend/app/models/response_feedback.py"
scp backend/app/models/__init__.py            "${HOST}:${BASE}/backend/app/models/__init__.py"
scp backend/app/api/feedback.py               "${HOST}:${BASE}/backend/app/api/feedback.py"
scp backend/app/main.py                       "${HOST}:${BASE}/backend/app/main.py"

# Frontend
echo "Frontend dosyaları..."
scp frontend/src/components/FeedbackModal.tsx  "${HOST}:${BASE}/frontend/src/components/FeedbackModal.tsx"
scp frontend/src/components/FeedbackModal.css "${HOST}:${BASE}/frontend/src/components/FeedbackModal.css"
scp frontend/src/components/FeedbackPanel.tsx "${HOST}:${BASE}/frontend/src/components/FeedbackPanel.tsx"
scp frontend/src/components/FeedbackPanel.css "${HOST}:${BASE}/frontend/src/components/FeedbackPanel.css"
scp frontend/src/components/ChatMessage.tsx   "${HOST}:${BASE}/frontend/src/components/ChatMessage.tsx"
scp frontend/src/components/ChatMessage.css   "${HOST}:${BASE}/frontend/src/components/ChatMessage.css"
scp frontend/src/components/ChatInterface.tsx  "${HOST}:${BASE}/frontend/src/components/ChatInterface.tsx"
scp frontend/src/components/ChatInterface.css "${HOST}:${BASE}/frontend/src/components/ChatInterface.css"
scp frontend/src/components/Sidebar.tsx       "${HOST}:${BASE}/frontend/src/components/Sidebar.tsx"
scp frontend/src/components/Sidebar.css       "${HOST}:${BASE}/frontend/src/components/Sidebar.css"

echo ""
echo "✅ Tüm dosyalar gönderildi."
echo "Sunucuda: ssh ${HOST}"
echo "Sonra: cd behlul && pkill -f run_server.py; ./start_on_server.sh"
