#!/bin/bash
# Sunucuda frontend'i 3001 portunda sunar. Bu script frontend/ klasöründe çalıştırılmalı.
# Kullanım: cd ~/behlul/frontend && ./serve_port_3001.sh

set -e
cd "$(dirname "$0")"
PORT=3001

if [ ! -d node_modules ] || [ ! -f node_modules/.bin/react-scripts ]; then
  echo "→ node_modules yok veya eksik, npm install çalıştırılıyor..."
  npm install
fi
if [ ! -f build/index.html ]; then
  echo "→ build/index.html yok, derleme yapılıyor..."
  npm run build
fi

echo "→ Arayüz: http://10.80.0.175:${PORT} (veya bu makinenin IP:${PORT})"
echo "→ Durdurmak için: Ctrl+C"
echo ""

# build klasörünün İÇİNDEN serve çalıştır (kök = build)
cd build
npx serve -s . -l "$PORT"
