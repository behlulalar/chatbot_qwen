#!/bin/bash
# Aynı soruyu 2 kez gönderir; 2. yanıtta cache hit (metadata.cached=true) beklenir.
# Kişi B maddesi: "Aynı soruyu 2 kez at: 2. sorguda cache hit var mı?"
#
# Kullanım: ./deploy/test_cache_hit.sh
#   BASE_URL=http://10.80.0.175:8000 ./deploy/test_cache_hit.sh

set -e
BASE_URL="${BASE_URL:-http://10.80.0.175:8000}"
QUESTION="${TEST_QUESTION:-Akademik personele nasıl ödül verilir?}"

echo "→ Hedef: $BASE_URL"
echo "→ Soru: $QUESTION"
echo ""

PAYLOAD=$(printf '%s' "{\"question\":\"$QUESTION\",\"include_sources\":false}")

echo "1. istek (cache miss beklenir)..."
R1=$(curl -s -X POST "$BASE_URL/api/chat/" -H "Content-Type: application/json" -d "$PAYLOAD")
CACHED1=$(echo "$R1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('metadata',{}).get('cached', '?'))" 2>/dev/null || echo "?")
echo "   metadata.cached = $CACHED1"
echo ""

echo "2. istek (aynı soru — cache hit beklenir)..."
R2=$(curl -s -X POST "$BASE_URL/api/chat/" -H "Content-Type: application/json" -d "$PAYLOAD")
CACHED2=$(echo "$R2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('metadata',{}).get('cached', '?'))" 2>/dev/null || echo "?")
echo "   metadata.cached = $CACHED2"
echo ""

if [ "$CACHED2" = "True" ] || [ "$CACHED2" = "true" ]; then
  echo "✅ 2. sorguda cache hit var (Redis/LRU çalışıyor)."
  exit 0
else
  echo "❌ 2. sorguda cache hit yok (metadata.cached = $CACHED2)."
  echo "   REDIS_ENABLED=True ve API restart yapıldı mı? redis-cli ping PONG dönüyor mu?"
  exit 1
fi
