# Sunucuya gönder (10.80.0.175 – behlulalar@~/behlul)

Buradaki her şey hazır; sadece **bir kez** `.env.sunucu` doldurup script’i çalıştır.

---

## 1. Burada (bir kez) – Sunucu bilgilerini yaz

`backend/.env.sunucu` dosyasını aç ve sadece şu iki satırı kendi değerlerinle değiştir:

- **DATABASE_URL** → Sunucudaki PostgreSQL kullanıcı ve şifre  
  Örnek: `postgresql://subu_user:GERCEK_SIFRE@localhost:5432/subu_chatbot`
- **OPENAI_API_KEY** → OpenAI API key (embedding için)  
  Örnek: `sk-proj-...`

Diğer satırlara dokunma (CORS, Qwen, portlar hazır).

---

## 2. Sunucuya gönder

Terminalde proje klasöründeyken:

```bash
chmod +x sunucuya_gonder.sh
./sunucuya_gonder.sh
```

Şifre sorulursa sunucu şifreni gir. Bu script:

- `.env`, `.env.sunucu`, backend, frontend, `start_on_server.sh` dahil **her şeyi**  
  **behlulalar@10.80.0.175** sunucusundaki **~/behlul** klasörüne kopyalar.  
- `node_modules`, `venv`, `.git`, büyük data klasörleri gönderilmez (hızlı olsun diye).

---

## 3. Sunucuda çalıştır

Sunucuya bağlan ve projeyi başlat:

```bash
ssh behlulalar@10.80.0.175
cd ~/behlul
chmod +x start_on_server.sh
./start_on_server.sh
```

İlk çalıştırmada script, `.env.sunucu` dosyasını `.env` yapıp backend ve frontend’i başlatır. Sunucuda **hiçbir dosyayı düzenlemen gerekmez**.

Tarayıcıdan: **http://10.80.0.175:3000**

---

## Notlar

- **ChromaDB:** İlk kez kullanıyorsan sunucuda `backend/data/chroma_db` boş olur.  
  İstersen bu klasörü başka makineden doldurup yine `sunucuya_gonder.sh` ile (exclude’u kaldırarak) tekrar gönderebilirsin; ya da sunucuda pipeline çalıştırırsın.
- **PostgreSQL:** Sunucuda veritabanı ve kullanıcı yoksa önce onu oluştur (SUNUCU_README.md’deki gibi).

Bu adımlarla her şey burada hazır; sadece `.env.sunucu` doldurup `./sunucuya_gonder.sh` çalıştırman yeterli.
