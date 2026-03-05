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

git Git kullanmıyorsanız Mac'teki proje klasöründen aşağıdaki komutlarla dosyaları sunucuya atabilirsiniz. `subu_chatbot_v2` ve sunucu IP'sini (`45.141.150.48`) kendi yolunuza göre değiştirin.

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

## Sık karşılaşılan sorunlar

### "sudo: unable to resolve host ..." uyarısı

Sunucu hostname'i DNS'te çözülemiyorsa sudo bu uyarıyı verir. Düzeltmek için:

```bash
# Mevcut hostname
hostname

# /etc/hosts'a ekle (hostname çıktısını kullanın)
echo "127.0.0.1 $(hostname)" | sudo tee -a /etc/hosts
```

Örnek: hostname `45-141-150-48.oyunlayici.com` ise:
```bash
echo "127.0.0.1 45-141-150-48.oyunlayici.com" | sudo tee -a /etc/hosts
```

### Backend doğru (debug'da 78 döküman) ama arayüzde 0 görünüyor

Siteye **http://45.141.150.48/** ile giriyorsanız, frontend'in API istekleri **http://45.141.150.48:8000** adresine gitmeli. Build sırasında bu adres verilmezse tarayıcı `localhost:8000`'e istek atar ve sunucudaki API'ye ulaşmaz.

**Sunucuda** (SSH ile bağlanıp) şunu çalıştırın:

```bash
cd /opt/local_chatbot_subu/frontend
REACT_APP_API_URL=http://45.141.150.48:8000 npm run build
```

Ardından Nginx'in bu build'i sunuyor olması gerekir (genelde `frontend/build` içeriği `/usr/share/nginx/html` veya benzeri bir yere kopyalanır). Build çıktısı zaten `/opt/local_chatbot_subu/frontend/build` altındaysa, Nginx root'u bu klasöre işaret ediyor olabilir; güncel build ile sayfayı **Ctrl+Shift+R** (hard refresh) ile yenileyin.

- Port **8000** sunucuda dışarıya açık olmalı (güvenlik duvarı). Açık değilse Nginx ile `/api`'yi backend'e proxy'leyip `REACT_APP_API_URL=http://45.141.150.48` ile build etmek gerekir.

### Build doğru ama hâlâ "0 doküman yüklü" (CORS veya port)

Frontend **http://45.141.150.48** üzerinden açıldığı için API'ye istek atarken **Origin: http://45.141.150.48** gider. Backend bu origin'i kabul etmezse tarayıcı yanıtı gizler ve sayı 0 görünür.

**1) Sunucuda backend `.env` dosyasında CORS'a frontend adresini ekleyin:**

```bash
# Backend .env (sunucuda: /opt/local_chatbot_subu/backend/.env)
# CORS_ORIGINS satırını şu şekilde yapın (virgülle ayırın):
CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://45.141.150.48,http://45.141.150.48:80
```

**2) Backend'i yeniden başlatın:**

```bash
sudo systemctl restart subu-backend
```

**3) Port 8000'in dışarıya açık olduğundan emin olun (sunucuda):**

```bash
sudo ufw allow 8000
sudo ufw status
# veya ufw kullanmıyorsanız iptables / firewall ayarınızı kontrol edin
```

**4) Tarayıcıda kontrol:** http://45.141.150.48 açıkken **F12 → Network** sekmesine girin, sayfayı yenileyin. `documents` veya `api/documents` isteğine tıklayın: **Status** 200 mü, yoksa (CORS) kırmızı / failed mı? CORS hatası varsa yukarıdaki CORS_ORIGINS düzeltmesi gerekir.

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

### Doküman sayısı hâlâ 0 – Debug

**1) Güncel documents.py’yi atın** (path çözümlemesi + debug endpoint eklendi):
```bash
# Mac'te
scp /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2/backend/app/api/documents.py root@45.141.150.48:/opt/local_chatbot_subu/backend/app/api/
```

**2) Sunucuda backend’i yeniden başlatın:**
```bash
sudo systemctl restart subu-backend
```

**3) Debug endpoint’e bakın (sunucuda veya tarayıcıdan):**
```bash
curl http://localhost:8000/api/documents/debug
```
Çıktıda göreceksiniz:
- `cwd` – Backend’in çalıştığı dizin
- `json_candidates` – Bakılan JSON klasörleri, `exists` ve `json_count`
- `json_dir_used` – Kullanılan klasör (burada dosya varsa sayı 0 olmaz)
- `vector_store_count` – Vector store’daki kayıt sayısı
- `db_count` – Veritabanındaki döküman sayısı

**4) Eğer `json_file_count` 0 ise** JSON’lar yanlış yerde. Doğru yerler:
- `/opt/local_chatbot_subu/backend/data/processed_json/`
- veya sunucuda `cwd` ne ise `cwd/data/processed_json/` veya `cwd/backend/data/processed_json/`

Örnek JSON’u oraya kopyalayıp **vector store’u oluşturun:**
```bash
cd /opt/local_chatbot_subu/backend
source venv/bin/activate
python load_manual_documents.py
sudo systemctl restart subu-backend
```

**5) Eğer `json_file_count` > 0 ama arayüzde hâlâ 0 görünüyorsa** API sayıyı JSON’dan döndürüyor olmalı; frontend’in doğru API’yi çağırdığından ve cache temizlendiğinden emin olun (Ctrl+Shift+R).

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
