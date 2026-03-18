# SUBU Chatbot — Production Deploy (12 Mart Roadmap)

Bu klasör, **Kişi A** (Gunicorn + systemd) ve **Kişi B** (Redis + cache test) maddelerine göre kurulum ve testleri içerir.

---

## Güncelleme öncesi: Sunucuda yedek (tar)

Sunucuya `git pull` veya dosya kopyalamadan **önce** mevcut proje halini tar ile yedeklemek için:

**1. Script'i sunucuya kopyalayın (veya repoyu zaten çektiyseniz sunucuda `deploy/` altında vardır):**
```bash
# Örnek: yerelde
scp deploy/backup_before_pull.sh kullanici@sunucu:/opt/subu_chatbot_v2/
```

**2. Sunucuda çalıştırın:**
```bash
ssh kullanici@sunucu
cd /opt/subu_chatbot_v2
chmod +x backup_before_pull.sh
./backup_before_pull.sh
```

Veya proje dizini farklıysa:
```bash
PROJECT_ROOT=/opt/local_chatbot_subu ./backup_before_pull.sh
```

Yedekler varsayılan olarak `/opt/backups/subu/subu_project_full_YYYYMMDD_HHMMSS.tar.gz` olarak kaydedilir. `venv`, `node_modules`, `.git` hariç tutulur; son 5 yedek saklanır.

**3. Ardından sadece değişen dosyaları güncelleyin:** GitHub’dan `git pull` veya aşağıdaki SCP script’i ile lokalden sunucuya gönderin.

### Lokalden SCP ile sadece değişen dosyaları gönderme

Sunucuya GitHub’dan değil, kendi lokalinden `scp` ile tek tek dosya gönderiyorsanız:

**Hazır script (proje kökünden):**
```bash
./deploy/scp_deploy_degisiklikleri.sh
```
Varsayılan hedef: `behlulalar@10.80.0.175:~/behlul`. Farklı hedef için:
```bash
HOST=kullanici@sunucu_ip BASE=/opt/subu_chatbot_v2 ./deploy/scp_deploy_degisiklikleri.sh
```

**Gönderilen dosyalar:** `README.md`, `backend/requirements.txt`, `deploy/README.md`, `deploy/subu-api.service`, `deploy/backup_before_pull.sh`

**Elle tek tek SCP örneği:**
```bash
scp README.md                    kullanici@sunucu:~/behlul/
scp backend/requirements.txt    kullanici@sunucu:~/behlul/backend/
scp deploy/README.md            kullanici@sunucu:~/behlul/deploy/
scp deploy/subu-api.service     kullanici@sunucu:~/behlul/deploy/
scp deploy/backup_before_pull.sh kullanici@sunucu:~/behlul/deploy/
```
Sunucuda `deploy` klasörü yoksa önce: `ssh kullanici@sunucu "mkdir -p ~/behlul/deploy"`

---

## Adım 1: Gunicorn kurulumu

Backend sanal ortamı aktifken:

```bash
cd backend
pip install gunicorn
# veya tüm bağımlılıklarla:
pip install -r requirements.txt
```

## Adım 2: 4 worker ile başlatma

Uygulama `backend/app/main.py` içinde tanımlı; Gunicorn için modül adı **`app.main:app`** (görseldeki `main:app` proje köküne göre; bizim yapıda `app.main:app` kullanılır).

**Backend dizininden** çalıştırın:

```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

- `-w 4`: 4 worker
- `-k uvicorn.workers.UvicornWorker`: FastAPI (ASGI) için Uvicorn worker
- `--bind 0.0.0.0:8000`: Dinlenecek adres ve port

## Adım 3: systemd servis dosyası

Sunucuda servis dosyası: **`/etc/systemd/system/subu-api.service`**

Repodaki şablonu kopyalayıp yolu ve kullanıcıyı düzenleyin:

```bash
sudo cp deploy/subu-api.service /etc/systemd/system/subu-api.service
sudo nano /etc/systemd/system/subu-api.service
# BACKEND_ROOT ve User/Group değerlerini sunucuya göre güncelleyin
```

## Adım 4: systemctl enable + start + status

```bash
sudo systemctl daemon-reload
sudo systemctl enable subu-api
sudo systemctl start subu-api
sudo systemctl status subu-api
```

## Adım 5: Gunicorn'ın Uvicorn'dan hızlı cevap verdiğini doğrulama

1. **Sadece Uvicorn** ile başlatın (tek process):
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Başka bir terminalde birkaç kez: `time curl -s -o /dev/null -w "%{time_total}\n" http://localhost:8000/health`

2. **Gunicorn (4 worker)** ile başlatın:
   ```bash
   cd backend && gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
   Aynı `time curl` testini tekrarlayın.

Gunicorn ile eşzamanlı isteklerde (ör. 4 paralel curl) ortalama yanıt süresi ve throughput, tek Uvicorn process’e göre daha iyi olmalıdır.

---

## Production .env: DEBUG ve CORS

Sunucudaki `backend/.env` dosyasında:

1. **DEBUG=False**  
   Production'da mutlaka `False` olmalı (detaylı hata mesajları dışarı sızmaz).

2. **CORS_ORIGINS**  
   Sadece frontend'in erişeceği adres(ler), virgülle ayrılmış:
   - IP ile erişiyorsanız: `http://10.80.0.175,http://10.80.0.175:80`
   - Domain kullanıyorsanız: `https://chat.subu.edu.tr`

Örnek satırlar:
```env
DEBUG=False
CORS_ORIGINS=http://10.80.0.175,http://10.80.0.175:80
```

Değişiklikten sonra: `sudo systemctl restart subu-api`

---

## PostgreSQL bağlantı havuzu (Adım 3–4)

Backend'de her worker için **pool_size=5**, **max_overflow=5** kullanılıyor. Toplam: 4 worker × (5+5) = **en fazla 40** bağlantı.

**Kontrol:** PostgreSQL `max_connections` bu değeri kaldırmalı (varsayılan 100 yeterli). Sunucuda:

```bash
sudo -u postgres psql -c "SHOW max_connections;"
```

Çıkan sayı ≥ 40 olmalı. Düşükse `postgresql.conf` içinde `max_connections` artırılıp PostgreSQL yeniden başlatılmalı.

---

## Deploy sonrası test

### 1. Sunucu canlı test (smoke test) — lokalden

Deploy ettikten sonra sunucudaki API'nin ayakta olduğunu doğrulamak için (lokal makinenizden):

```bash
chmod +x deploy/test_deploy_smoke.sh
./deploy/test_deploy_smoke.sh
```

Varsayılan adres: `http://10.80.0.175:8000`. Farklı adres/port için:

```bash
BASE_URL=http://10.80.0.175:8000 ./deploy/test_deploy_smoke.sh
```

Script şunları kontrol eder: `GET /health`, `GET /api/documents/`, `GET /api/chat/cache/stats`, `GET /`. Hepsi 200 dönmeli.

### 2. Lokal unit testler (pytest)

Kod tarafında değişiklik yaptıktan sonra, sunucuya göndermeden önce lokalde test almak için:

```bash
cd backend
source venv/bin/activate
pytest -v
```

Sadece API testleri: `pytest tests/test_api.py -v`

---

## Kişi B — Redis ve cache hit testi

Redis kurulumu, `REDIS_ENABLED=True` ve "aynı soruyu 2 kez at, 2.’de cache hit mi?" adımları için tam rehber:

**[deploy/kisi_b_redis.md](kisi_b_redis.md)**

Kısa özet:
1. Sunucuda: `sudo apt install redis-server` → `systemctl enable redis-server` → `redis-cli ping` (PONG).
2. Backend `.env`: `REDIS_ENABLED=True` → API’yi yeniden başlat.
3. Cache hit testi (lokalden): `./deploy/test_cache_hit.sh` — aynı soru iki kez gider, ikinci yanıtta `metadata.cached: true` beklenir.
4. Bellek: Sunucuda `redis-cli info memory`.
