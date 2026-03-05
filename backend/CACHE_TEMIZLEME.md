# Cache temizleme ve “yanıt bulunamadı” kontrolü

## 1. Cache’i temizleme

### Yöntem A: API ile (önerilen)
Backend çalışırken tarayıcı veya terminalden:

**Tüm cache’i temizle:**
```bash
curl -X POST "http://localhost:8000/api/chat/cache/clear"
```

**Sadece cevap cache’ini temizle (response):**
```bash
curl -X POST "http://localhost:8000/api/chat/cache/clear?pattern=response:*"
```

Başarılı yanıt örneği: `{"status":"success","cleared_keys":5,"pattern":null}`

### Yöntem B: Sunucuyu yeniden başlatma
- Redis **kapalıysa** (`REDIS_ENABLED=False`, varsayılan): Cache sadece bellekte (LRU). Sunucuyu durdurup (Ctrl+C) tekrar `python run_server.py` ile başlatın; cache sıfırlanır.
- Redis **açıksa**: Bellek cache’i yeniden başlatmayla silinir; Redis’teki cache için Yöntem A’yı kullanın veya `redis-cli FLUSHDB` çalıştırın.

---

## 2. Hangi endpoint kullanılıyor?

Frontend **streaming değil**, normal chat kullanıyor:
- `frontend/src/components/ChatInterface.tsx` → `axios.post(..., '/api/chat/', ...)` (POST `/api/chat/`).
- “Yanıt bulunamadı” farklı bir endpoint yüzünden değil; gelen cevap metni veya eski cache’ten kaynaklanıyor olabilir.

---

## 3. Cevap metnini kontrol etme

“Bilgi bulunamadı” bazen **LLM’in ürettiği cevap metninin içinde** olur (API 200 döner, ama metin “bilgi bulunamadı” diyor). Kontrol için:

**Tarayıcıda:**
1. Geliştirici araçları (F12) → Network.
2. Soruyu gönderin, istek listesinde `chat` isteğine tıklayın.
3. “Response” sekmesinde `answer` alanına bakın: Uzun bir metin mi yoksa “bilgi/yanıt bulunamadı” gibi kısa bir cümle mi?

**Terminalden:**
```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"question":"Arge komisyonunun görevleri nelerdir","include_sources":true}' | python3 -m json.tool
```
Çıktıdaki `"answer"` değeri, kullanıcıya göstereceğiniz cevaptır.

---

## Özet
1. Cache’i temizleyin: `curl -X POST "http://localhost:8000/api/chat/cache/clear"` veya sunucuyu yeniden başlatın.
2. Aynı soruyu tekrar sorun; hâlâ “yanıt bulunamadı” geliyorsa Network/curl ile `answer` içeriğine bakın.
3. Frontend şu an streaming kullanmıyor; sorun endpoint farkından kaynaklanmıyor.
