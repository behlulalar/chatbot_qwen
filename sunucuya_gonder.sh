#!/bin/bash
# Projeyi behlulalar@10.80.0.175 sunucusundaki ~/behlul klasörüne gönderir.
# .env, .env.sunucu dahil her şey gider (node_modules, venv, .git hariç).

set -e
cd "$(dirname "$0")"
HEDEF="behlulalar@10.80.0.175:~/behlul/"

echo "→ Hedef: $HEDEF"
echo "→ .env / .env.sunucu dahil gönderiliyor..."
echo ""

rsync -avz \
  --exclude 'node_modules' \
  --exclude 'venv' \
  --exclude '.git' \
  --exclude 'backend/data/raw_pdfs' \
  --exclude 'backend/data/processed_json' \
  --exclude 'backend/data/chroma_db' \
  --exclude 'frontend/build' \
  ./ "$HEDEF"

echo ""
echo "✅ Gönderim tamamlandı."
echo "   Sunucuda: ssh behlulalar@10.80.0.175"
echo "   Sonra:    cd ~/behlul && chmod +x start_on_server.sh && ./start_on_server.sh"
echo "   Arayüz:   http://10.80.0.175:3000"
