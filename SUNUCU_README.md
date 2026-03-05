# Sunucuda Çalıştırma (10.80.0.175)

Projeyi bu sunucuya kopyaladıktan sonra aşağıdaki adımlarla çalıştırın.

## 1. İlk kurulum (bir kez)

### PostgreSQL
```bash
sudo -u postgres psql -c "CREATE DATABASE subu_chatbot;"
sudo -u postgres psql -c "CREATE USER subu_user WITH PASSWORD 'güçlü_bir_şifre';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE subu_chatbot TO subu_user;"
```

### Ollama + Qwen 14B
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:14b
```

### Node.js 18+ (frontend için)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Projeyi sunucuya kopyala

Bilgisayarında (rsync ile):
```bash
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '.git' \
  --exclude 'backend/data/raw_pdfs' --exclude 'backend/data/processed_json' \
  ./ KULLANICI@10.80.0.175:/opt/subu_chatbot_v2/
```

Sunucuda klasör yoksa:
```bash
sudo mkdir -p /opt/subu_chatbot_v2
sudo chown $USER:$USER /opt/subu_chatbot_v2
```

## 3. .env düzenle (ilk çalıştırmada)

Sunucuda:
```bash
cd /opt/subu_chatbot_v2
./start_on_server.sh
```
Script `backend/.env` yoksa `.env.server` kopyalar ve çıkar. Sonra:

```bash
nano backend/.env
```
Şunları doldur:
- `DATABASE_URL=postgresql://subu_user:GÜÇLÜ_ŞİFRE@localhost:5432/subu_chatbot`
- `OPENAI_API_KEY=sk-...` (ChromaDB embedding için)

Kaydet, tekrar:
```bash
./start_on_server.sh
```

## 4. ChromaDB verisi

- **Seçenek A:** Başka makinede oluşturduğun `backend/data/chroma_db` klasörünü sunucuya kopyala (rsync ile).
- **Seçenek B:** Sunucuda pipeline çalıştır (OPENAI_API_KEY gerekir, PDF’ler veya processed_json gerekir):
  ```bash
  cd /opt/subu_chatbot_v2/backend && source venv/bin/activate && python setup_data_pipeline.py
  ```

## 5. Başlatma

```bash
cd /opt/subu_chatbot_v2
chmod +x start_on_server.sh
./start_on_server.sh
```

Tarayıcıdan: **http://10.80.0.175:3000**

---

## 0 doküman görünüyorsa (teşhis)

**Ollama CPU → GPU taşıma döküman sayısını etkilemez.** Embedding’ler OpenAI ile yapılıyor; Ollama sadece cevap üretimi (LLM) için kullanılıyor. ChromaDB verisi Ollama’dan bağımsızdır.

0 doküman genelde şunlardan kaynaklanır:
- Sunucuda ChromaDB hiç oluşturulmamış veya `data/chroma_db` boş
- GPU’ya geçerken sunucu/yol değiştiyse ChromaDB klasörü kopyalanmamış olabilir

**Teşhis (sunucu API’si açıkken):** Tarayıcıda veya curl ile:
```text
http://10.80.0.175:8000/api/chroma-debug
```
Dönen JSON’da `resolved_path`, `path_exists`, `count`, `error` alanlarına bakın.

**Çözüm:**
1. **ChromaDB’yi sunucuda yeniden oluştur:**  
   `processed_json` klasörü dolu olmalı (başka makineden rsync ile atabilirsiniz).
   ```bash
   cd ~/behlul/backend && ./chroma_olustur.sh
   ```
2. **Veya** başka makinedeki dolu `backend/data/chroma_db` klasörünü sunucuya kopyalayın:
   ```bash
   rsync -avz backend/data/chroma_db/ behlulalar@10.80.0.175:~/behlul/backend/data/chroma_db/
   ```
3. Backend’i yeniden başlatın: `./restart_on_server.sh`

---

**Özet:** İlk seferde `.env` düzenle → `./start_on_server.sh`. Sonraki seferlerde sadece `./start_on_server.sh`.
