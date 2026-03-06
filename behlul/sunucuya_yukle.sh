#!/bin/bash
# Tek dosya yükle: scp ile behlulalar@10.80.0.175:~/behlul/
# Kullanım: ./behlul/sunucuya_yukle.sh <dosya_yolu>
# Örnek:   ./behlul/sunucuya_yukle.sh backend/app/rag/chunker.py

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
HEDEF="behlulalar@10.80.0.175:~/behlul/"

if [ $# -eq 0 ]; then
  echo "Kullanım: $0 <dosya> [dosya2 ...]"
  echo "Örnek:   $0 backend/app/rag/chunker.py"
  exit 1
fi

for f in "$@"; do
  if [ -f "$f" ]; then
    echo "→ Gönderiliyor: $f"
    scp "$f" "$HEDEF$f"
    echo "   ✓ $f"
  else
    echo "   ✗ Yok: $f"
  fi
done

echo ""
echo "✅ Bitti. Sunucuda: ssh behlulalar@10.80.0.175"
