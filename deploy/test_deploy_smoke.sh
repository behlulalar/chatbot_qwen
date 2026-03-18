#!/bin/bash
# Deploy sonrası sunucudaki API'nin canlı testi (smoke test).
# Lokal makinenizden çalıştırın; sunucu adresi varsayılan: http://10.80.0.175:8000
#
# Kullanım:
#   ./deploy/test_deploy_smoke.sh
#   BASE_URL=http://sunucu:8000 ./deploy/test_deploy_smoke.sh

set -e
BASE_URL="${BASE_URL:-http://10.80.0.175:8000}"
FAIL=0

echo "→ Hedef: $BASE_URL"
echo ""

# 1. Health
echo -n "GET /health ... "
HTTP=$(curl -s -o /tmp/subu_health.json -w "%{http_code}" --connect-timeout 5 "$BASE_URL/health" || true)
if [ "$HTTP" = "200" ]; then
  echo "OK ($HTTP)"
  cat /tmp/subu_health.json | head -c 120
  echo "..."
else
  echo "FAIL (HTTP $HTTP)"
  FAIL=1
fi
echo ""

# 2. Documents
echo -n "GET /api/documents/ ... "
HTTP=$(curl -s -o /tmp/subu_docs.json -w "%{http_code}" --connect-timeout 5 "$BASE_URL/api/documents/" || true)
if [ "$HTTP" = "200" ]; then
  echo "OK ($HTTP)"
else
  echo "FAIL (HTTP $HTTP)"
  FAIL=1
fi
echo ""

# 3. Cache stats
echo -n "GET /api/chat/cache/stats ... "
HTTP=$(curl -s -o /tmp/subu_cache.json -w "%{http_code}" --connect-timeout 5 "$BASE_URL/api/chat/cache/stats" || true)
if [ "$HTTP" = "200" ]; then
  echo "OK ($HTTP)"
else
  echo "FAIL (HTTP $HTTP)"
  FAIL=1
fi
echo ""

# 4. Root/API bilgisi
echo -n "GET / (veya /api) ... "
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE_URL/" || true)
if [ "$HTTP" = "200" ]; then
  echo "OK ($HTTP)"
else
  echo "FAIL (HTTP $HTTP)"
  FAIL=1
fi
echo ""

if [ $FAIL -eq 0 ]; then
  echo "✅ Tüm smoke testler geçti."
  exit 0
else
  echo "❌ Bazı testler başarısız. Sunucu çalışıyor mu? Port 8000 açık mı?"
  exit 1
fi
