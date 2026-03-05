#!/bin/bash
# Sunucuda ChromaDB oluşturur (processed_json + OpenAI embedding).
# Kullanım: cd ~/behlul/backend && ./chroma_olustur.sh

set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  echo "Önce venv oluştur: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

JSON_DIR="data/processed_json"
if [ ! -d "$JSON_DIR" ] || [ -z "$(ls -A $JSON_DIR/*.json 2>/dev/null)" ]; then
  echo "Hata: $JSON_DIR içinde .json dosyası yok."
  echo "Bu bilgisayarda şunu çalıştırıp JSON'ları gönderin:"
  echo "  rsync -avz backend/data/processed_json/ behlulalar@10.80.0.175:~/behlul/backend/data/processed_json/"
  exit 1
fi

echo "→ ChromaDB oluşturuluyor (processed_json + OpenAI embedding)..."
source venv/bin/activate
python build_vectorstore_only.py
echo "✅ Bitti. Backend'i yeniden başlatıp deneyebilirsiniz."
echo "   Arayüz: http://10.80.0.175:3001"
