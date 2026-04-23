# ExcelAI - Yapay Zeka Destekli Otomatik Excel Kayıt Uygulaması

## Proje Amacı

Excel'e veri girerken yaşanan tüm manuel süreçleri, hata kaynaklarını ve ara aşamaları ortadan kaldırarak **tamamen AI destekli, otomatik bir Excel kayıt sistemi** oluşturmak. Kullanıcı sadece ham veriyi (metin, fotoğraf, ses, belge) sağlar; sistem iş yeri tanımına göre doğru formatta, doğrulanmış ve profesyonel Excel dosyasını üretir.

**Vizyon:** Kullanıcı ile Excel arasındaki tüm "çeviri" katmanlarını kaldırmak. Fotoğrafı çek → Excel hazır. Konuş → Excel hazır. Metni yapıştır → Excel hazır.

## Proje Durumu ve Yapılanlar

### v0.1 - Temel Altyapı (Tamamlandı)
- **app.py** — Streamlit tabanlı web arayüzü (kurulum, Excel oluşturma, işlev yönetimi, geçmiş, ayarlar)
- **database.py** — SQLite ile iş yeri profili, işlevsellik tanımları ve geçmiş yönetimi
- **prompt_engine.py** — İş tanımına göre otomatik sistem promptu oluşturma
- **ai_engine.py** — OpenAI API entegrasyonu, kod üretimi, görsel analiz, güvenli kod çalıştırma
- **Çalıştırma:** `streamlit run app.py`

### v0.2 - Çoklu Model & Araç Altyapısı (Tamamlandı)
- Gemini / Claude / GPT üçlü model desteği
- Akıllı model yönlendirme
- 7 kullanıcı aracı tasarımı
- Gelişmiş prompt mühendisliği

### v0.3 - Flutter Windows Desktop Migration ✅ KODLAMA TAMAMLANDI (22-23 Nisan 2026)

- **Backend API Layer** ✅ TAMAMLANDI
  - FastAPI REST API (api_server.py - 640 satır)
  - 20+ endpoint (Config, Business, Functionalities, Tools, History, Debug)
  - CORS middleware
  - Multipart file upload desteği
  - Pydantic validation
  - Thread-safe SQLite
  - Test: Tüm endpoint'ler çalışıyor
  
- **Flutter Windows Projesi** ✅ %100 TAMAMLANDI
  - Flutter 3.41.7, Dart 3.11.5
  - Proje: `flutter_excelai` (25+ dosya, ~2860 satır)
  - Dependencies: Riverpod 2.5.1, Dio 5.4.0, file_picker 8.0.0, intl 0.19.0
  
  **Klasör Yapısı:**
  - `lib/utils/` - Constants, Theme
  - `lib/services/` - 7 servis (API client, Config, Business, Functions, Tools, History, Providers)
  - `lib/models/` - 4 model (APIConfig, BusinessProfile, Functionality, ToolResult)
  - `lib/providers/` - 4 provider (Config, Business, Functions, History)
  - `lib/pages/` - 5 sayfa (Dashboard, Tools, Functions, Settings, History)
  
  **Sayfalar (Tümü Tamamlandı):**
  - ✅ Dashboard Page - Metrics, quick actions, feature cards
  - ✅ Settings Page - API key yönetimi (load/save)
  - ✅ Functions Page - CRUD, enrich, algorithm generation
  - ✅ Tools Page - 6 araç tipi (image, pdf, voice, text, excel, form)
  - ✅ History Page - File list, download, delete
  
  **Özellikler:**
  - Material Design 3 (Streamlit renkleri)
  - Riverpod state management
  - Auto-refresh providers
  - Error/loading/empty states
  - Form validation
  - File upload/download
  - JSON preview
  - Search/filter
  
- **KALAN ADIMLAR:**
  - ⚠️ Visual Studio Desktop Development with C++ kurulumu (ZORUNLU)
  - Test ve bug fixes
  - UI/UX polish
  - Windows installer (MSIX)

## 📚 Ek Dokümantasyon

### Sorun Giderme Kılavuzları
- **[Gemini API Troubleshooting](docs/gemini-api-troubleshooting.md)** — Gemini API sorunları ve çözümleri (429, 404, timeout hataları)

---

# BÖLÜM 1: GERÇEK KULLANICI SENARYOLARI VE SORUN ANALİZİ

## Sektörel İş Akışları — "Bugün Ne Yapıyorlar?"

### Senaryo 1: Muhasebeci — Fatura & Fiş Girişi
```
Bugünkü süreç (8-12 saat/ay, 50-100 fatura):
E-posta PDF eki → Aç → Gözle oku → Excel'e yaz → Banka CSV ile karşılaştır → Hata düzelt

Bizim çözümümüz (dakikalar):
Fatura fotoğrafı/PDF yükle → AI çıkar → Doğrula → Excel hazır
```
- **Girdi:** E-posta PDF ekleri, kağıt faturalar, fiş fotoğrafları, banka CSV
- **Excel çıktı:** Tarih | Satıcı | Fatura No | Açıklama | Kategori | Tutar | KDV | Toplam | Ödeme Durumu
- **Ağrı noktası:** Her satıcının farklı fatura formatı, rakam yer değiştirme hataları, ay sonu yoğunluğu

### Senaryo 2: Depo/Stok Yöneticisi — Envanter Takibi
```
Bugünkü süreç (45-90 dk/gün):
Kağıt irsaliye → Fiziksel sayım → Vardiya sonu ofise git → Excel güncelle → E-posta at

Bizim çözümümüz:
İrsaliye fotoğrafı çek → Sesli not bırak "30 kutu X ürünü geldi" → AI güncelle → Excel hazır
```
- **Girdi:** Kağıt irsaliye, el yazısı sayım listeleri, sesli notlar
- **Excel çıktı:** SKU | Ürün | Kategori | Mevcut Stok | Giriş | Çıkış | Yeniden Sipariş | Lokasyon
- **Ağrı noktası:** Fiziksel hareket ile Excel güncelleme arasında saatlerce/günlerce gecikme, %5-15 sayım tutarsızlığı

### Senaryo 3: İK Uzmanı — Puantaj & Bordro
```
Bugünkü süreç (6-10 saat/dönem, 50 çalışan):
Çalışan puantaj gönderir (kağıt/Excel/WhatsApp) → İK toplar → Tek tek girer → Mesai hesaplar → Bordro sistemi

Bizim çözümümüz:
Puantaj fotoğrafı/mesajı yükle → AI saatleri çıkar → Mesai otomatik hesapla → Excel hazır
```
- **Girdi:** Kağıt puantajlar, WhatsApp mesajları, Excel dosyaları, kart basma CSV
- **Excel çıktı:** Sicil | Ad Soyad | Departman | Pzt-Cum Saatleri | Normal | Mesai | İzin | Toplam | Ücret
- **Ağrı noktası:** Geç gelen puantajlar (%20-30 zaman kaybı takipte), mesai hesaplama karmaşıklığı

### Senaryo 4: İnşaat — Saha Raporu
```
Bugünkü süreç (5-8 saat/hafta/proje):
Şantiyede kağıt form doldur → 2-5 gün sonra ofise getir → Admin Excel'e girsin → Maliyet hesapla

Bizim çözümümüz:
Sahadan fotoğraf + sesli rapor → AI aynı gün işle → Maliyet otomatik → Excel hazır
```
- **Girdi:** El yazısı günlük raporlar, saha fotoğrafları, sesli notlar, teslimat fişleri
- **Excel çıktı:** İşçilik Logu, Malzeme Kullanımı, İlerleme Takibi, Güvenlik Kaydı (6-10 sekme)
- **Ağrı noktası:** Okunamayan el yazısı, 2-5 gün gecikme, birden fazla projenin birleşik görünümü yok

### Senaryo 5: Küçük İşletme Sahibi — Masraf Takibi
```
Bugünkü süreç (2-4 saat/ay, 30-50 fiş):
Fiş cüzdana at → Ay sonunda masaya dök → Tek tek oku ve yaz → Kategori ata → Kredi kartıyla eşle

Bizim çözümümüz:
Fişi çek → Uygulama anında tanı → Kategori otomatik → Aylık rapor Excel hazır
```
- **Girdi:** Fiş fotoğrafları, kredi kartı CSV/PDF, e-fatura
- **Excel çıktı:** Tarih | Satıcı | Kategori | Tutar | Ödeme | Vergi İndirilebilir | Not
- **Ağrı noktası:** Fişlerin %15-25'i kaybolur, termal kağıt solar, kategori tutarsızlığı

### Senaryo 6: Satış Ekibi — Pipeline & Komisyon
- **Girdi:** Toplantı notları, kartvizit fotoğrafları, e-posta yazışmaları, CRM CSV
- **Excel çıktı:** Firma | İlgili Kişi | Görüşme | Aşama | Tahmini Değer | Kapanış Tarihi | Komisyon
- **Zaman:** Temsilci başına 5-8 saat/hafta veri girişi

### Senaryo 7: Eğitimci — Not & Yoklama
- **Girdi:** Kağıt yoklama, el yazısı not çizelgesi, sınav kağıdı fotoğrafları, LMS CSV
- **Excel çıktı:** Öğrenci | Ödev1..N | Sınav1..N | Katılım | Ağırlıklı Ort | Harf Notu
- **Zaman:** Günlük yoklama 50-90 dk, not girişi ödev başına 30-60 dk/sınıf

### Senaryo 8: Sağlık — Hasta Kaydı & Faturalama
- **Girdi:** Kağıt başvuru formları, sigorta kartı fotoğrafları, klinik notlar, EOB belgeleri
- **Excel çıktı:** Hasta ID | Ad | Tarih | Doktor | ICD-10 | CPT | Tutar | Sigorta | Talep Durumu
- **Zaman:** Günde 2-3 saat kodlama ve faturalama girişi

## İstatistiksel Özet

| Metrik | Bulgu |
|--------|-------|
| Hatalı Excel oranı | %88 (Panko araştırması) |
| Alan başına hata oranı | %1-4 |
| Veri temizleme süresi | Çalışma süresinin %30-40'ı |
| Kağıttan dijitale hız cezası | 5-10x yavaş |
| Kötü verinin ABD maliyeti | Yıllık 3+ trilyon $ |

---

# BÖLÜM 2: ÇOKLU MODEL STRATEJİSİ

## Model Profilleri

### Gemini 2.5 Flash — "Hızlı İşçi"
| Özellik | Değer |
|---------|-------|
| **Rol** | Yüksek hacimli ön işleme, hızlı çıkarma, toplu sınıflandırma |
| **Hız** | En hızlı (~2-5x diğerlerinden hızlı) |
| **Maliyet** | En düşük (~$0.15/1M input, $0.60/1M output) |
| **Bağlam Penceresi** | 1M token (en geniş) |
| **Multimodal** | Mükemmel — görsel, PDF, video, ses native desteği |
| **JSON Garantisi** | `response_schema` ile decode-time garanti |
| **Zayıf Yönler** | Derin muhakeme ve karmaşık kod üretiminde zayıf |
| **API** | `google-generativeai` Python paketi |

### Claude 4.5 Sonnet — "Uzman Mühendis"
| Özellik | Değer |
|---------|-------|
| **Rol** | Karmaşık kod üretimi, iş mantığı, Excel formülleri, kalite-kritik çıktılar |
| **Hız** | Orta |
| **Maliyet** | Orta (~$3/1M input, $15/1M output) |
| **Bağlam Penceresi** | 200K token |
| **Kod Kalitesi** | Sınıfının en iyisi — temiz, idiomatik, güvenli Python/openpyxl kodu |
| **Muhakeme** | Güçlü analitik ve çok adımlı muhakeme |
| **JSON** | Tool use ile yapılandırılmış çıktı (güvenilir ama garanti değil) |
| **Zayıf Yönler** | Gemini'den yavaş ve pahalı |
| **API** | `anthropic` Python paketi |

### GPT-5 — "Çok Yönlü Yedek"
| Özellik | Değer |
|---------|-------|
| **Rol** | Genel amaçlı yedek, güçlü talimat takibi, OpenAI ekosistem entegrasyonu |
| **Hız** | Orta |
| **Maliyet** | En yüksek |
| **Multimodal** | Mükemmel — metin, görsel, ses giriş/çıkış |
| **JSON Garantisi** | `strict: true` ile decode-time garanti |
| **Zayıf Yönler** | En pahalı seçenek, rate limiting |
| **API** | `openai` Python paketi (v1.x) |

## Akıllı Model Yönlendirme (Model Router)

Her görev en uygun modele otomatik yönlendirilir:

```
┌──────────────────────────────────────────────────────────────┐
│                      GÖREV GELDİ                             │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
              ┌────────────────────┐
              │   Görev Türü Nedir? │
              └────────┬───────────┘
                       ↓
    ┌──────────────────┼───────────────────┐
    ↓                  ↓                   ↓
┌─────────┐    ┌──────────────┐    ┌──────────────┐
│ ÇıKARMA │    │  DÖNÜŞTÜRME  │    │  KOD ÜRETİMİ │
│ (Extract)│    │ (Transform)  │    │  (Generate)  │
└────┬────┘    └──────┬───────┘    └──────┬───────┘
     ↓                ↓                   ↓
  GEMINI          Basit? ──→ GEMINI    CLAUDE
  2.5 FLASH      Karmaşık? → CLAUDE   4.5 SONNET
                  Yedek? ──→ GPT-5
```

### Yönlendirme Kuralları

| Görev | Birincil Model | Neden | Yedek |
|-------|---------------|-------|-------|
| Fotoğraf/PDF'den veri çıkarma | **Gemini Flash** | En hızlı, en ucuz, 1M token bağlam, native multimodal | GPT-5 |
| Basit sınıflandırma (kategori atama) | **Gemini Flash** | Düşük maliyet, düşük gecikme | Claude |
| Basit JSON çıkarma | **Gemini Flash** | Schema-guaranteed output, ucuz | GPT-5 |
| Karmaşık veri dönüştürme | **Claude Sonnet** | En iyi muhakeme, iş mantığı anlama | GPT-5 |
| Excel kodu üretme (openpyxl) | **Claude Sonnet** | Sınıfının en iyi kod üretici | GPT-5 |
| Formül/VBA üretimi | **Claude Sonnet** | Kod kalitesi | GPT-5 |
| Anomali tespiti | **Claude Sonnet** | Derin muhakeme | GPT-5 |
| Büyük belge işleme (>100K token) | **Gemini Flash** | 1M token bağlam penceresi | - |
| Ses transkripsiyonu | **Whisper** (OpenAI) | Özel amaçlı ses modeli | Gemini |
| Genel yedek (hata durumunda) | **GPT-5** | Farklı hata profili, güçlü fallback | - |

### Maliyet Optimizasyonu

**Hedef:** API çağrılarının ~%70-80'i Gemini Flash ile (hacim), ~%20-30'u Claude Sonnet ile (kalite), GPT-5 sadece yedek.

- **Prompt önbellekleme:** Her üç provider da tekrarlayan prefix'ler için cache destekler
- **Batch API:** Acil olmayan işler için %50 indirimli batch endpoint kullanımı
- **Kademeli işleme:** Önce ucuz model dene, başarısızlıkta pahalıya yükselt (fallback chain)
- **Token minimizasyonu:** Büyük bağlam = büyük maliyet, her zaman minimumda tut

---

# BÖLÜM 3: KULLANICI ARAÇLARI (TOOLS) TASARIMI

## Araç Felsefesi

Her araç şu prensiplere uyar:
1. **Tek sorumluluk** — Her araç bir işi iyi yapar
2. **Birleştirilebilir** — Araçlar zincirlenerek karmaşık iş akışları oluşturulabilir
3. **Önizleme → Onay → Üretim** — Kullanıcı her zaman son sözü söyler
4. **Model-agnostik** — Arka planda hangi AI çalışırsa çalışsın, kullanıcı arayüzü aynı

## 7 Temel Araç

### Araç 1: 📸 Görsel → Excel (Fotoğraftan Veri Çıkarma)
```
Kullanım: Fiş, fatura, form, tablo fotoğrafı yükle → Excel'e dönüştür
Model: Gemini 2.5 Flash (çıkarma) → Claude Sonnet (kod üretimi)
```
**Akış:**
1. Kullanıcı fotoğraf yükler (tek veya çoklu)
2. Gemini Flash görseli analiz eder, yapılandırılmış JSON çıkarır
3. JSON → Pydantic doğrulama
4. Düşük güvenli alanlar kullanıcıya gösterilir (sarı vurgu)
5. Kullanıcı onaylar/düzeltir
6. Claude Sonnet openpyxl kodu üretir
7. Excel dosyası oluşturulur

**Desteklenen görseller:**
- Fiş/makbuz fotoğrafları
- Fatura görüntüleri (her format)
- Kağıt formlar (puantaj, sipariş, kontrol listesi)
- Ekran görüntüleri (tablo içeren)
- El yazısı notlar ve listeler
- Kartvizitler

**Özel özellikler:**
- Çoklu fiş → tek Excel (toplu işleme)
- Otomatik kategori atama (iş tanımına göre)
- Bulanık/eğik fotoğraf uyarısı

### Araç 2: 📄 PDF → Excel (Belge Dönüştürme)
```
Kullanım: PDF belge yükle → Tabloları otomatik bul → Excel'e aktar
Model: Gemini 2.5 Flash (1M token ile büyük PDF desteği)
```
**Akış:**
1. PDF yüklenir (tek veya çoklu)
2. Sayfa sayfa işlenir (multimodal — taranmış PDF de desteklenir)
3. Tablolar otomatik tespit edilir
4. Her tablo ayrı bir Excel sayfasına
5. Tablo olmayan metin içeriği de yapılandırılmış olarak çıkarılabilir

**Özel özellikler:**
- Çok sayfalı PDF'lerde tablo birleştirme (sayfa atlayan tablolar)
- Banka ekstresi PDF → muhasebe Excel'e dönüşüm
- Tedarikçi fatura PDF → alım kaydı Excel

### Araç 3: 🎤 Ses → Excel (Sesli Veri Girişi)
```
Kullanım: Sesli not kaydet veya ses dosyası yükle → AI yorumla → Excel'e dönüştür
Model: Whisper (transkripsiyon) → Gemini Flash (yapılandırma) → Claude (kod)
```
**Akış:**
1. Kullanıcı mikrofon ile konuşur veya ses dosyası yükler
2. Whisper API transkript oluşturur
3. Gemini Flash transkripti iş bağlamına göre yapılandırır
4. JSON → doğrulama → kullanıcı onayı
5. Excel oluşturulur

**Kullanım örnekleri:**
- Saha mühendisi: "Bugün 3 usta 2 kalfa çalıştı, 50 torba çimento kullanıldı"
- Satıcı: "Mehmet Bey ile görüştüm, 50 bin liralık teklif verdim, haftaya dönüş yapacak"
- Depocu: "B-3 rafına 200 adet X ürünü yerleştirildi"

### Araç 4: ✏️ Metin → Excel (Serbest Metin Dönüştürme)
```
Kullanım: Herhangi bir metin yapıştır → AI yapılandır → Excel'e dönüştür
Model: Gemini Flash (basit) veya Claude Sonnet (karmaşık)
```
**Desteklenen girdiler:**
- Serbest metin açıklaması ("Dün 3 fatura kesti: A firması 5000 TL, B firması 3200 TL...")
- E-posta içeriği (kopyala-yapıştır)
- WhatsApp/mesaj metinleri
- Web sayfası tabloları (kopyala-yapıştır)
- CSV/TSV verisi
- JSON verisi

**Akıllı özellikler:**
- Otomatik format tespiti (CSV mi, serbest metin mi, tablo mu?)
- Birden fazla kaynak metinden tek Excel oluşturma
- "Bunu da ekle" desteği (mevcut Excel'e satır ekleme)

### Araç 5: 📝 Akıllı Form → Excel (Dinamik Form Oluşturucu)
```
Kullanım: İş tanımına göre otomatik oluşturulan formları doldur → Excel
Model: Claude Sonnet (form tasarımı) → Gemini Flash (doğrulama)
```
**Akış:**
1. İşlevsellik tanımından dinamik form oluşturulur
2. Alanlar otomatik doğrulama kuralları ile gelir
3. Bağımlı alanlar: ürün kodu girince açıklama + fiyat otomatik dolar
4. Toplu giriş modu: tablo formatında hızlı satır ekleme
5. Form → JSON → Excel

**Özel özellikler:**
- Otomatik tamamlama (daha önce girilen değerlerden)
- Barkod/QR kod tarama desteği
- Master veri eşleme (müşteri listesi, ürün kataloğu)

### Araç 6: 🔄 Excel → Excel (Dönüştürme & Birleştirme)
```
Kullanım: Mevcut Excel dosyalarını dönüştür, birleştir veya yeniden formatla
Model: Claude Sonnet (karmaşık dönüşüm mantığı)
```
**Kullanım senaryoları:**
- Farklı formattaki Excel'leri tek standartta birleştirme
- Bir Excel'i farklı bir şablona dönüştürme
- Banka CSV → muhasebe Excel formatı
- Birden fazla şubenin verilerini konsolide etme
- Eski format → yeni format göçü

### Araç 7: 🔍 Doğrulama & Düzeltme Aracı
```
Kullanım: Mevcut Excel'i yükle → AI analiz etsin → Hataları bul → Düzelt
Model: Claude Sonnet (anomali tespiti) → Gemini Flash (toplu doğrulama)
```
**Yapabilecekleri:**
- Format tutarsızlıkları bulma (aynı sütunda farklı tarih formatları)
- Muhtemel yazım hatalarını tespit ("İstabul" → "İstanbul")
- Sayısal anomaliler ("Bu satırda tutar diğerlerinden 100x büyük")
- Eksik alanları tespit ve öneri
- Tekrar kayıtları bulma
- Formül tutarlılık kontrolü

## Araç Birleştirme Senaryoları

```
Senaryo: Muhasebeci Ayşe'nin ay sonu rutini

1. [📸 Görsel] 47 fiş fotoğrafı toplu yükle → Tüm fişler tanınır
2. [📄 PDF] 12 fatura PDF yükle → Tablolar çıkarılır
3. [✏️ Metin] Banka ekstresini yapıştır → Hesap hareketleri çıkar
4. [🔄 Dönüştürme] Üç kaynağı birleştir → Tek muhasebe Excel'i
5. [🔍 Doğrulama] Birleşik dosyayı kontrol et → 3 anomali bulundu → Düzelt
6. → Sonuç: 8 saatlik iş 20 dakikada tamamlandı
```

---

# BÖLÜM 4: YAZILIM MÜHENDİSLİĞİ — AI İLE VERİMLİ İLETİŞİM

## Katmanlı Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUNUM KATMANI (Streamlit)                    │
│  Araç Seçimi │ Dosya Yükleme │ Önizleme │ Onay │ İndirme       │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ORKESTRASYON KATMANI                           │
│  ToolOrchestrator — araçları yönetir, adımları koordine eder    │
│  ModelRouter — her görevi en uygun modele yönlendirir            │
│  PipelineManager — çok adımlı iş akışlarını yürütür            │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI İLETİŞİM KATMANI                          │
│  PromptBuilder — model-spesifik prompt oluşturma                │
│  SchemaEnforcer — Pydantic model → JSON schema dönüşümü         │
│  ResponseParser — AI yanıtını parse etme ve doğrulama           │
│  RetryHandler — hata durumunda yedek modele geçiş               │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   MODEL ADAPTÖR KATMANI                          │
│  GeminiAdapter   │  ClaudeAdapter   │  OpenAIAdapter            │
│  (google-genai)  │  (anthropic)     │  (openai)                 │
│  Her biri kendi API'sinin yapılandırılmış çıktı mekanizmasını   │
│  kullanır: response_schema / tool_use / json_schema             │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EXCEL OLUŞTURMA KATMANI                        │
│  TemplateEngine — şablon yönetimi                               │
│  ExcelBuilder — openpyxl ile profesyonel dosya oluşturma        │
│  CodeSandbox — AI ürettiği kodu güvenli çalıştırma              │
└─────────────────────────────────────────────────────────────────┘
```

## AI İletişim Optimizasyonu

### 1. Model-Spesifik Prompt Sarmalayıcı (Wrapper)

Her AI modeli farklı prompt stilinden daha iyi sonuç alır. Çekirdek prompt aynı kalır, model-spesifik sarmalayıcı eklenir:

```
┌─────────────────────────────────────┐
│         ÇEKİRDEK PROMPT            │
│  (model-agnostik iş mantığı)       │
│  - Şema tanımı                     │
│  - İş kuralları                    │
│  - Örnek girdi/çıktı              │
└──────────────┬──────────────────────┘
               ↓
     ┌─────────┼──────────┐
     ↓         ↓          ↓
┌─────────┐ ┌────────┐ ┌────────┐
│ GEMINI  │ │ CLAUDE │ │  GPT   │
│ Wrapper │ │ Wrapper│ │ Wrapper│
│         │ │        │ │        │
│ Minimal │ │XML tag │ │System  │
│ talimat │ │yapısı  │ │msg +   │
│ "Return │ │<data>  │ │schema  │
│  JSON"  │ │</data> │ │first   │
│ yeterli │ │tercih  │ │tercih  │
└─────────┘ └────────┘ └────────┘
```

**Gemini için:** Minimum talimat en iyi sonucu verir. "Şu JSON şemasına uygun çıktı ver" yeterli.
**Claude için:** XML etiketli yapı tercih edilir. `<input_data>`, `<rules>`, `<output_format>` bölümleri.
**GPT için:** System message'da şema tanımı + katı talimatlar en iyi sonucu verir.

### 2. Yapılandırılmış Çıktı Zorlaması

Her model için native mekanizmayı kullanarak JSON uyumluluğunu garanti altına alma:

```python
# ORTAK: Pydantic şema tanımı (tek kaynak)
class FaturaVerisi(BaseModel):
    tarih: date
    satici: str
    fatura_no: str
    kalemler: list[FaturaKalemi]
    ara_toplam: Decimal
    kdv: Decimal
    toplam: Decimal

# GEMINİ: response_schema ile decode-time garanti
generation_config = {
    "response_mime_type": "application/json",
    "response_schema": FaturaVerisi  # Garanti
}

# CLAUDE: Tool use ile yapılandırılmış çıktı
tools = [{
    "name": "fatura_cikari",
    "input_schema": FaturaVerisi.model_json_schema()  # Güvenilir
}]

# GPT: Strict JSON schema
response_format = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,  # Garanti
        "schema": FaturaVerisi.model_json_schema()
    }
}
```

**Kritik ilke:** Pydantic modeli tek kaynak (single source of truth). Tüm modeller aynı şemayı kullanır. Şema değişikliği tek yerde yapılır.

### 3. Çok Adımlı Pipeline Yönetimi

Karmaşık görevleri tek devasa prompt yerine zincirleme küçük adımlara bölme:

```
ADIM 1 (Gemini Flash — ucuz, hızlı):
"Bu görseldeki tüm metni çıkar, yapılandır"
    ↓ JSON
ADIM 2 (Gemini Flash — doğrulama):
"Bu veride tutarsızlık var mı? Güven skoru ver"
    ↓ Doğrulanmış JSON + güven skorları
ADIM 3 (Claude Sonnet — karmaşık mantık, sadece gerekirse):
"Bu verileri iş kurallarına göre dönüştür, Excel kodu üret"
    ↓ Python kodu
ADIM 4 (Yerel — AI yok):
Pydantic doğrulama → Güvenlik tarama → Sandbox çalıştırma → Excel
```

**Avantaj:** Toplam maliyetin %70-80'i ucuz Gemini Flash'ta harcanır. Claude sadece gerçekten gerektiğinde devreye girer.

### 4. Hata Yönetimi ve Yedekleme (Fallback Chain)

```
Birincil model çağrısı
    ↓ Başarılı? → Devam
    ↓ Başarısız?
        ↓
Aynı modelde 1 kez retry (farklı temperature)
    ↓ Başarılı? → Devam
    ↓ Başarısız?
        ↓
Yedek modele geçiş (Gemini→GPT-5, Claude→GPT-5)
    ↓ Başarılı? → Devam
    ↓ Başarısız?
        ↓
Kullanıcıya bildirim + manuel giriş seçeneği
```

### 5. Bağlam Yönetimi

```python
class ContextManager:
    """Her AI çağrısına minimum ama yeterli bağlam sağla."""

    def build_context(self, tool, business_profile, functionality):
        return {
            "is_yeri": {  # Her zaman dahil — kim için çalışıyoruz
                "ad": business_profile.name,
                "sektor": business_profile.sector,
                "ozel_kurallar": business_profile.rules
            },
            "islev": {  # Hangi işlev için çalışıyoruz
                "ad": functionality.name,
                "sema": functionality.schema,
                "ornekler": functionality.examples[:3]  # Max 3 örnek (token tasarrufu)
            },
            "gecmis": self.get_recent_patterns(functionality.id, limit=5)
            # Son 5 başarılı dönüşümden pattern çıkar — AI tutarlılık öğrenir
        }
```

---

# BÖLÜM 5: PROMPT MÜHENDİSLİĞİ STRATEJİLERİ

## Temel İlkeler

### 1. Dört Katmanlı Prompt Yapısı

Her AI çağrısında bu yapıyı uygula:

```
KATMAN 1: ŞEA TANIMI
"Çıktın şu JSON şemasına uymalıdır: { ... }"
→ AI'ın neyi üreteceğini kesinleştir

KATMAN 2: ÖRNEK (Few-Shot)
"Örnek girdi: [fiş fotoğrafı] → Örnek çıktı: {tarih: ..., satici: ...}"
→ 2-3 tamamlanmış örnek göster

KATMAN 3: İŞ KURALLARI
"Tarihler DD.MM.YYYY formatında olmalı. KDV oranı %20. Toplam = ara_toplam + kdv"
→ Domain bilgisi ve kısıtlar

KATMAN 4: KALİTE TALİMATLARI
"Emin olmadığın alanlara [belirsiz] yaz. Her alan için güven skoru ver (0-1)."
→ Hata yönetimi ve güven metrikleri
```

### 2. Görev Tiplerine Göre Prompt Şablonları

#### A. Veri Çıkarma Promptu (Extraction)
```
Sen bir veri çıkarma uzmanısın. Verilen [kaynağı] analiz et.

<schema>
{hedef JSON şeması}
</schema>

<rules>
- Tüm metin içeriğini oku, hiçbir öğeyi atlama
- Sayısal değerleri sayı olarak döndür (string değil)
- Tarih formatı: YYYY-MM-DD
- Belirsiz değerler için: {"value": "tahmin", "confidence": 0.6}
- Bulunamayan alanlar: null
</rules>

<examples>
Girdi: [örnek görsel/metin]
Çıktı: {örnek JSON}
</examples>

Şimdi bu girdiyi işle:
[kullanıcı girdisi]
```

#### B. Kod Üretme Promptu (Generation)
```
openpyxl kütüphanesi ile Excel dosyası oluşturacak Python kodu üret.

<constraints>
- Tek fonksiyon: create_excel(data: dict, output_path: str)
- İzin verilen importlar: openpyxl, datetime, os, json, re, math
- YASAK: eval, exec, subprocess, __import__, system, popen
- 1-indexed satır/sütun (openpyxl kuralı)
- Sayfa adı max 31 karakter
- Büyük veri setleri için write_only mode
</constraints>

<style_requirements>
- Başlık satırı: kalın, koyu mavi arka plan (#1E3A5F), beyaz yazı, ortalanmış
- Veri satırları: alternatif satır renklendirme (zebra)
- Sütun genişlikleri: içeriğe göre otomatik ayarla
- Kenarlıklar: ince, gri (#CCCCCC)
- Sayısal alanlar: sağa hizalı, binlik ayırıcılı
- Para alanları: #,##0.00 ₺ formatı
- Tarih alanları: DD.MM.YYYY formatı
- Son satırda toplam/özet (varsa)
- Yazdırma ayarları: landscape, fit to page
</style_requirements>

<data_schema>
{Pydantic şeması}
</data_schema>

<sample_data>
{örnek veri}
</sample_data>

Bu veri yapısı için create_excel fonksiyonunu üret:
```

#### C. Doğrulama Promptu (Validation)
```
Aşağıdaki çıkarılmış veriyi doğrula ve skorla.

<business_context>
{iş yeri ve işlev tanımı}
</business_context>

<extracted_data>
{AI'ın çıkardığı JSON}
</extracted_data>

<validation_rules>
1. Matematiksel tutarlılık: kalemler toplamı = ara_toplam, ara_toplam + kdv = toplam
2. Format uyumu: tarihler valid mi, tutarlar pozitif mi
3. Mantıksal tutarlılık: gelecek tarihli fatura var mı, negatif miktar var mı
4. Anomali tespiti: bu iş yerinin normal aralığının dışında değer var mı
</validation_rules>

Her alan için şu formatta yanıt ver:
{
  "field": "alan_adı",
  "value": "değer",
  "status": "valid|warning|error",
  "confidence": 0.0-1.0,
  "message": "açıklama (varsa)"
}
```

### 3. Chain-of-Verification (CoVe) — Kendini Doğrulayan AI

Özellikle kritik veriler (muhasebe, bordro) için:

```
ADIM 1: Çıkar
"Bu faturadaki verileri çıkar" → JSON

ADIM 2: Bağımsız doğrulama soruları üret
AI'dan kendi çıktısını kontrol edecek sorular üretmesini iste:
"Toplam tutar gerçekten 5.430 TL mi?"
"KDV oranı %20 mi %18 mi?"
"Fatura tarihi 2025 yılında mı?"

ADIM 3: Her soruyu bağımsız yanıtla
Her soru ayrı bir AI çağrısı ile (veya aynı çağrıda ayrı bölüm olarak) doğrulanır.

ADIM 4: Tutarsızlık varsa → Düzelt ve kullanıcıya bildir
```

### 4. Güven Skoru Sistemi

Her AI çıktısında alan bazında güven skoru isteme:

```json
{
  "tarih": {"value": "2025-03-15", "confidence": 0.95},
  "satici": {"value": "Migros", "confidence": 0.99},
  "toplam": {"value": 145.50, "confidence": 0.88},
  "fatura_no": {"value": "A-12345", "confidence": 0.72}
}
```

**Eşik değerler:**
- `> 0.90` → Otomatik kabul (yeşil)
- `0.70 - 0.90` → Kullanıcıya göster, onay iste (sarı)
- `< 0.70` → Kullanıcıdan manuel giriş iste (kırmızı)

### 5. Sektörel Prompt Kütüphanesi

Her sektör için önceden optimize edilmiş prompt şablonları:

| Sektör | Prompt Varyasyonu |
|--------|-------------------|
| Muhasebe | KDV oranları (%1, %10, %20), hesap planı kodları, fatura/irsaliye ayrımı |
| İnşaat | Birim fiyat pozları, metraj hesabı, iş kalemi kodları |
| İK/Bordro | SGK prim oranları, gelir vergisi dilimleri, AGİ hesaplaması |
| Perakende | Barkod formatları, KDV grupları, stok birimi dönüşümleri |
| Sağlık | ICD-10 kodu doğrulama, SGK/özel sigorta fiyat farkları |
| Eğitim | Ağırlıklı not hesaplama, devamsızlık kuralları, başarı kriterleri |

### 6. Prompt Performans İzleme

Her prompt çağrısının metriklerini kaydet:
```python
class PromptMetrics:
    model: str              # Hangi model kullanıldı
    tool: str               # Hangi araç
    task_type: str          # extraction/generation/validation
    input_tokens: int       # Girdi token sayısı
    output_tokens: int      # Çıktı token sayısı
    latency_ms: int         # Gecikme
    cost_usd: float         # Maliyet
    success: bool           # Başarılı mı
    confidence_avg: float   # Ortalama güven skoru
    user_corrections: int   # Kullanıcı kaç alan düzeltti
```

Bu metriklerle:
- Hangi prompt hangi modelde en iyi çalışıyor → otomatik öğren
- Kullanıcı düzeltmeleri → prompt'u iyileştir
- Maliyet/kalite dengesini optimize et

---

# BÖLÜM 6: GELİŞTİRME PLANI

## Dosya Yapısı (Hedef v1.0)

```
excel/
├── CLAUDE.md                    # Proje belgelendirmesi
├── app.py                       # Streamlit ana arayüz
├── requirements.txt             # Bağımlılıklar
├── .gitignore
│
├── core/                        # Çekirdek iş mantığı
│   ├── __init__.py
│   ├── database.py              # SQLite veritabanı
│   ├── models.py                # Pydantic veri modelleri
│   └── config.py                # Uygulama konfigürasyonu
│
├── ai/                          # AI katmanı
│   ├── __init__.py
│   ├── router.py                # Model yönlendirici
│   ├── adapters/                # Model adaptörleri
│   │   ├── __init__.py
│   │   ├── base.py              # Soyut adaptör arayüzü
│   │   ├── gemini_adapter.py    # Gemini 2.5 Flash
│   │   ├── claude_adapter.py    # Claude 4.5 Sonnet
│   │   └── openai_adapter.py    # GPT-5
│   ├── prompts/                 # Prompt şablonları
│   │   ├── __init__.py
│   │   ├── extraction.py        # Veri çıkarma promptları
│   │   ├── generation.py        # Kod üretme promptları
│   │   ├── validation.py        # Doğrulama promptları
│   │   └── templates/           # Sektörel prompt şablonları
│   │       ├── accounting.py
│   │       ├── inventory.py
│   │       ├── hr_payroll.py
│   │       └── construction.py
│   └── pipeline.py              # Çok adımlı pipeline yönetimi
│
├── tools/                       # Kullanıcı araçları
│   ├── __init__.py
│   ├── base_tool.py             # Soyut araç arayüzü
│   ├── image_to_excel.py        # 📸 Görsel → Excel
│   ├── pdf_to_excel.py          # 📄 PDF → Excel
│   ├── voice_to_excel.py        # 🎤 Ses → Excel
│   ├── text_to_excel.py         # ✏️ Metin → Excel
│   ├── form_to_excel.py         # 📝 Form → Excel
│   ├── excel_transform.py       # 🔄 Excel → Excel
│   └── validator.py             # 🔍 Doğrulama & Düzeltme
│
├── excel_engine/                # Excel oluşturma motoru
│   ├── __init__.py
│   ├── builder.py               # openpyxl ile Excel oluşturma
│   ├── styles.py                # Profesyonel stil tanımları
│   ├── templates.py             # Sektörel şablon kütüphanesi
│   └── sandbox.py               # Güvenli kod çalıştırma
│
├── ui/                          # Arayüz bileşenleri
│   ├── __init__.py
│   ├── pages/                   # Streamlit sayfa modülleri
│   │   ├── setup.py             # İlk kurulum
│   │   ├── generate.py          # Ana üretim sayfası
│   │   ├── tools.py             # Araç seçim ve kullanım
│   │   ├── history.py           # Geçmiş
│   │   └── settings.py          # Ayarlar
│   └── components/              # Yeniden kullanılabilir bileşenler
│       ├── preview.py           # Veri önizleme
│       ├── confidence.py        # Güven skoru gösterimi
│       └── file_upload.py       # Dosya yükleme
│
└── outputs/                     # (gitignore) Oluşturulan dosyalar
```

## Geliştirme Fazları

### Faz 1: Çoklu Model Altyapısı (Öncelik: Kritik)
- [ ] Model adaptör arayüzü (base adapter)
- [ ] Gemini adaptör (google-generativeai)
- [ ] Claude adaptör (anthropic)
- [ ] OpenAI adaptör (openai v1.x)
- [ ] Model yönlendirici (router)
- [ ] API anahtar yönetimi (3 ayrı key)
- [ ] Fallback chain mekanizması

### Faz 2: Pydantic Veri Modelleri (Öncelik: Kritik)
- [ ] Temel veri modelleri (fatura, stok, puantaj, masraf)
- [ ] JSON schema dönüşümü (her model için)
- [ ] Doğrulama kuralları
- [ ] Güven skoru modeli

### Faz 3: Araç İmplementasyonu (Öncelik: Yüksek)
- [ ] Görsel → Excel (MVP araç)
- [ ] Metin → Excel
- [ ] PDF → Excel
- [ ] Akıllı Form
- [ ] Ses → Excel
- [ ] Excel Dönüştürme
- [ ] Doğrulama Aracı

### Faz 4: Prompt Mühendisliği (Öncelik: Yüksek)
- [ ] Çıkarma prompt şablonları
- [ ] Kod üretme prompt şablonları
- [ ] Doğrulama prompt şablonları
- [ ] Sektörel prompt kütüphanesi
- [ ] Model-spesifik sarmalayıcılar
- [ ] CoVe (Chain-of-Verification)

### Faz 5: Arayüz Yenileme (Öncelik: Orta)
- [ ] Araç seçim ekranı
- [ ] Önizleme + güven skoru gösterimi
- [ ] Toplu işleme arayüzü
- [ ] Geçmiş ve metrik dashboard

### Faz 6: İleri Özellikler (Öncelik: Düşük)
- [ ] Ses entegrasyonu (Whisper)
- [ ] Barkod/QR tarama
- [ ] Sektörel şablon kütüphanesi
- [ ] Prompt performans izleme ve otomatik optimizasyon

---

# BÖLÜM 7: VERİ AKIŞ DİYAGRAMI (DETAYLI)

```
KULLANICI
    │
    ├─── 📸 Fotoğraf yükler
    ├─── 📄 PDF yükler
    ├─── 🎤 Ses kaydeder
    ├─── ✏️ Metin yapıştırır
    ├─── 📝 Form doldurur
    ├─── 🔄 Excel yükler
    │
    ↓
┌─────────────────────────────────────────────────────┐
│              ARAÇ SEÇİCİ (ToolOrchestrator)          │
│  Girdi tipine göre otomatik araç seçimi              │
│  veya kullanıcının manuel seçimi                     │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              MODEL YÖNLENDİRİCİ (ModelRouter)        │
│                                                      │
│  Görev analizi → Karmaşıklık skoru → Model seçimi   │
│                                                      │
│  Basit çıkarma ──→ Gemini 2.5 Flash ($)             │
│  Karmaşık mantık ─→ Claude 4.5 Sonnet ($$$)         │
│  Yedek ──────────→ GPT-5 ($$$$)                     │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              PROMPT OLUŞTURUCU (PromptBuilder)       │
│                                                      │
│  İş bağlamı + Şema + Örnekler + Kurallar            │
│      ↓                                              │
│  Model-spesifik sarmalama                            │
│  (Gemini: minimal / Claude: XML / GPT: system-first)│
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              AI ÇAĞRISI + YAPILANDIRILMIŞ ÇIKTI      │
│                                                      │
│  Gemini: response_schema (garanti)                   │
│  Claude: tool_use input_schema (güvenilir)           │
│  GPT: json_schema strict:true (garanti)              │
│                                                      │
│  → Structured JSON çıktı                            │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              DOĞRULAMA (ValidationLayer)              │
│                                                      │
│  1. Pydantic şema doğrulama                         │
│  2. İş kuralları kontrolü                            │
│  3. AI anomali tespiti (opsiyonel, Claude)           │
│  4. Güven skoru hesaplama                            │
│                                                      │
│  Sonuç:                                             │
│  ✅ >0.90 güven → otomatik kabul                    │
│  ⚠️ 0.70-0.90 → kullanıcıya göster, onay iste      │
│  ❌ <0.70 → manuel düzeltme iste                    │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              ÖNİZLEME & ONAY                         │
│                                                      │
│  Tablo önizleme (Streamlit dataframe)               │
│  Güven skoru renklendirme (yeşil/sarı/kırmızı)     │
│  Düzeltme imkanı (inline edit)                      │
│  "Onayla ve Oluştur" butonu                         │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              EXCEL OLUŞTURMA                          │
│                                                      │
│  Claude Sonnet → openpyxl kodu üretir               │
│  Güvenlik taraması (yasaklı pattern kontrolü)       │
│  Sandbox'ta çalıştırma                              │
│  Profesyonel formatlama (stiller, genişlikler, vs.) │
│                                                      │
│  → .xlsx dosyası                                    │
└──────────────────────┬──────────────────────────────┘
                       ↓
                 📥 İNDİR + GEÇMİŞE KAYDET
```

---

## Teknoloji Yığını (Hedef v1.0)

| Katman | Teknoloji |
|--------|-----------|
| Frontend | Streamlit |
| AI - Hızlı İşleme | Gemini 2.5 Flash (google-generativeai) |
| AI - Kaliteli Üretim | Claude 4.5 Sonnet (anthropic) |
| AI - Yedek | GPT-5 (openai) |
| AI - Ses | Whisper (openai) |
| Veri Doğrulama | Pydantic v2 |
| Excel Üretim | openpyxl |
| Veritabanı | SQLite |
| Görsel İşleme | Pillow |
| PDF İşleme | PyMuPDF (fitz) |

---

# BÖLÜM 8: API ENTEGRASYON MİMARİSİ

api_entegrasyon.md içinde bu bölümün içeriği yer almaktadır.
---
---

# BÖLÜM 9: FLUTTER WINDOWS DESKTOP MIGRATION

**Detaylı bilgi için:** `FLUTTER_MIGRATION.md` dosyasına bakın.

## Özet

**Durum:** KODLAMA FAZI %100 TAMAMLANDI ✅  
**Başlangıç:** 22 Nisan 2026  
**Tamamlanma:** 23 Nisan 2026  
**Süre:** ~10 saat  
**İlerleme:** %88 (Visual Studio kurulumu ve test kaldı)

### Tamamlanan:
✅ **Hafta 1:** Backend API Layer (FastAPI, 20+ endpoint, 640 satır)  
✅ **Hafta 2-8:** Flutter Windows projesi (25+ dosya, ~2860 satır)
  - Models (4 dosya): APIConfig, BusinessProfile, Functionality, ToolResult
  - Services (7 dosya): API client, Config, Business, Functions, Tools, History
  - Providers (4 dosya): Config, Business, Functions, History
  - Pages (5 dosya): Dashboard, Tools, Functions, Settings, History
  - Utils: Theme, Constants

### Kalan:
⚠️ **Visual Studio Desktop Development with C++** (Windows build için ZORUNLU)  
⚠️ Test ve bug fixes  
⚠️ UI/UX polish  
⚠️ Windows installer (MSIX)

### Özellikler:
- 🎨 Material Design 3 (Streamlit color palette)
- 🔄 Riverpod state management
- 📡 Dio HTTP client (GET, POST, PUT, DELETE)
- 📁 File picker (upload/download)
- 🔍 Search/filter functionality
- ⚡ Auto-refresh providers
- ✅ Error/loading/empty states
- 📋 Form validation
- 🎯 6 tool types (image, pdf, voice, text, excel, form)

**Komutlar:**
```bash
# Backend başlat
cd C:\Users\azsxd\OneDrive\Masaüstü\ExcelAI
start_server.bat

# Flutter çalıştır (Visual Studio kurulumu sonrası)
cd C:\Users\azsxd\OneDrive\Masaüstü\flutter_excelai
C:\Users\azsxd\flutter\bin\flutter run -d windows

# Flutter build (release)
C:\Users\azsxd\flutter\bin\flutter build windows --release
# Output: build/windows/x64/runner/Release/flutter_excelai.exe
```

**Dosya Konumları:**
- Backend: `C:\Users\azsxd\OneDrive\Masaüstü\ExcelAI`
- Flutter: `C:\Users\azsxd\OneDrive\Masaüstü\flutter_excelai`
- Flutter SDK: `C:\Users\azsxd\flutter`
- Detaylı Rapor: `FLUTTER_MIGRATION.md`

**İstatistikler:**
- Yeni Kod: ~3500+ satır
- Değiştirilen: 3 satır
- Dependencies: +12 paket
- Backend Korunma: %100
