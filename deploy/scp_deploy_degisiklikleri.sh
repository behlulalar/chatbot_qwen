#!/bin/bash
# Gunicorn + deploy (12 Mart) değişikliklerini SCP ile sunucuya gönderir.
# GitHub kullanmıyorsunuz; sadece bu dosyaları lokalden tek tek atıyorsunuz.
#
# Kullanım: Proje kökünden çalıştırın:
#   ./deploy/scp_deploy_degisiklikleri.sh
#
# Hedefi değiştirmek için:
#   HOST=kullanici@sunucu_ip BASE=/opt/subu_chatbot_v2 ./deploy/scp_deploy_degisiklikleri.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

HOST="${HOST:-behlulalar@10.80.0.175}"
BASE="${BASE:-~/behlul}"

echo "→ Hedef: ${HOST}:${BASE}"
echo "→ Gönderilen dosyalar (Gunicorn + deploy + Kişi B Redis):"
echo "  README.md, backend/requirements.txt, backend/app/schemas/chat.py"
echo "  deploy/README.md, deploy/subu-api.service, deploy/backup_before_pull.sh"
echo "  deploy/kisi_b_redis.md, deploy/test_cache_hit.sh"
echo ""

# Sunucuda deploy dizini olsun
ssh "${HOST}" "mkdir -p ${BASE}/deploy"

scp README.md                          "${HOST}:${BASE}/README.md"
scp backend/requirements.txt            "${HOST}:${BASE}/backend/requirements.txt"
scp backend/app/schemas/chat.py        "${HOST}:${BASE}/backend/app/schemas/chat.py"
scp deploy/README.md                    "${HOST}:${BASE}/deploy/README.md"
scp deploy/subu-api.service             "${HOST}:${BASE}/deploy/subu-api.service"
scp deploy/backup_before_pull.sh        "${HOST}:${BASE}/deploy/backup_before_pull.sh"
scp deploy/kisi_b_redis.md             "${HOST}:${BASE}/deploy/kisi_b_redis.md"
scp deploy/test_cache_hit.sh            "${HOST}:${BASE}/deploy/test_cache_hit.sh"

echo ""
echo "✅ Gönderim tamamlandı."
echo "   Sunucuda backend bağımlılıkları güncellemek için:"
echo "   ssh ${HOST} 'cd ${BASE}/backend && source venv/bin/activate && pip install -r requirements.txt'"
