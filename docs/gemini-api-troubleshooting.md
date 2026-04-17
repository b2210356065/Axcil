# Gemini API Sorun Giderme Kılavuzu

## Tarih: 17 Nisan 2026

Bu doküman, ExcelAI projesinde karşılaşılan Gemini API sorunlarını ve çözümlerini içerir.

---

## Sorun 1: 429 - Quota Exceeded (Gemini 2.0 Flash)

### Hata Mesajı
```
RuntimeError: Gemini API Error 429: RESOURCE_EXHAUSTED
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Model: gemini-2.0-flash
```

### Sebep
- `gemini-2.0-flash` modeli için günlük ücretsiz quota dolmuş
- Kod otomatik olarak tüm preview/experimental modelleri `gemini-2.0-flash`'a yönlendiriyordu
- Default model `gemini-3.1-flash-live-preview` idi ve bu da 2.0'a redirect ediliyordu

### Çözüm
1. **Model değişikliği:** Daha stabil ve quota'sı dolmamış modele geçiş
2. **İlk deneme:** `gemini-1.5-flash` (stabil, eski model)
3. **Nihai çözüm:** `gemini-3-flash-preview` (en yeni 3.x serisi)

---

## Sorun 2: 404 - Model Not Found (Gemini 3.1 Live Preview)

### Hata Mesajı
```
RuntimeError: Gemini API Error 404
models/gemini-3.1-flash-live-preview is not found for API version v1beta
```

### Sebep
- `gemini-3.1-flash-live-preview` modeli Google tarafından kaldırılmış veya hiç var olmamış
- Config dosyasında bu model seçiliydi

### Çözüm
1. **Mevcut modelleri listeleme:**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=API_KEY"
```

2. **Kullanılabilir modelleri tespit ettik:**
   - `gemini-3-flash-preview` ✅
   - `gemini-2.5-flash` ✅
   - `gemini-flash-latest` ✅

3. **Config güncelleme:**
```json
{
  "gemini_model": "models/gemini-3-flash-preview"
}
```

---

## Sorun 3: Read Timeout (60 saniye)

### Hata Mesajı
```
requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='generativelanguage.googleapis.com', port=443):
Read timed out. (read timeout=60)
```

### Sebep
- Gemini-3-flash-preview gibi yeni modeller daha yavaş yanıt veriyor
- Karmaşık kod üretimi 60 saniyeden fazla sürüyor
- Özellikle büyük mock data (1000 kişi) ile işlem ağır

### Çözüm

**Değişiklik yapılan dosya:** `ai/adapters/gemini_adapter.py`

Tüm API timeout değerlerini 60 saniyeden **180 saniye (3 dakika)** yükselttik:

```python
# ÖNCESİ
response = self._post_with_retry(url, json_data=request_body, timeout=60, dbg=dbg)

# SONRASI
response = self._post_with_retry(url, json_data=request_body, timeout=180, dbg=dbg)
```

**Değiştirilen yerler (5 adet):**
- Line 208: `extract()` metodu
- Line 334: `generate_code()` metodu
- Line 397: `raw_generate()` metodu
- Line 492: `validate()` metodu
- Line 589: `classify()` metodu

---

## Sorun 4: Otomatik Model Redirect Karışıklığı

### Problem
- Config'de `gemini-3.1-flash-live-preview` seçiliydi
- Kod bunu "unstable" görüp otomatik olarak `gemini-1.5-flash`'a yönlendiriyordu
- Kullanıcı ayarlarda 3.1 görüyor, ama işlem 1.5'te yapılıyordu
- Kullanıcı kafası karışıyordu: "Ben 3.1 seçtim ama neden 1.5 kullanılıyor?"

### Çözüm

**Auto-redirect mekanizmasını tamamen kaldırdık.**

**Değişiklik yapılan dosya:** `ai/adapters/gemini_adapter.py` (Line 49-61)

**ÖNCESİ:**
```python
# Kararlı model: gemini-2.0-flash. Diğer tüm deneysel/preview sürümleri yönlendir.
import re as _re
model_base = self.model_name.replace("models/", "")
is_unstable = bool(_re.search(
    r'(2\.5|3\.\d|preview|experimental|exp|live)',
    model_base, _re.IGNORECASE
))
if is_unstable:
    original_model = self.model_name
    self.model_name = "models/gemini-1.5-flash"
    print(f"[GEMINI ADAPTER] Redirecting unstable model '{original_model}' → '{self.model_name}'")
```

**SONRASI:**
```python
# OTOMATİK REDIRECT KALDIRILDI - Kullanıcı ne seçerse o kullanılır
# Model adı aynen kullanılacak, redirect yok
print(f"[GEMINI ADAPTER] Kullanılan model: {self.model_name}")
```

**Fayda:** Artık kullanıcı hangi modeli seçerse, O model kullanılıyor. Şeffaf ve tahmin edilebilir davranış.

---

## Sorun 5: Config Dosyası Geri Yazılma

### Problem
- Kod ile `.api_keys.json` dosyasını değiştiriyorduk
- Streamlit uygulaması çalışırken değişiklik yapıyorduk
- Streamlit dosyayı tekrar eski haline geri yazıyordu

### Çözüm

**DOĞRU SÜREÇ:**
1. ✅ **Önce** Streamlit uygulamasını **KAPAT** (Ctrl+C)
2. ✅ **Sonra** config dosyasını değiştir
3. ✅ **En son** uygulamayı yeniden başlat

**Uygulamanın çalışırken config değiştirmeye çalışma!**

---

## Sorun 6: Python Bytecode Cache

### Problem
- Kod değişikliği yapıldı
- Ama uygulama eski kodu kullanmaya devam etti
- Hata mesajları hala eski değerleri gösteriyordu (örn: timeout=60)

### Çözüm

**Cache temizleme komutu:**
```bash
find C:/Users/Bedirhan/Desktop/excel -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find C:/Users/Bedirhan/Desktop/excel -name "*.pyc" -delete 2>/dev/null
find C:/Users/Bedirhan/Desktop/excel -name "*.pyo" -delete 2>/dev/null
```

**Her kod değişikliğinden sonra:**
1. ✅ Cache temizle
2. ✅ Uygulamayı tamamen kapat
3. ✅ 2-3 saniye bekle
4. ✅ Yeniden başlat

---

## Nihai Konfigürasyon

### `.api_keys.json` (Son Hali)
```json
{
  "gemini_key": "AIzaSyCuJKXJzn_rJzPA9IWdUtf9A9c4B8ojdt4",
  "claude_key": "",
  "openai_key": "",
  "gemini_model": "models/gemini-3-flash-preview",
  "claude_model": "claude-sonnet-4-5",
  "openai_model": "gpt-4o",
  "confidence_high": 0.9,
  "confidence_low": 0.7
}
```

### Kod Değişiklikleri Özeti

**1. `ai/adapters/gemini_adapter.py`**
- ❌ Auto-redirect mekanizması kaldırıldı (Line 49-61)
- ✅ Timeout değerleri 60→180 saniye (5 yerde)
- ✅ Debug log eklendi: `print(f"[GEMINI ADAPTER] Kullanılan model: {self.model_name}")`

**2. `core/models.py`**
- ✅ Default model değiştirildi: `gemini-3.1-flash-live-preview` → `gemini-1.5-flash`

**3. `ui/pages/settings.py`**
- ✅ Dropdown sıralaması değiştirildi (stabil model en üstte)
- ✅ Model seçeneklerine açıklama eklendi

---

## Mevcut Gemini Modelleri (17 Nisan 2026)

### Stabil Modeller (Önerilen)
- `models/gemini-2.5-flash` - En yeni stabil
- `models/gemini-flash-latest` - Otomatik en yeni
- `models/gemini-1.5-flash` - Eski ama çok stabil

### Preview/Experimental Modeller
- `models/gemini-3-flash-preview` - 3.x serisi (şu anda kullanılan)
- `models/gemini-3.1-flash-lite-preview`
- `models/gemini-3.1-pro-preview`

### Quota Dolmuş / Kullanılamaz
- ❌ `models/gemini-2.0-flash` - Quota dolmuş (429)
- ❌ `models/gemini-3.1-flash-live-preview` - Model bulunamıyor (404)

---

## Sorun Giderme Kontrol Listesi

Gemini API hatası alıyorsan, sırayla kontrol et:

### ✅ 1. Model Seçimi
```bash
# Mevcut modeli kontrol et
cat C:/Users/Bedirhan/Desktop/excel/.api_keys.json | grep gemini_model

# Kullanılabilir modelleri listele
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=API_KEY"
```

### ✅ 2. Quota Kontrolü
- 429 hatası alıyorsan → Model değiştir veya yeni API key al
- https://ai.google.dev/gemini-api/docs/rate-limits

### ✅ 3. Timeout Kontrolü
- Timeout hatası alıyorsan → `gemini_adapter.py` dosyasında timeout değerlerini kontrol et
- Tüm timeout'lar 180 saniye olmalı

### ✅ 4. Cache Temizleme
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### ✅ 5. Uygulama Yeniden Başlatma
```bash
# Ctrl+C ile kapat
# 2-3 saniye bekle
streamlit run app.py
```

### ✅ 6. Terminal Logları
```
[GEMINI ADAPTER] Kullanılan model: models/gemini-3-flash-preview
```
Bu log doğru modeli göstermeli.

---

## Öneriler

### Kod Üretimi İçin
- **Claude kullan:** Gemini kod üretiminde zayıf, Claude çok daha iyi
- Eğer Claude key'in varsa, kod üretimi için Claude'u tercih et

### Veri Çıkarma İçin
- **Gemini kullan:** Görsel/PDF'den veri çıkarmada mükemmel
- Hızlı ve ucuz

### Timeout İyileştirme
- Mock data boyutunu küçült (1000 → 50 kişi)
- Basit kod iste (karmaşık algoritmalar yerine)
- İşlemi parçalara böl

---

## Yardımcı Komutlar

### Model Test
```python
import requests

api_key = "YOUR_API_KEY"
model = "models/gemini-3-flash-preview"
url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"

response = requests.post(url, json={
    "contents": [{"parts": [{"text": "Test"}]}]
}, timeout=180)

print(response.status_code)
print(response.text[:500])
```

### Config Hızlı Değiştirme
```bash
# Modeli değiştir (uygulama kapalıyken!)
python -c "import json; f=open('.api_keys.json','r+'); d=json.load(f); d['gemini_model']='models/gemini-3-flash-preview'; f.seek(0); f.write(json.dumps(d,indent=2)); f.truncate()"
```

---

## Sonuç

**Başarılı Çözüm:**
- ✅ Model: `gemini-3-flash-preview`
- ✅ Timeout: 180 saniye
- ✅ Auto-redirect: Kaldırıldı
- ✅ Cache: Temizlendi

**Test Edilen Senaryolar:**
- ✅ Görsel → Excel (başarılı)
- ✅ Kod üretimi (başarılı ama yavaş - Claude öneriliyor)
- ⚠️ 1000 kişilik mock data (timeout riski var, 50-100 öneriliyor)

**Geliştirme Tarihi:** 17 Nisan 2026
**Son Güncelleme:** 17 Nisan 2026
