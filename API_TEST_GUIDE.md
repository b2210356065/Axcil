# ExcelAI API Test Rehberi

## Sunucuyu Başlatma

### Yöntem 1: Batch Script (Önerilen)
```bash
# start_server.bat dosyasına çift tıklayın
# veya cmd'den:
start_server.bat
```

### Yöntem 2: Manuel Başlatma
```bash
cd C:\Users\azsxd\OneDrive\Masaüstü\ExcelAI
pip install fastapi uvicorn python-multipart
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
```

### Başlatma Sonrası
- **API Base URL:** `http://127.0.0.1:8000`
- **API Docs (Swagger):** `http://127.0.0.1:8000/docs`
- **Alternatif Docs (ReDoc):** `http://127.0.0.1:8000/redoc`

---

## Postman ile Test Senaryoları

### 1. Health Check
**Test:** Sunucu çalışıyor mu?

```
GET http://127.0.0.1:8000/api/health
```

**Beklenen Response:**
```json
{
  "status": "healthy",
  "router_initialized": false,
  "database": "connected",
  "timestamp": "2025-04-22T10:30:00"
}
```

---

### 2. Config Kaydetme
**Test:** API anahtarlarını kaydet

```
POST http://127.0.0.1:8000/api/config
Content-Type: application/json

{
  "gemini_key": "YOUR_GEMINI_KEY_HERE",
  "claude_key": "YOUR_CLAUDE_KEY_HERE",
  "openai_key": "YOUR_OPENAI_KEY_HERE",
  "gemini_model": "models/gemini-2.0-flash-preview",
  "claude_model": "claude-sonnet-4-20250514",
  "openai_model": "gpt-4o-mini"
}
```

**Beklenen Response:**
```json
{
  "success": true,
  "message": "Config kaydedildi"
}
```

---

### 3. Config Yükleme
**Test:** Kaydedilen config'i getir

```
GET http://127.0.0.1:8000/api/config
```

**Beklenen Response:**
```json
{
  "gemini_key": "YOUR_KEY...",
  "claude_key": "YOUR_KEY...",
  "openai_key": "YOUR_KEY...",
  "gemini_model": "models/gemini-2.0-flash-preview",
  "claude_model": "claude-sonnet-4-20250514",
  "openai_model": "gpt-4o-mini",
  "confidence_high": 0.9,
  "confidence_low": 0.7,
  "available_providers": ["GEMINI", "CLAUDE", "OPENAI"]
}
```

---

### 4. Business Profile Oluşturma
**Test:** İş yeri profili oluştur

```
POST http://127.0.0.1:8000/api/business
Content-Type: application/json

{
  "business_name": "Test İşletmesi",
  "business_description": "API test için örnek işletme",
  "sector": "Test",
  "is_active": true
}
```

**Beklenen Response:**
```json
{
  "success": true,
  "business_id": 1
}
```

---

### 5. Business Profile Getirme
**Test:** Aktif business'i getir

```
GET http://127.0.0.1:8000/api/business
```

**Beklenen Response:**
```json
{
  "id": 1,
  "business_name": "Test İşletmesi",
  "business_description": "API test için örnek işletme",
  "sector": "Test",
  "is_active": true,
  "created_at": "2025-04-22 10:35:00"
}
```

---

### 6. Functionality Oluşturma
**Test:** Yeni iş tanımı oluştur

```
POST http://127.0.0.1:8000/api/functionalities
Content-Type: application/json

{
  "business_id": 1,
  "name": "Fatura Girişi",
  "description": "Fatura fotoğraflarından Excel oluşturma",
  "data_type_ids": [1, 3]
}
```

**Beklenen Response:**
```json
{
  "success": true,
  "functionality_id": 1
}
```

---

### 7. Functionalities Listeleme
**Test:** Tüm functionalities'i getir

```
GET http://127.0.0.1:8000/api/functionalities?business_id=1
```

**Beklenen Response:**
```json
[
  {
    "id": 1,
    "business_id": 1,
    "name": "Fatura Girişi",
    "description": "Fatura fotoğraflarından Excel oluşturma",
    "enriched_definition": null,
    "algorithm_path": null,
    "algorithm_version": 0,
    "data_type_ids": [1, 3]
  }
]
```

---

### 8. Functionality Enrichment
**Test:** AI ile zenginleştir

```
POST http://127.0.0.1:8000/api/functionalities/1/enrich
```

**NOT:** Bu işlem API key gerektirir ve 30-60 saniye sürebilir.

**Beklenen Response:**
```json
{
  "success": true,
  "enriched": {
    "is_ozeti": "Fatura belgelerinden...",
    "sutunlar": [...],
    "kurallari": [...],
    "sunum": {...}
  },
  "attempt_id": 1
}
```

---

### 9. Enrichment Onaylama
**Test:** Zenginleştirmeyi onayla

```
POST http://127.0.0.1:8000/api/functionalities/1/enrich/confirm
Content-Type: application/json

{
  "attempt_id": 1
}
```

---

### 10. Algorithm Generation
**Test:** Algoritma oluştur

```
POST http://127.0.0.1:8000/api/functionalities/1/generate_algo
```

**NOT:** Enrichment yapılmış olmalı. 30-90 saniye sürebilir.

**Beklenen Response:**
```json
{
  "success": true,
  "code": "def process_data(...):\n    ...",
  "version": 1,
  "test_results": {...}
}
```

---

### 11. Data Types Listeleme
**Test:** Mevcut veri tiplerini getir

```
GET http://127.0.0.1:8000/api/data_types
```

**Beklenen Response:**
```json
[
  {
    "id": 1,
    "name": "Görsel",
    "description": "Fotoğraf veya resim dosyası",
    "icon": "📸",
    "is_default": true
  },
  ...
]
```

---

### 12. History Listeleme
**Test:** Oluşturulan Excel dosyalarını getir

```
GET http://127.0.0.1:8000/api/history
```

---

### 13. Debug Logs
**Test:** AI debug loglarını getir

```
GET http://127.0.0.1:8000/api/debug/logs?limit=50&source=file
```

---

## Tarayıcı ile Test

### Swagger UI (İnteraktif)
`http://127.0.0.1:8000/docs` adresine gidin:
- Tüm endpoint'leri görebilirsiniz
- "Try it out" butonu ile direkt test edebilirsiniz
- Request/Response örneklerini görebilirsiniz

### ReDoc (Dokümantasyon)
`http://127.0.0.1:8000/redoc` adresine gidin:
- Daha temiz dokümantasyon görünümü
- Endpoint'leri kategorilere göre görüntüleyin

---

## Curl ile Test (Terminal)

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

### Config Kaydetme
```bash
curl -X POST http://127.0.0.1:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"gemini_key": "YOUR_KEY", "claude_key": "YOUR_KEY"}'
```

### Business Oluşturma
```bash
curl -X POST http://127.0.0.1:8000/api/business \
  -H "Content-Type: application/json" \
  -d '{"business_name": "Test", "business_description": "Test işletmesi", "is_active": true}'
```

---

## Beklenen Test Sonuçları

### ✅ Başarılı Senaryolar
1. Health check → `status: healthy`
2. Config save/load → API keys kaydedilir
3. Business CRUD → İşletme oluşturulur
4. Functionality CRUD → İş tanımı oluşturulur
5. Data types → 6 varsayılan tip listelenir

### ⚠️ İzin Gerektiren Senaryolar
1. Enrichment → API key gerekli, Claude Sonnet kullanır
2. Algorithm → API key + enrichment gerekli
3. Tools processing → Henüz mock, implementasyon devam ediyor

### ❌ Beklenen Hatalar
1. Router not initialized → API key girilmemiş
2. 404 Not found → İD bulunamadı
3. 422 Validation error → Request body hatalı

---

## Sonraki Adımlar

1. **Dependencies Yükle:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Sunucuyu Başlat:**
   ```bash
   start_server.bat
   ```

3. **Tarayıcıda Aç:**
   - http://127.0.0.1:8000/docs

4. **Postman Collection İçe Aktar:**
   - Swagger'dan "Export" → Postman formatı

5. **Gerçek API Keys Test:**
   - Config endpoint'e gerçek keyler gir
   - Enrichment ve Algorithm test et

---

## Bilinen Sorunlar

1. **Tools processing endpoint:** Şu anda mock response dönüyor. Gerçek implementasyon için:
   - ImageToExcelTool entegrasyonu gerekli
   - Multipart file parsing eklenmeli
   - Excel bytes → base64 encoding yapılmalı

2. **Long-running operations:** Timeout artırılmalı:
   - Enrichment: 60-90 saniye
   - Algorithm: 90-120 saniye

3. **File download:** History endpoint'ten Excel indirme henüz yok.

---

## Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
**Çözüm:**
```bash
pip install fastapi uvicorn python-multipart
```

**Problem:** `Address already in use (port 8000)`
**Çözüm:**
```bash
# Port 8000'i kullanan process'i kapat veya farklı port kullan:
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001
```

**Problem:** `Router not initialized`
**Çözüm:** Config endpoint'e API keys kaydet.

**Problem:** CORS hatası
**Çözüm:** CORS middleware zaten aktif, sorun devam ederse `allow_origins` güncelle.
