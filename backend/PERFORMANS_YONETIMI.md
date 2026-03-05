# Performans ve Cevap Kalitesi Yönetimi

Bu belge, chatbot’un yavaş çalışması ve hatalı cevaplar için alınabilecek önlemleri açıklar.

## 1. Bilgisayar Donması / Kasma (ÇÖZÜLDÜ)

**Sorun:** Soru sorulduğunda tarayıcı/sunucu donuyor gibi hissediliyordu.

**Yapılan:** Chat API, ağır işlemleri (retrieval + LLM çağrısı) artık thread pool’da çalıştırıyor. Event loop bloke olmuyor, sunucu diğer isteklere yanıt verebiliyor.

**Test:** Sunucuyu yeniden başlatın (`python run_server.py`) ve tekrar deneyin. Donma hissi azalmış olmalı.

---

## 2. Yavaş Cevap Süresi

Cevap süresi genelde şunlardan kaynaklanır:

| Bileşen | Tahmini süre | Öneri |
|---------|--------------|--------|
| Retrieval (keyword + vector) | 0.5–2 sn | Cache kullan |
| LLM çağrısı (OpenAI) | 2–8 sn | - |
| LLM çağrısı (Ollama local) | 15–60+ sn | Daha hafif model veya `MAX_TOKENS` azalt |

**Öneriler:**

1. **Cache’i etkin tutun**  
   `.env` içinde Redis kapatıksa, en azından in-memory LRU cache kullanılır.  
   Aynı/benzer sorular tekrar sorulduğunda cevap hızlı gelir.

2. **Ollama 7B (önerilen)**
   - Model: `qwen2.5:7b` — Modelfile.7b ile `subu-qwen-7b` da oluşturulabilir.
   - `.env` içinde:
     - `MAX_TOKENS=800` (varsayılan 1200’den az)
   - GPU varsa CUDA ile çalıştığınızdan emin olun.

3. **Redis cache**
   - `.env`: `REDIS_ENABLED=true`  
   - Birden fazla kullanıcı/oturum için yanıtlar paylaşılır, yükleme azalır.

---

## 3. Yanlış Cevaplar

**Olası nedenler:**

- Yanlış veya alakasız kaynakların retrieval’a girmesi
- LLM’in prompt’u tam uygulayamaması
- Mevzuat dilinin belirsiz olması

**Yapılabilecekler:**

1. **Soruyu net sorun**  
   Örn: “Lisans mezuniyet şartları” yerine “Turizm Fakültesi lisans mezuniyet şartları”.

2. **Cache temizliği**  
   Yanlış cevap cache’lendiyse:
   - API: `POST /api/chat/cache/clear` (tüm cache)
   - `POST /api/chat/cache/clear?pattern=response:*` (sadece yanıtlar)

3. **Retrieval ayarları**  
   `retrieval.py` içinde `VECTOR_K`, `retrieval_k` değerleri doküman sayısına göre gözden geçirilebilir.

4. **Prompt güncellemesi**  
   `app/llm/prompts.py` içindeki `SYSTEM_PROMPT` ve `USER_PROMPT_TEMPLATE` ile kural ve örnekler güncellenebilir.

---

## 4. Hızlı Kontrol Listesi

- [ ] Sunucuyu yeniden başlattım (thread pool düzeltmesi için)
- [ ] `.env` içinde `MAX_TOKENS` uygun (Ollama için 800–1200)
- [ ] Ollama kullanıyorsam daha hafif model denedim
- [ ] Yanlış cevap varsa cache temizledim (`POST /api/chat/cache/clear`)
- [ ] Soruyu daha spesifik sordum

---

## 5. Teknik Notlar

- **Chat endpoint:** `asyncio.to_thread()` ile sync `generate_response` thread pool’da çalışır.
- **Stream endpoint:** Producer thread + `Queue` ile bloklayıcı işlem event loop’u kilitlemez.
- **Thread pool:** En fazla 4 worker, `chat.py` içinde `_executor`.
