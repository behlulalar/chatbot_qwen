# Sunucuda ChromaDB Oluşturma

Chatbot’un cevap verebilmesi için vektör veritabanı (ChromaDB) gerekir. İki yol var.

---

## Yol 1: Bu bilgisayardan ChromaDB’yi kopyala (en hızlı)

Zaten bu bilgisayarda ChromaDB oluşturduysan, tüm `chroma_db` klasörünü sunucuya atman yeterli.

**Bu bilgisayarda (Mac):**
```bash
cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2
rsync -avz backend/data/chroma_db/ behlulalar@10.80.0.175:~/behlul/backend/data/chroma_db/
```

Sunucuda başka bir şey yapmana gerek yok; backend zaten `backend/data/chroma_db` kullanıyor.

---

## Yol 2: Sunucuda ChromaDB’yi sıfırdan oluştur

Sunucuda **processed_json** (işlenmiş mevzuat JSON’ları) ve **OpenAI API key** gerekir.

### Adım 1: processed_json’ı sunucuya kopyala

Bu bilgisayarda JSON’lar `backend/data/processed_json/` içinde. Sunucuya gönder:

```bash
cd /Users/muhammedbehlulalar/Desktop/subu_chatbot_v2
rsync -avz backend/data/processed_json/ behlulalar@10.80.0.175:~/behlul/backend/data/processed_json/
```

### Adım 2: Sunucuda ChromaDB’yi oluştur

Sunucuda:

```bash
cd ~/behlul/backend
source venv/bin/activate
python build_vectorstore_only.py
```

- `.env` içinde **OPENAI_API_KEY** dolu olmalı (embedding için kullanılır).
- Script, `data/processed_json` içindeki tüm `.json` dosyalarını okuyup chunk’layacak, OpenAI ile embedding alıp ChromaDB’ye yazacak. Birkaç dakika sürebilir.

İlk seferde sıfırdan kuruyorsan `--rebuild` kullanma; zaten dolu bir Chroma’yı silip yeniden kurmak istersen:

```bash
python build_vectorstore_only.py --rebuild
```

---

## "0 doküman" hâlâ görünüyorsa

Backend’in ChromaDB klasörünü doğru bulduğundan emin ol. Sunucuda `backend/.env` içinde **mutlak path** ver:

```env
CHROMA_PERSIST_DIRECTORY=/home/behlulalar/behlul/backend/data/chroma_db
```

Backend’i yeniden başlat, arayüzü yenile.

---

## Kontrol

Backend çalışırken:

```bash
curl http://10.80.0.175:8000/health
```

Veya tarayıcıdan bir soru sor; kaynak bulunamıyorsa ChromaDB boş veya yol yanlış demektir.

**Özet:** Hızlı yol = chroma_db’yi rsync ile kopyala. Yoksa processed_json’ı kopyala + sunucuda `build_vectorstore_only.py` çalıştır.
