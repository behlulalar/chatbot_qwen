#!/bin/bash
# Sadece son yapılan değişikliklerdeki dosyaları sunucuya gönderir.
# Hedef: behlulalar@10.80.0.175:~/behlul/

set -e
cd "$(dirname "$0")"
HEDEF="behlulalar@10.80.0.175:~/behlul/"

# Gönderilecek dosyalar (bu konuşmada değiştirdiklerimiz)
FILES=(
  "backend/app/main.py"
  "SUNUCU_README.md"
  "restart_on_server.sh"
)

echo "→ Hedef: $HEDEF"
echo "→ Sadece şu dosyalar gönderiliyor:"
for f in "${FILES[@]}"; do echo "   - $f"; done
echo ""

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    rsync -avz "$f" "$HEDEF$f"
  else
    echo "⚠️  Atlandı (yok): $f"
  fi
done

echo ""
echo "✅ Gönderim tamamlandı."
echo "   Sunucuda yeniden başlatmak için: cd ~/behlul && chmod +x restart_on_server.sh && ./restart_on_server.sh"
