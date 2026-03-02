# Sunucuya Değişiklikleri Alma Rehberi

## Değişiklik yaptığımız dosyalar

| Dosya | Açıklama |
|-------|----------|
| `backend/app/api/documents.py` | Döküman sayısı fallback, path çözümleme |
| `backend/setup_data_pipeline.py` | MevzuatChunker kullanımı |
| `backend/build_vectorstore_only.py` | `--rebuild` seçeneği, path düzeltmesi |
| `backend/load_manual_documents.py` | **Yeni:** Manuel PDF/JSON yükleme script'i |
| `backend/data/processed_json/sample_mevzuat.json` | **Yeni:** Örnek mevzuat (demo) |
| `frontend/src/components/Sidebar.tsx` | Sidebar kapatma, döküman sayısı |
| `frontend/src/components/Sidebar.css` | Sidebar stilleri |
| `SUNUCUYA_ALMA.md` | Bu rehber |

---

## Seçenek 1: Git ile (Önerilen)

### Mac'te (Local)
```bash
cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2

git status
git add -A
git commit -m "fix: vector store updates"
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

Git kullanmıyorsanız Mac'teki proje klasöründen aşağıdaki komutlarla dosyaları sunucuya atabilirsiniz. `subu_chatbot_v2` ve sunucu IP'sini (`45.141.150.48`) kendi yolunuza göre değiştirin.

### Mac'te – Backend dosyalarını atma
```bash
# Sunucu adresi (IP'yi kendi sunucunuza göre değiştirin)
H=root@45.141.150.48
P=/opt/local_chatbot_subu

# Tek tek atma
scp backend/app/api/documents.py $H:$P/backend/app/api/
scp backend/setup_data_pipeline.py backend/build_vectorstore_only.py backend/load_manual_documents.py $H:$P/backend/
ssh $H "mkdir -p $P/backend/data/processed_json"
scp backend/data/processed_json/sample_mevzuat.json $H:$P/backend/data/processed_json/
```
*(Komutları Mac'te proje klasöründen çalıştırın: `cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2`)*

**Tek satırda (hepsini birden):**
```bash
cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2
scp backend/setup_data_pipeline.py backend/build_vectorstore_only.py backend/load_manual_documents.py root@45.141.150.48:/opt/local_chatbot_subu/backend/
scp backend/app/api/documents.py root@45.141.150.48:/opt/local_chatbot_subu/backend/app/api/
ssh root@45.141.150.48 "mkdir -p /opt/local_chatbot_subu/backend/data/processed_json"
scp backend/data/processed_json/sample_mevzuat.json root@45.141.150.48:/opt/local_chatbot_subu/backend/data/processed_json/
```

### Mac'te – Frontend dosyalarını atma (değiştirdiyseniz)
```bash
scp /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2/frontend/src/components/{Sidebar.tsx,Sidebar.css} root@45.141.150.48:/opt/local_chatbot_subu/frontend/src/components/
```

### Ubuntu sunucuda – Son adım
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

### Doküman sayısı 0 ve chatbot cevap vermiyor

Sunucuda scraping çalışmadığı için `data/` boş olabilir. Örnek veri ile vector store oluşturun:

**1) Örnek JSON'u sunucuya kopyalayın (Mac'te):**
```bash
ssh root@45.141.150.48 "mkdir -p /opt/local_chatbot_subu/backend/data/processed_json"
scp /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2/backend/data/processed_json/sample_mevzuat.json \
  root@45.141.150.48:/opt/local_chatbot_subu/backend/data/processed_json/
```

**2) Sunucuda vector store'u oluşturun:**
```bash
cd /opt/local_chatbot_subu/backend
source venv/bin/activate
python build_vectorstore_only.py
```

**3) Backend'i yeniden başlatın:**
```bash
sudo systemctl restart subu-backend
```

Bundan sonra döküman sayısı 0'dan çıkar ve chatbot örnek metne göre cevap verebilir. Gerçek mevzuat için scraping’i internete erişebilen bir makinede çalıştırıp `data/` klasörünü sunucuya kopyalayabilirsiniz.

### Manuel eklediğiniz PDF/JSON'ları sisteme yüklemek

Sunucuda `data/raw_pdfs` veya `data/processed_json` içine manuel kopyaladığınız dosyalar varsa, bunların LLM tarafından kullanılması için **vector store** oluşturulmalı. Aşağıdaki script hem PDF'leri JSON'a çevirir hem tüm JSON'lardan vector store'u yeniden oluşturur hem de (isteğe bağlı) veritabanına kaydeder:

**Sunucuda (tek komut):**
```bash
cd /opt/local_chatbot_subu/backend
source venv/bin/activate
python load_manual_documents.py
sudo systemctl restart subu-backend
```

- **PDF'ler** `backend/data/raw_pdfs/` içinde olmalı; script henüz JSON'u olmayan her PDF'i JSON'a çevirip `data/processed_json/` içine yazar.
- **JSON'lar** doğrudan `backend/data/processed_json/` içine kopyalanabilir; script bu klasördeki tüm `.json` dosyalarını okuyup vector store'u sıfırdan oluşturur.
- Sadece vector store istiyorsanız (DB'ye kayıt istemiyorsanız): `python load_manual_documents.py --no-db`

### Doküman sayısı hâlâ 0 (genel kontrol)
```bash
# Sunucuda log kontrol
sudo journalctl -u subu-backend -n 30 | grep -i document

# JSON dosya sayısı (fallback için)
ls /opt/local_chatbot_subu/backend/data/processed_json/*.json 2>/dev/null | wc -l
```

### Sidebar kapanmıyor
- Sidebar'da **X (kapat)** butonuna tıkla
- Mobilde koyu alana (overlay) tıkla
- Tarayıcıda hard refresh (Ctrl+Shift+R)
