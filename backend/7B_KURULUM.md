# Qwen2.5 7B Kurulum ve Ayarlar

## 1. Model Kurulumu

```bash
# 7B modelini indir
ollama pull qwen2.5:7b
```

Opsiyonel (parametreleri sabitlemek için):

```bash
cd backend
ollama create subu-qwen-7b -f Modelfile.7b
```

## 2. .env Ayarları

`.env` dosyasında:

```env
LLM_BASE_URL=http://localhost:11434/v1
MODEL_NAME=qwen2.5:7b
MAX_TOKENS=800
```

`MAX_TOKENS=800` yanıt süresini kısaltır (varsayılan 1200 yerine).

Özel Modelfile kullandıysan: `MODEL_NAME=subu-qwen-7b`

## 3. Backend Başlatma

```bash
cd backend
python run_server.py
```

## 4. Testler

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

Ortamınıza göre: `python -m pytest tests/ -v` veya venv içinden çalıştırın.
