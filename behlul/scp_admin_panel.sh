#!/bin/bash
# Admin panel değişikliklerini scp ile behlulalar@10.80.0.175:~/behlul/ adresine gönderir.
# Kullanım: Proje kökünden (subu_chatbot_v2) çalıştırın: ./behlul/scp_admin_panel.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
HOST="behlulalar@10.80.0.175"
BASE="~/behlul"

echo "→ Hedef: ${HOST}:${BASE}"
echo ""

# Gerekli dizinleri oluştur
echo "Sunucuda dizinler oluşturuluyor..."
ssh "${HOST}" "mkdir -p ${BASE}/backend/app/core ${BASE}/frontend/src/context ${BASE}/frontend/src/pages"
echo ""

# Backend
echo "Backend dosyaları..."
scp backend/app/core/auth.py             "${HOST}:${BASE}/backend/app/core/auth.py"
scp backend/app/core/deps.py             "${HOST}:${BASE}/backend/app/core/deps.py"
scp backend/app/core/__init__.py         "${HOST}:${BASE}/backend/app/core/__init__.py"
scp backend/app/api/auth.py              "${HOST}:${BASE}/backend/app/api/auth.py"
scp backend/app/api/feedback.py          "${HOST}:${BASE}/backend/app/api/feedback.py"
scp backend/app/config.py                "${HOST}:${BASE}/backend/app/config.py"
scp backend/app/main.py                  "${HOST}:${BASE}/backend/app/main.py"
scp backend/requirements.txt             "${HOST}:${BASE}/backend/requirements.txt"

# Frontend
echo "Frontend dosyaları..."
scp frontend/src/context/AuthContext.tsx  "${HOST}:${BASE}/frontend/src/context/AuthContext.tsx"
scp frontend/src/pages/LoginPage.tsx      "${HOST}:${BASE}/frontend/src/pages/LoginPage.tsx"
scp frontend/src/pages/LoginPage.css      "${HOST}:${BASE}/frontend/src/pages/LoginPage.css"
scp frontend/src/pages/AdminLayout.tsx    "${HOST}:${BASE}/frontend/src/pages/AdminLayout.tsx"
scp frontend/src/pages/AdminLayout.css    "${HOST}:${BASE}/frontend/src/pages/AdminLayout.css"
scp frontend/src/pages/AdminDashboard.tsx "${HOST}:${BASE}/frontend/src/pages/AdminDashboard.tsx"
scp frontend/src/pages/AdminDashboard.css "${HOST}:${BASE}/frontend/src/pages/AdminDashboard.css"
scp frontend/src/pages/AdminFeedback.tsx  "${HOST}:${BASE}/frontend/src/pages/AdminFeedback.tsx"
scp frontend/src/pages/AdminPage.tsx      "${HOST}:${BASE}/frontend/src/pages/AdminPage.tsx"
scp frontend/src/App.tsx                  "${HOST}:${BASE}/frontend/src/App.tsx"
scp frontend/src/components/FeedbackPanel.tsx  "${HOST}:${BASE}/frontend/src/components/FeedbackPanel.tsx"
scp frontend/src/components/Sidebar.tsx   "${HOST}:${BASE}/frontend/src/components/Sidebar.tsx"
scp frontend/src/components/Sidebar.css   "${HOST}:${BASE}/frontend/src/components/Sidebar.css"
scp frontend/package.json                 "${HOST}:${BASE}/frontend/package.json"

echo ""
echo "✅ Tüm dosyalar gönderildi."
echo ""
echo "Not: Sunucuda backend/app/core/ ve frontend/src/context/ frontend/src/pages/ yoksa önce oluşturun:"
echo "  mkdir -p backend/app/core frontend/src/context frontend/src/pages"
echo ""
echo "Sunucuda: ssh ${HOST}"
echo "  cd behlul"
echo "  pip install -r backend/requirements.txt  (PyJWT, passlib eklenmiş olabilir)"
echo "  .env dosyasına ekle: ADMIN_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD"
echo "  cd frontend && npm install && npm run build"
echo "  pkill -f run_server.py; ./start_on_server.sh"
