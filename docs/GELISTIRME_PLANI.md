# ExcelAI — Geliştirme Uygulama Planı

> Bu doküman, terminali açtığınızda sırasıyla uygulayacağımız adımları içerir.
> Her adım tamamlandığında ✅ ile işaretlenecektir.

---

## GENEL BAKIŞ

```
Mevcut Durum (v0.1):
  app.py, database.py, prompt_engine.py, ai_engine.py
  → Tek model (OpenAI), temel arayüz, basit Excel üretimi

Hedef (v1.0):
  Modüler mimari, 3 AI modeli, 7 araç, sektörel şablonlar,
  güven skoru, önizleme, doğrulama katmanı
```

**Tahmini toplam adım:** 15 ana adım, her biri bağımsız çalışır hale getirilecek.

---

## ADIM 1: Proje Yapısını Oluştur
**Durum:** ⬜ Bekliyor

Mevcut düz dosya yapısını modüler klasör yapısına dönüştür.

```
excel/
├── app.py                  # Ana giriş noktası (sadece router)
├── core/
│   ├── __init__.py
│   ├── database.py         # ← mevcut database.py taşınacak
│   ├── models.py           # Pydantic veri modelleri (YENİ)
│   └── config.py           # Uygulama ayarları (YENİ)
├── ai/
│   ├── __init__.py
│   ├── router.py           # Model yönlendirici (YENİ)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py         # Soyut adaptör (YENİ)
│   │   ├── gemini.py       # Gemini adaptör (YENİ)
│   │   ├── claude.py       # Claude adaptör (YENİ)
│   │   └── openai_.py      # OpenAI adaptör (YENİ — mevcut ai_engine'dan)
│   └── prompts/
│       ├── __init__.py
│       ├── builder.py      # Prompt oluşturucu (YENİ — mevcut prompt_engine'dan)
│       ├── extraction.py   # Çıkarma promptları (YENİ)
│       ├── generation.py   # Kod üretme promptları (YENİ)
│       └── validation.py   # Doğrulama promptları (YENİ)
├── tools/
│   ├── __init__.py
│   ├── base.py             # Soyut araç arayüzü (YENİ)
│   ├── image_tool.py       # 📸 Görsel → Excel (YENİ)
│   ├── text_tool.py        # ✏️ Metin → Excel (YENİ)
│   ├── pdf_tool.py         # 📄 PDF → Excel (YENİ)
│   ├── form_tool.py        # 📝 Form → Excel (YENİ)
│   ├── voice_tool.py       # 🎤 Ses → Excel (YENİ)
│   ├── transform_tool.py   # 🔄 Excel → Excel (YENİ)
│   └── validator_tool.py   # 🔍 Doğrulama (YENİ)
├── excel_engine/
│   ├── __init__.py
│   ├── builder.py          # Excel oluşturma (YENİ)
│   ├── styles.py           # Stil tanımları (YENİ)
│   └── sandbox.py          # Güvenli kod çalıştırma (mevcut ai_engine'dan)
├── ui/
│   ├── __init__.py
│   ├── setup_page.py       # İlk kurulum sayfası
│   ├── main_page.py        # Ana araç seçim sayfası
│   ├── tool_page.py        # Araç kullanım sayfası
│   ├── settings_page.py    # Ayarlar sayfası
│   ├── history_page.py     # Geçmiş sayfası
│   └── components.py       # Ortak UI bileşenleri (önizleme, güven skoru vb.)
└── templates/              # Sektörel hazır şablonlar
    ├── __init__.py
    └── presets.py           # Fatura, stok, puantaj vb. hazır tanımlar
```

**Yapılacaklar:**
- [ ] Klasörleri oluştur
- [ ] `__init__.py` dosyalarını oluştur
- [ ] Mevcut kodları yeni konumlarına taşı (import'ları güncelle)
- [ ] `app.py`'yi sadece sayfa yönlendirme yapacak şekilde sadeleştir
- [ ] Çalıştığını doğrula: `streamlit run app.py`

---

## ADIM 2: Pydantic Veri Modelleri (core/models.py)
**Durum:** ⬜ Bekliyor

Tüm sistemin temelini oluşturacak veri şemalarını tanımla.

**Yapılacaklar:**
- [ ] `APIConfig` — 3 ayrı API key + model adları
- [ ] `BusinessProfile` — İş yeri bilgileri
- [ ] `Functionality` — İşlevsellik tanımı
- [ ] `InputField` / `ExcelColumn` / `ExcelSheet` — Şablon yapıları
- [ ] `ExtractionResult` — AI çıkarma sonucu (değer + güven skoru)
- [ ] `ValidationResult` — Doğrulama sonucu (status + mesaj)
- [ ] `PromptMetrics` — Prompt performans metrikleri
- [ ] Genel veri modelleri: `FaturaVerisi`, `StokHareketi`, `PuantajVerisi`, `MasrafKaydi`

---

## ADIM 3: Uygulama Ayarları (core/config.py)
**Durum:** ⬜ Bekliyor

API anahtarları, model tercihleri ve uygulama ayarlarını yönet.

**Yapılacaklar:**
- [ ] 3 ayrı API key saklama/yükleme (şifreli, `.api_keys.json`)
- [ ] Model tercih ayarları (hangi model hangi görev için)
- [ ] Güven skoru eşikleri (varsayılan: 0.90 / 0.70)
- [ ] Dil ayarı (TR)
- [ ] Çıktı klasörü ayarı

---

## ADIM 4: AI Adaptör Katmanı
**Durum:** ⬜ Bekliyor

Her AI sağlayıcısı için ortak arayüzü uygulayan adaptörler.

**Yapılacaklar:**
- [ ] `base.py` — `BaseAdapter` soyut sınıf:
  - `chat(system, user) → AIResponse`
  - `chat_with_image(system, user, image) → AIResponse`
  - `chat_structured(system, user, schema) → AIResponse`
  - `test_connection() → bool`
  - `estimate_cost(in_tok, out_tok) → float`
- [ ] `gemini.py` — `google-generativeai` ile Gemini 2.5 Flash
  - `response_schema` ile garantili JSON
  - Native görsel desteği
  - Pip: `google-generativeai`
- [ ] `claude.py` — `anthropic` ile Claude 4.5 Sonnet
  - Tool use ile yapılandırılmış çıktı
  - Kod üretme odaklı
  - Pip: `anthropic`
- [ ] `openai_.py` — `openai` ile GPT-5
  - `json_schema strict:true` ile garantili JSON
  - Whisper entegrasyonu (ses)
  - Pip: `openai` (zaten var)
- [ ] Her adaptörü bağımsız test et (connection test)

---

## ADIM 5: Model Yönlendirici (ai/router.py)
**Durum:** ⬜ Bekliyor

Görev türü + karmaşıklık + mevcut adaptörlere göre akıllı model seçimi.

**Yapılacaklar:**
- [ ] `ModelRouter` sınıfı
- [ ] Yönlendirme kuralları (CLAUDE.md Bölüm 2'deki tabloya göre)
- [ ] Fallback chain (birincil başarısız → yedek modele geç)
- [ ] Tek model modu (1 key varsa her şeyi o yapar)
- [ ] Maliyet takibi (hangi model ne kadar harcadı)

---

## ADIM 6: Prompt Oluşturucu (ai/prompts/)
**Durum:** ⬜ Bekliyor

Model-agnostik çekirdek prompt + model-spesifik sarmalayıcılar.

**Yapılacaklar:**
- [ ] `builder.py` — `PromptBuilder` sınıfı
  - İş bağlamı ekleme (iş yeri + işlevsellik)
  - Şema ekleme (Pydantic → JSON schema)
  - Örnek ekleme (few-shot)
  - Model-spesifik sarmalama (Gemini/Claude/GPT)
- [ ] `extraction.py` — Veri çıkarma prompt şablonları
  - Fiş/fatura çıkarma
  - Tablo çıkarma
  - Genel belge çıkarma
  - Güven skoru isteme
- [ ] `generation.py` — openpyxl kod üretme prompt şablonları
  - Stil gereksinimleri (başlık, zebra, kenarlık)
  - Güvenlik kısıtları (izin verilen import'lar)
  - Template-based generation
- [ ] `validation.py` — Doğrulama prompt şablonları
  - Matematiksel tutarlılık
  - Format kontrolü
  - Anomali tespiti

---

## ADIM 7: Excel Motoru (excel_engine/)
**Durum:** ⬜ Bekliyor

Profesyonel Excel dosyası oluşturma altyapısı.

**Yapılacaklar:**
- [ ] `styles.py` — Hazır stil seti:
  - Başlık stili (koyu mavi, beyaz yazı, kalın)
  - Zebra satır renkleri
  - Kenarlık stilleri
  - Sayı/para/tarih formatları (Türkçe locale)
- [ ] `builder.py` — `ExcelBuilder` sınıfı:
  - JSON veri → Excel dönüşümü (AI kodu olmadan, doğrudan)
  - Otomatik sütun genişliği
  - Toplam/özet satırları
  - Çoklu sayfa desteği
  - Yazdırma ayarları
- [ ] `sandbox.py` — Güvenli kod çalıştırma (mevcut koddan)
  - Yasaklı pattern kontrolü
  - İzin verilen modül listesi
  - Timeout mekanizması

---

## ADIM 8: İlk Araç — Metin → Excel (tools/text_tool.py)
**Durum:** ⬜ Bekliyor

En basit araç, tüm pipeline'ı uçtan uca test etmek için.

**Yapılacaklar:**
- [ ] `BaseTool` soyut sınıfı (tools/base.py)
- [ ] `TextToExcelTool` implementasyonu:
  1. Metin al
  2. Otomatik format algıla (CSV? JSON? serbest metin?)
  3. AI ile yapılandır (Gemini Flash veya mevcut model)
  4. Pydantic doğrulama
  5. Güven skoru hesapla
  6. Önizleme verisi oluştur
  7. Onay sonrası Excel üret
- [ ] Uçtan uca test: metin gir → Excel indir

---

## ADIM 9: Görsel → Excel Aracı (tools/image_tool.py)
**Durum:** ⬜ Bekliyor

En kritik araç — fiş/fatura fotoğrafından Excel.

**Yapılacaklar:**
- [ ] Görsel kalite kontrolü (çözünürlük, bulanıklık)
- [ ] Multimodal AI çağrısı (Gemini Flash öncelikli)
- [ ] Toplu görsel desteği (birden fazla fiş → tek Excel)
- [ ] Güven skoru ile önizleme
- [ ] Orijinal görsel + çıkarılan veri yan yana gösterim
- [ ] Kullanıcı düzeltme → Excel oluşturma

---

## ADIM 10: PDF → Excel Aracı (tools/pdf_tool.py)
**Durum:** ⬜ Bekliyor

**Yapılacaklar:**
- [ ] PDF tipi tespiti (metin tabanlı vs taranmış)
- [ ] PyMuPDF ile metin çıkarma (metin tabanlı PDF)
- [ ] Sayfa sayfa multimodal AI (taranmış PDF)
- [ ] Tablo tespiti ve çıkarma
- [ ] Çok sayfalı tablo birleştirme
- [ ] Pip: `PyMuPDF`

---

## ADIM 11: Form → Excel Aracı (tools/form_tool.py)
**Durum:** ⬜ Bekliyor

**Yapılacaklar:**
- [ ] İşlevsellik tanımından dinamik form oluşturma
- [ ] Alan tiplerine göre widget seçimi
- [ ] Toplu giriş modu (st.data_editor)
- [ ] Alan bağımlılıkları (ürün kodu → açıklama)
- [ ] Master veri desteği (Excel/CSV ile yüklenebilir lookup tabloları)

---

## ADIM 12: Ses → Excel Aracı (tools/voice_tool.py)
**Durum:** ⬜ Bekliyor

**Yapılacaklar:**
- [ ] Ses dosyası yükleme (MP3, WAV, M4A)
- [ ] Tarayıcı mikrofon kaydı (streamlit-webrtc veya audio_recorder)
- [ ] Whisper API ile transkripsiyon
- [ ] Transkript → yapılandırılmış JSON (Gemini Flash)
- [ ] Standart doğrulama → önizleme → Excel akışı
- [ ] Pip: `openai` (Whisper aynı API), `streamlit-audiorecorder`

---

## ADIM 13: Dönüştürme & Doğrulama Araçları
**Durum:** ⬜ Bekliyor

**transform_tool.py:**
- [ ] Excel yükleme ve okuma
- [ ] Format dönüştürme (eski → yeni şablon)
- [ ] Birden fazla Excel birleştirme
- [ ] Sütun eşleme (AI destekli)

**validator_tool.py:**
- [ ] Excel yükleme
- [ ] Format analizi (Gemini Flash)
- [ ] İçerik analizi (Claude Sonnet)
- [ ] Hata listesi + düzeltme önerileri
- [ ] "Otomatik Düzelt" butonu
- [ ] Düzeltilmiş Excel indirme

---

## ADIM 14: Sektörel Şablon Kütüphanesi (templates/)
**Durum:** ⬜ Bekliyor

**Yapılacaklar:**
- [ ] `presets.py` — Hazır işlevsellik şablonları:
  - Fatura / Fiş Kaydı
  - Banka Mutabakat
  - Masraf Takibi
  - Stok Giriş / Çıkış
  - Puantaj / Mesai
  - Günlük Saha Raporu
  - Satış Raporu
  - Not / Yoklama
- [ ] İlk kurulumda şablon seçimi
- [ ] Seçilen şablon → otomatik işlevsellik + prompt oluşturma

---

## ADIM 15: Arayüz Yenileme ve Son Dokunuşlar
**Durum:** ⬜ Bekliyor

**Yapılacaklar:**
- [ ] Ana sayfa: Araç seçim kartları (CLAUDE.md Bölüm 10 tasarımı)
- [ ] Önizleme ekranı: Güven skoru renklendirme + inline düzenleme
- [ ] İlk kurulum: 3 adımlı wizard (iş yeri → API keys → şablon seçimi)
- [ ] Ayarlar: 3 ayrı API key yönetimi + bağlantı testi
- [ ] Geçmiş: Filtreleme + tekrar indirme
- [ ] Dashboard: Toplam üretim, model kullanım dağılımı, maliyet özeti
- [ ] Son test: Tüm araçları uçtan uca test et

---

## UYGULAMA SIRASI ÖZETİ

```
Terminal açıldığında şu sırayla gideceğiz:

ADIM  1  → Proje yapısı (klasörler, taşıma)           ~temel
ADIM  2  → Pydantic modelleri                          ~temel
ADIM  3  → Config / API key yönetimi                   ~temel
ADIM  4  → AI adaptörleri (Gemini, Claude, GPT)        ~temel
ADIM  5  → Model yönlendirici                          ~temel
ADIM  6  → Prompt oluşturucu                           ~temel
ADIM  7  → Excel motoru                                ~temel
───────── buraya kadar altyapı hazır ─────────
ADIM  8  → Metin → Excel aracı (MVP test)              ~araç
ADIM  9  → Görsel → Excel aracı                        ~araç
ADIM 10  → PDF → Excel aracı                           ~araç
ADIM 11  → Form → Excel aracı                          ~araç
ADIM 12  → Ses → Excel aracı                           ~araç
ADIM 13  → Dönüştürme & Doğrulama araçları             ~araç
───────── buraya kadar tüm araçlar hazır ──────
ADIM 14  → Sektörel şablonlar                          ~iyileştirme
ADIM 15  → Arayüz yenileme & son dokunuşlar            ~iyileştirme
```

---

## NOTLAR

- Her adım sonunda `streamlit run app.py` ile çalıştığı doğrulanacak
- Her adım bağımsız çalışabilir tasarlanmıştır (bir adım bitmeden diğerine geçilmez)
- Adım 1-7 tamamlandığında temel altyapı hazırdır, gerisi araç eklemedir
- Öncelik sırası değiştirilebilir — kullanıcı hangi aracı isterse önce o yapılır
- API key olmadan da uygulama açılabilmeli (kurulum sayfasına yönlendirmeli)
