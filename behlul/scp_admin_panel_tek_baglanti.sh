#!/bin/bash
# Admin panel dosyalarını TEK SSH bağlantısında tar ile gönderir (connection reset sorununu azaltır).
# Kullanım: Proje kökünden: ./behlul/scp_admin_panel_tek_baglanti.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
HOST="behlulalar@10.80.0.175"
BASE="behlul"

echo "→ Hedef: ${HOST}:~/${BASE} (tek bağlantı ile tar)"
echo ""

# Tek SSH bağlantısında: mkdir + tar ile tüm dosyaları gönder
tar cf - \
  backend/app/core/auth.py \
  backend/app/core/deps.py \
  backend/app/core/__init__.py \
  backend/app/api/auth.py \
  backend/app/api/feedback.py \
  backend/app/config.py \
  backend/app/main.py \
  backend/requirements.txt \
  frontend/src/context/AuthContext.tsx \
  frontend/src/pages/LoginPage.tsx \
  frontend/src/pages/LoginPage.css \
  frontend/src/pages/AdminLayout.tsx \
  frontend/src/pages/AdminLayout.css \
  frontend/src/pages/AdminDashboard.tsx \
  frontend/src/pages/AdminDashboard.css \
  frontend/src/pages/AdminFeedback.tsx \
  frontend/src/pages/AdminPage.tsx \
  frontend/src/App.tsx \
  frontend/src/components/FeedbackPanel.tsx \
  frontend/src/components/Sidebar.tsx \
  frontend/src/components/Sidebar.css \
  frontend/package.json \
  | ssh "${HOST}" "mkdir -p ${BASE}/backend/app/core ${BASE}/frontend/src/context ${BASE}/frontend/src/pages && cd ${BASE} && tar xf -"

echo ""
echo "✅ Tüm dosyalar tek bağlantı ile gönderildi."
echo "Sunucuda: cd ~/behlul && pip install -r backend/requirements.txt"
echo "  .env: ADMIN_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD"
echo "  cd frontend && npm install && npm run build && cd .. && ./start_on_server.sh"
echo ""
