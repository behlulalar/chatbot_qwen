# SUBU Chatbot — Production Deploy (12 Mart Roadmap)

Bu klasör, **Kişi A** için 12 Mart Çarşamba maddelerine göre Gunicorn + systemd kurulumunu içerir.

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
