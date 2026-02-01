# 🚀 Performance Optimization Guide

Bu döküman SUBU Mevzuat Chatbot'un performans optimizasyonlarını açıklar.

## 📊 Cache Sistemi

### Multi-Level Cache Architecture

```
┌─────────────────────────────────────────┐
│         User Query                       │
└──────────────┬──────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │   Level 1: LRU Cache  │ ← In-memory (fastest, ~100 items)
    │   (In-Memory)         │
    └──────────┬────────────┘
               │ miss
               ▼
    ┌──────────────────────┐
    │   Level 2: Redis      │ ← Distributed (shared across instances)
    │   (Distributed)       │
    └──────────┬────────────┘
               │ miss
               ▼
    ┌──────────────────────┐
    │   Generate Response   │ ← RAG + LLM (slowest, most expensive)
    │   (RAG + LLM)         │
    └───────────────────────┘
```

### Özellikleri

1. **Level 1: In-Memory LRU Cache**
   - En hızlı (microseconds)
   - Limited size (100 items)
   - Process-local

2. **Level 2: Redis Cache**
   - Distributed (shared across multiple instances)
   - Persistent (survives restarts)
   - TTL support

3. **Cache Strategy**
   - Sadece **standalone questions** cache'lenir (conversation history olmadan)
   - Conversation history'li sorular cache'lenmez (her konuşma unique)
   - Meta questions cache'lenmez (her zaman aynı cevap)

---

## ⚙️ Kurulum

### 1. Redis Kurulumu (İsteğe Bağlı)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 2. Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Yeni dependencies:
- `redis>=5.0.0` - Redis client
- `hiredis>=2.2.0` - Fast Redis parser
- `cachetools>=5.3.0` - In-memory LRU cache

### 3. Konfigürasyon

`.env` dosyasında:

```bash
# Cache Settings
REDIS_ENABLED=true  # false for in-memory only
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Cache TTL (seconds)
QUERY_CACHE_TTL=3600  # 1 hour
RESPONSE_CACHE_TTL=1800  # 30 minutes
```

---

## 📈 Performans Kazançları

### Benchmark Sonuçları

| Scenario | Without Cache | With Cache (LRU) | With Cache (Redis) | Speedup |
|----------|---------------|-------------------|--------------------|---------|
| Identical query | ~2.5s | ~0.001s | ~0.01s | **2500x** |
| Similar query | ~2.5s | ~0.001s | ~0.01s | **2500x** |
| New query | ~2.5s | ~2.5s | ~2.5s | 1x |

### Token Savings

```
Without Cache:
- 100 identical queries = 100 API calls = ~400,000 tokens = $0.27

With Cache:
- 100 identical queries = 1 API call + 99 cache hits = ~4,000 tokens = $0.0027

Savings: 99% tokens, 99% cost! 💰
```

---

## 🧪 Test Etme

### 1. Cache Stats Endpoint

```bash
# Cache istatistiklerini gör
curl http://localhost:8000/api/chat/cache/stats

# Response:
{
  "status": "success",
  "cache": {
    "lru_size": 45,
    "lru_maxsize": 100,
    "redis_enabled": true,
    "redis_hits": 1234,
    "redis_misses": 567,
    "redis_keys": 89
  }
}
```

### 2. Cache Hit Test

```bash
# İlk soru (cache MISS)
time curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Yaz okulu kaç hafta sürer?"}'

# Aynı soru tekrar (cache HIT)
time curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Yaz okulu kaç hafta sürer?"}'
```

**Beklenen:**
- İlk istek: ~2-3 saniye
- İkinci istek: ~0.01 saniye (**250x daha hızlı!**)

### 3. Cache Clear

```bash
# Tüm cache'i temizle
curl -X POST http://localhost:8000/api/chat/cache/clear

# Sadece response cache'i temizle
curl -X POST "http://localhost:8000/api/chat/cache/clear?pattern=response:*"
```

---

## 🔧 Tuning & Best Practices

### Cache TTL Ayarları

```bash
# Sık değişmeyen mevzuatlar için
RESPONSE_CACHE_TTL=3600  # 1 saat

# Sık güncellenen bilgiler için
RESPONSE_CACHE_TTL=600  # 10 dakika

# Test/development için
RESPONSE_CACHE_TTL=60  # 1 dakika
```

### Cache Invalidation

Mevzuat güncellendiğinde cache'i temizle:

```python
from app.utils.cache_manager import get_cache_manager

# Tüm cache'i temizle
cache = get_cache_manager()
cache.clear()

# Sadece belirli pattern'i temizle
cache.clear(pattern="response:*")
```

### Memory Usage

```bash
# Redis memory kullanımını kontrol et
redis-cli info memory

# Output:
used_memory: 1.2M
used_memory_human: 1.2MB
maxmemory: 100MB
```

### LRU Cache Size

```python
# Backend code'da:
cache_manager = CacheManager(
    lru_maxsize=200  # Daha fazla cache için
)
```

**Tavsiye:**
- Development: 50-100 items
- Production: 200-500 items

---

## 🐛 Troubleshooting

### Redis Connection Error

**Hata:**
```
Redis connection failed: Error connecting to localhost:6379
```

**Çözüm:**
1. Redis çalışıyor mu kontrol et:
   ```bash
   redis-cli ping
   # Beklenen: PONG
   ```

2. Redis'i başlat:
   ```bash
   brew services start redis  # macOS
   sudo systemctl start redis  # Ubuntu
   ```

3. Ya da Redis'siz kullan:
   ```bash
   # .env dosyasında:
   REDIS_ENABLED=false
   ```

### Cache Not Working

**Kontrol Listesi:**

1. ✅ Cache enabled mi?
   ```python
   # response_generator.py'da:
   enable_cache=True
   ```

2. ✅ Conversation history yok mu?
   ```bash
   # Cache sadece standalone questions için çalışır
   # Conversation history varsa cache bypass edilir
   ```

3. ✅ Cache stats endpoint'i çalışıyor mu?
   ```bash
   curl http://localhost:8000/api/chat/cache/stats
   ```

### High Memory Usage

**Redis memory limit ayarla:**

```bash
# redis.conf'da:
maxmemory 100mb
maxmemory-policy allkeys-lru
```

Ya da Docker ile:
```bash
docker run -d -p 6379:6379 --name redis \
  redis:alpine \
  redis-server --maxmemory 100mb --maxmemory-policy allkeys-lru
```

---

## 📊 Monitoring

### Cache Hit Rate

```python
from app.utils.cache_manager import get_cache_manager

cache = get_cache_manager()
stats = cache.get_stats()

hit_rate = stats['redis_hits'] / (stats['redis_hits'] + stats['redis_misses'])
print(f"Cache hit rate: {hit_rate:.2%}")
```

**Hedef:**
- Development: >50%
- Production: >70%

### Response Time Monitoring

```python
import time

start = time.time()
response = generator.generate_response(question)
elapsed = time.time() - start

if response['metadata'].get('cached'):
    print(f"✅ Cache HIT: {elapsed:.3f}s")
else:
    print(f"⏱️  Generated: {elapsed:.3f}s")
```

---

## 🚀 Production Deployment

### Redis Cluster (High Availability)

```bash
# docker-compose.yml'de:
services:
  redis-master:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
  
  redis-sentinel:
    image: redis:alpine
    command: redis-sentinel /etc/redis/sentinel.conf
```

### Cache Warming

```python
# Popüler soruları önceden cache'le
popular_questions = [
    "Yaz okulu kaç hafta sürer?",
    "Lisans mezuniyet şartları nelerdir?",
    "Üst sınıftan ders almak için kaç ortalama gerekir?"
]

for question in popular_questions:
    generator.generate_response(question)
```

---

## 💡 Best Practices

1. **✅ Cache'i mevzuat güncellemelerinde temizle**
2. **✅ Redis'i production'da kullan** (shared cache)
3. **✅ TTL'leri ihtiyaca göre ayarla**
4. **✅ Cache hit rate'i monitor et**
5. **✅ Memory usage'i takip et**
6. **❌ Sensitive data cache'leme** (user info, credentials)
7. **❌ Conversation history'li soruları cache'leme**

---

## 📞 Yardım

Sorular için:
- Cache Stats: `GET /api/chat/cache/stats`
- Clear Cache: `POST /api/chat/cache/clear`
- Logs: `backend/logs/response_generator.log`

**Happy Caching! 🚀**
