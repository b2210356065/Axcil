# ExcelAI - AI-Powered Excel Generation System

## Proje Amacı

Excel veri girişi süreçlerini tamamen AI destekli, otomatik bir sisteme dönüştürmek. Kullanıcı ham veri sağlar (fotoğraf, PDF, ses, metin), sistem profesyonel Excel dosyası üretir.

**Vizyon:** Fotoğrafı çek → Excel hazır. Konuş → Excel hazır. Metni yapıştır → Excel hazır.

---

## 📊 Proje Durumu

### ✅ v0.4 - Production Ready (25 Nisan 2026)

**Son Güncellemeler:**
- ✅ **Gemini 3.0 Flash** entegrasyonu tamamlandı
  - Model: `models/gemini-3-flash-preview`
  - Timeout: 180 saniye (tüm metodlar)
  - Auto-redirect kaldırıldı
  - Backend default model düzeltildi

- ✅ **Flutter UI Assets** düzenlendi
  - 6 tool görseli eklendi (SVG + PNG)
  - `assets/tools/` klasörü oluşturuldu
  - SVG desteği (`flutter_svg` paketi)
  - PNG görseller orijinal renklerle

- ✅ **Dosya Organizasyonu** temizlendi
  - Tüm MD dosyaları `docs/` klasörüne taşındı
  - Asset görselleri düzenlendi
  - Root dizin temizlendi

**Aktif Bileşenler:**
- 🟢 Backend API (FastAPI - Port 8000)
- 🟢 Flutter Windows Desktop (Debug mode)
- 🟢 SQLite Database
- 🟢 AI Router (Gemini/Claude/GPT)

---

## 🛠️ Teknoloji Stack

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Database:** SQLite3
- **AI Models:**
  - Gemini 3-Flash-Preview (hızlı çıkarma)
  - Claude 4.5 Sonnet (kod üretimi)
  - GPT-4o (yedek)
- **Excel Engine:** openpyxl

### Frontend
- **Framework:** Flutter 3.41.7 (Windows Desktop)
- **State Management:** Riverpod 2.5.1
- **HTTP Client:** Dio 5.4.0
- **UI:** Material Design 3

---

## 📁 Klasör Yapısı

```
excel/
├── CLAUDE.md                    # Proje talimatları (bu dosya)
├── README.md                    # Kullanıcı dokümantasyonu
├── .api_keys.json              # API anahtarları (git'de yok)
│
├── api_server.py               # FastAPI backend (640 satır)
├── app.py                      # Streamlit UI (eski)
│
├── core/                       # Çekirdek iş mantığı
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   └── ...
│
├── ai/                         # AI katmanı
│   ├── router.py               # Model yönlendirici
│   ├── adapters/               # Gemini, Claude, OpenAI
│   ├── prompts/                # Prompt şablonları
│   └── pipeline.py
│
├── excel_engine/               # Excel oluşturma
│   ├── builder.py
│   ├── styles.py
│   └── sandbox.py
│
├── tools/                      # Kullanıcı araçları
│   ├── image_to_excel.py
│   ├── pdf_to_excel.py
│   ├── voice_to_excel.py
│   └── ...
│
├── flutter_excelai/            # Flutter Windows Desktop
│   ├── lib/
│   │   ├── models/             # 4 model
│   │   ├── services/           # 7 servis
│   │   ├── providers/          # 4 provider
│   │   ├── pages/              # 5 sayfa
│   │   └── utils/              # Constants, Theme
│   ├── assets/tools/           # Tool görselleri (6 adet)
│   └── pubspec.yaml
│
├── docs/                       # Dokümantasyon
│   ├── gemini-api-troubleshooting.md
│   ├── FLUTTER_MIGRATION.md
│   ├── API_TEST_GUIDE.md
│   └── ...
│
└── outputs/                    # Oluşturulan Excel dosyaları
```

---

## 🚀 Çalıştırma

### Backend (FastAPI)
```bash
cd C:/Users/Bedirhan/Desktop/excel
python api_server.py
# Backend: http://127.0.0.1:8000
# Health Check: http://127.0.0.1:8000/api/health
```

### Frontend (Flutter Desktop)
```bash
cd C:/Users/Bedirhan/Desktop/excel/flutter_excelai
flutter run -d windows
```

### Streamlit (Eski Arayüz)
```bash
cd C:/Users/Bedirhan/Desktop/excel
streamlit run app.py
```

---

## 🎯 6 Kullanıcı Aracı

| Araç | Açıklama | Girdi | Görsel |
|------|----------|-------|--------|
| 📸 **Image to Excel** | Fotoğraftan veri çıkarma | Fiş, fatura, form fotoğrafı | `image.svg` |
| 📄 **PDF to Excel** | PDF'den tablo çıkarma | Fatura, rapor, ekstreleri | `pdf.png` |
| 🎤 **Voice to Excel** | Sesli not → Excel | Ses kaydı, notlar | `voice.svg` |
| ✏️ **Text to Excel** | Metin → yapılandırılmış veri | Serbest metin, e-posta | `text.png` |
| 🔄 **Excel Transform** | Excel → farklı format | Mevcut Excel dosyaları | `excel.png` |
| 📝 **Smart Form** | Dinamik form → Excel | Form doldurma | `form.svg` |

---

## 🔧 Yapılandırma

### API Anahtarları (`.api_keys.json`)
```json
{
  "gemini_key": "AIzaSy...",
  "claude_key": "",
  "openai_key": "",
  "gemini_model": "models/gemini-3-flash-preview",
  "claude_model": "claude-sonnet-4-5",
  "openai_model": "gpt-4o",
  "confidence_high": 0.9,
  "confidence_low": 0.7
}
```

### Flutter Backend URL (`lib/utils/constants.dart`)
```dart
static const String baseUrl = 'http://127.0.0.1:8000';
```

---

## 📚 Dokümantasyon

### Sorun Giderme
- **[Gemini API Troubleshooting](docs/gemini-api-troubleshooting.md)** - Gemini API hataları ve çözümleri
- **[Flutter Migration](docs/FLUTTER_MIGRATION.md)** - Flutter Windows Desktop detayları
- **[API Test Guide](docs/API_TEST_GUIDE.md)** - Backend API test senaryoları

### Geliştirme
- **[Geliştirme Planı](docs/GELISTIRME_PLANI.md)** - Roadmap ve task listesi
- **[Prompt Strategies](docs/prompt_engineering_strategies.md)** - AI prompt optimizasyonu
- **[Mimari Tasarım](docs/YENI_MIMARI_TASARIMI.md)** - Sistem mimarisi

---

## 🎨 Flutter UI Özellikleri

### Material Design 3 Theme (Streamlit Renkleri)
```dart
primary: Color(0xFF1E3A5F)      // Koyu mavi
accent: Color(0xFF00C4B4)       // Turkuaz
surface: Color(0xFFF8F9FA)      // Açık gri
error: Color(0xFFE74C3C)        // Kırmızı
warning: Color(0xFFF39C12)      // Turuncu
```

### Sayfalar
- **Dashboard** - Metrics, hızlı aksiyonlar
- **Tools** - 6 araç seçimi ve kullanım
- **Functions** - İşlevsellik yönetimi (CRUD)
- **Settings** - API key ayarları
- **History** - Oluşturulan dosyalar

### State Management
- **Riverpod Providers:**
  - `configNotifierProvider` - API config
  - `businessNotifierProvider` - İş profili
  - `functionalityNotifierProvider` - İşlevsellikler
  - `historyNotifierProvider` - Geçmiş

---

## ⚙️ Backend API Endpoints

### Config
- `GET /api/config` - Mevcut config'i getir
- `POST /api/config` - Config kaydet

### Business Profile
- `GET /api/business` - Aktif business profili
- `POST /api/business` - Business oluştur/güncelle

### Functionalities
- `GET /api/functionalities` - Tüm functionalities
- `GET /api/functionalities/{id}` - Tekil functionality
- `POST /api/functionalities` - Yeni functionality
- `PUT /api/functionalities/{id}` - Güncelle
- `DELETE /api/functionalities/{id}` - Sil
- `POST /api/functionalities/{id}/enrich` - AI zenginleştirme
- `POST /api/functionalities/{id}/generate_algo` - Algoritma üretimi

### Tools
- `POST /api/tools/process` - Tool çalıştırma (multipart)

### History
- `GET /api/history` - Geçmiş kayıtlar
- `DELETE /api/history/{id}` - Kayıt sil

### Debug
- `GET /api/debug/logs` - Debug logları
- `GET /api/health` - Health check

---

## 🔐 Güvenlik

### Code Sandbox (excel_engine/sandbox.py)
```python
# İzin verilen modüller
ALLOWED_MODULES = {
    'openpyxl', 'datetime', 'os',
    'json', 're', 'math'
}

# Yasaklı fonksiyonlar
FORBIDDEN_PATTERNS = [
    'exec', 'eval', '__import__',
    'subprocess', 'system', 'popen'
]
```

### API CORS
```python
allow_origins=["*"]  # Development
# Production: ["http://localhost:3000"]
```

---

## 🐛 Bilinen Sorunlar

### Çözüldü ✅
- ✅ Gemini 2.0 Flash quota exceeded → Gemini 3.0 Flash'a geçiş
- ✅ Timeout hataları → 180 saniye timeout
- ✅ SVG görseller görünmüyor → flutter_svg paketi eklendi
- ✅ PNG görseller renkli → Renklendirme sadece SVG'lere uygulanıyor
- ✅ text.PNG klasör dışında → assets/tools/ klasörüne taşındı

### Devam Eden
- ⚠️ Visual Studio C++ Build Tools kurulumu gerekiyor (Windows build için)
- ⚠️ Tool processing endpoint implementasyonu eksik (backend)

---

## 📝 Son Değişiklikler (25 Nisan 2026)

### Gemini 3.0 Entegrasyonu
```python
# api_server.py (Line 81)
gemini_model: str = "models/gemini-3-flash-preview"  # ✅ Düzeltildi

# ai/adapters/gemini_adapter.py
timeout=180  # ✅ 5 metodda güncellendi
```

### Flutter Assets Düzenlemesi
```yaml
# pubspec.yaml
flutter:
  assets:
    - assets/tools/

# flutter_svg paketi eklendi
dependencies:
  flutter_svg: ^2.2.4
```

### Dosya Organizasyonu
```bash
# MD dosyaları docs/ klasörüne taşındı
docs/
├── api_entegrasyon.md
├── API_TEST_GUIDE.md
├── CHANGELOG.md
├── FLUTTER_MIGRATION.md
├── gemini-api-troubleshooting.md
└── ...

# Root dizinde sadece:
├── CLAUDE.md
└── README.md
```

---

## 🎯 Sonraki Adımlar

1. **Visual Studio kurulumu** (C++ Build Tools)
2. **Tool processing** implementasyonu
3. **UI/UX polish** (animasyonlar, loading states)
4. **Windows installer** (MSIX packaging)
5. **Production deployment**

---

## 📧 İletişim & Destek

**Hata Bildirimi:** GitHub Issues
**Dokümantasyon:** `docs/` klasörü
**API Endpoint Test:** Postman collection (`docs/API_TEST_GUIDE.md`)

---

**Son Güncelleme:** 25 Nisan 2026
**Versiyon:** v0.4 (Production Ready)
**Durum:** 🟢 Aktif Geliştirme
