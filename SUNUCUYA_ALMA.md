# Sunucuya Değişiklikleri Alma Rehberi

## Seçenek 1: Git ile (Önerilen)

### Mac'te (Local)
```bash
cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2

git status
git add -A
git commit -m "fix: Doküman sayısı fallback + mobil sidebar kapatma"
git push origin main
```

### Ubuntu Sunucuda
```bash
cd /opt/local_chatbot_subu
git pull origin main

# Backend yeniden başlat
sudo systemctl restart subu-backend

# Frontend yeniden build
cd frontend
npm run build
```

---

## Seçenek 2: SCP ile Dosya Kopyalama

### Mac'te - Tek komutla tüm değişen dosyaları gönder
```bash
# Backend
scp /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2/backend/app/api/documents.py \
  root@45.141.150.48:/opt/local_chatbot_subu/backend/app/api/

# Frontend (4 dosya)
scp /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2/frontend/src/components/{Sidebar.tsx,Sidebar.css,ChatInterface.tsx,ChatInterface.css} \
  root@45.141.150.48:/opt/local_chatbot_subu/frontend/src/components/
```

### Ubuntu Sunucuda
```bash
sudo systemctl restart subu-backend
cd /opt/local_chatbot_subu/frontend && npm run build
```

---

## Kontrol Listesi

### 1. Backend güncel mi?
```bash
# Sunucuda
grep -A2 "Fallback: when DB is empty" /opt/local_chatbot_subu/backend/app/api/documents.py
```
"Fallback" satırını görüyorsan backend güncel.

### 2. Backend çalışıyor mu?
```bash
curl http://localhost:8000/api/documents/?limit=1
```
`total` alanı 0'dan büyük olmalı (veya vector store / JSON sayısı).

### 3. Frontend build güncel mi?
```bash
# Sunucuda build tarihi
ls -la /opt/local_chatbot_subu/frontend/build/static/js/*.js | head -1
```

### 4. Tarayıcı cache
- Sayfayı Ctrl+Shift+R (hard refresh) ile yenile
- Veya mobilde tarayıcı cache'ini temizle

---

## Hâlâ Olmadıysa

### Doküman sayısı hâlâ 0
```bash
# Sunucuda log kontrol
sudo journalctl -u subu-backend -n 30 | grep -i document

# JSON dosya sayısı (fallback için)
ls /opt/local_chatbot_subu/backend/data/processed_json/*.json | wc -l
```

### Sidebar kapanmıyor
- Sidebar'da **X (kapat)** butonuna tıkla
- Mobilde koyu alana (overlay) tıkla
- Tarayıcıda hard refresh (Ctrl+Shift+R)
