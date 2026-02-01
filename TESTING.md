# 🧪 Chatbot Doğruluk Testi

Bu döküman, SUBU Mevzuat Chatbot'un doğruluğunu test etmek için kullanabileceğin araçları açıklıyor.

## 📋 İçindekiler

1. [Otomatik Test](#otomatik-test)
2. [Manuel Test](#manuel-test)
3. [Sürekli İyileştirme](#sürekli-iyileştirme)
4. [Test Sonuçlarını Yorumlama](#test-sonuçlarını-yorumlama)

---

## 🤖 Otomatik Test

### Test Script'i Çalıştır

```bash
cd backend

# Colorama kütüphanesini yükle (ilk kez)
pip install colorama

# Test'i çalıştır
python test_accuracy.py
```

### Test Kategorileri

Test script'i şu kategorileri kontrol eder:

1. **✅ Doğru Kaynak Bulma**
   - Diploma vs Eğitim-Öğretim yönergesi
   - Lisans vs Lisansüstü ayrımı
   - Yurt içi vs Yurt dışı öğrenci ayrımı

2. **✅ Doğru Cevap Verme**
   - Sayısal bilgiler (2.50 ortalama, 4 yıl, vb.)
   - Prosedür bilgileri (bütünleme sınavı, vb.)
   - Meta sorular (sen kimsin, vb.)

3. **✅ Yanlış Bilgi Vermeme**
   - Lisans öğrencisi için yüksek lisans bilgisi vermemeli
   - Türk öğrenci için yurt dışı kabul bilgisi vermemeli
   - Mevzuatlarda olmayan bilgiyi uydurmamali

4. **✅ Eksik Bilgi Uyarısı**
   - Detaylı bilgi yoksa "Öğrenci İşleri'ne başvurun" demeli

---

## 🧑‍💻 Manuel Test

### Test Soruları Listesi

#### Kategori 1: Temel Bilgiler (Kolay)
```
✓ Lisans programları kaç yıldır?
  Beklenen: 4 yıl

✓ Ön lisans programları kaç yıldır?
  Beklenen: 2 yıl

✓ Seçmeli ders açılması için kaç öğrenci gerekir?
  Beklenen: En az 20 öğrenci
```

#### Kategori 2: Sınav ve Notlar (Orta)
```
✓ Bir günde en fazla kaç sınava girebilirim?
  Beklenen: 2 sınav (genel kural)

✓ Bütünleme sınavı nedir?
  Beklenen: Final'e giremeyen veya başarısız öğrenciler için

✓ Üst sınıftan ders almak için kaç ortalama gerekir?
  Beklenen: 2.50 GANO
```

#### Kategori 3: Karışık Konseptler (Zor)
```
⚠️ Lisans öğrencileri için tez savunması nasıl yapılır?
  Beklenen: "Lisans öğrencileri için tez yoktur" veya "Lisansüstü için geçerlidir"

⚠️ Türk öğrenciler için lisansa başvuru şartları neler?
  Beklenen: ÖSYM sistemi (YURT DIŞI belgelerinden bahsetmemeli!)

⚠️ Lisanstan mezun olmak için gereken not ortalaması kaç?
  Beklenen: "Mevzuatlarda açıkça belirtilmemiş, Öğrenci İşleri'ne başvurun"
```

#### Kategori 4: Meta Sorular
```
✓ Sen kimsin?
  Beklenen: SUBU Mevzuat Asistanı tanıtımı

✓ Nasıl çalışırsın?
  Beklenen: RAG sistemi açıklaması
```

---

## 📊 Sürekli İyileştirme

### 1. Test Sonuçlarını Kaydet

Her test sonrası `test_results.json` dosyası oluşturulur:

```bash
cat backend/test_results.json | jq '.[] | select(.source_match == false)'
```

Başarısız testleri görürsün.

### 2. Yeni Test Soruları Ekle

Gerçek kullanımda gördüğün sorunları `test_questions.json`'a ekle:

```json
{
  "id": 11,
  "category": "Yeni Kategori",
  "question": "Yeni soru?",
  "expected_answer": "Beklenen cevap",
  "expected_source": "İlgili yönerge"
}
```

### 3. Filtreleri İyileştir

Eğer yanlış kaynak geliyorsa, `response_generator.py`'daki filtreleri güncelle.

### 4. Prompt'u İyileştir

Eğer cevap kalitesi kötüyse, `prompts.py`'daki talimatları güncelle.

---

## 🎯 Test Sonuçlarını Yorumlama

### Başarı Kriterleri

```
✅ BAŞARILI:
- Source accuracy >= 70%
- Answer quality (GOOD) >= 70%

⚠️ DİKKAT GEREKTİRİYOR:
- Source accuracy 50-70%
- Answer quality 50-70%

❌ BAŞARISIZ:
- Source accuracy < 50%
- Answer quality < 50%
```

### Örnek Çıktı

```
==================================================
TEST SUMMARY
==================================================
Total tests: 10
Source accuracy: 9/10 (90.0%)
Answer quality (GOOD): 8/10 (80.0%)
Answer quality (PARTIAL): 1/10 (10.0%)

✓ TESTS PASSED
```

### Sorun Giderme

#### Sorun: Yanlış Kaynak Geliyor

**Örnek:** "Lisans mezuniyet" sorusu → "Diploma Düzenleme" yönergesi geliyor

**Çözüm:**
1. `response_generator.py` → `_filter_by_context()` fonksiyonunu kontrol et
2. Yeni filtreleme kuralı ekle
3. Test'i tekrar çalıştır

#### Sorun: Cevap Kalitesi Düşük

**Örnek:** Çok genel cevaplar veriyor, detay yok

**Çözüm:**
1. `prompts.py` → `USER_PROMPT_TEMPLATE` talimatlarını güncelle
2. "KAPSAMLI ve DETAYLI" ifadesini vurgula
3. Test'i tekrar çalıştır

#### Sorun: Lisans/Lisansüstü Karışıyor

**Örnek:** Lisans sorusuna lisansüstü cevabı veriyor

**Çözüm:**
1. `response_generator.py` → `_filter_by_context()` Rule 1 ve 2'yi kontrol et
2. `normalize_turkish()` fonksiyonunun doğru çalıştığını doğrula
3. Debug loglarını aç: `logger.py` → `level=logging.DEBUG`

---

## 📈 İleri Düzey: LLM-as-Judge

Daha gelişmiş bir değerlendirme için GPT-4'ü kullanarak otomatik değerlendirme yapabilirsin:

```python
def evaluate_with_llm(question, expected, actual):
    """Use GPT-4 to evaluate answer quality."""
    prompt = f"""
    Soru: {question}
    Beklenen Cevap: {expected}
    Gerçek Cevap: {actual}
    
    Gerçek cevabı 1-10 arasında puanla:
    - Doğruluk (accuracy)
    - Kapsamlılık (completeness)
    - Anlaşılırlık (clarity)
    """
    # GPT-4 API call here
    return score
```

---

## 🔄 Günlük Test Rutini

1. **Sabah:** Otomatik testi çalıştır
2. **Başarısızları analiz et:** Hangi kategorilerde sorun var?
3. **İyileştir:** Filtreleri veya prompt'u güncelle
4. **Tekrar test et:** İyileştirme çalıştı mı?
5. **Commit:** Değişiklikleri kaydet

```bash
# Günlük test rutini
cd backend
python test_accuracy.py > test_$(date +%Y%m%d).log
```

---

## 📞 Yardım

Sorun mu yaşıyorsun?
1. `test_results.json` dosyasını incele
2. Backend loglarını kontrol et (`logs/response_generator.log`)
3. Debug mode'u aç ve tekrar dene

**İyi testler! 🚀**
