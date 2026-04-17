# ExcelAI - AI Destekli Otomatik Excel Oluşturucu

**v0.2.1** - Fonksiyonellik Odaklı Sistem

## 🎯 Proje Amacı

Excel'e veri girerken yaşanan tüm manuel süreçleri, hata kaynaklarını ve ara aşamaları ortadan kaldırarak **tamamen AI destekli, otomatik bir Excel kayıt sistemi** oluşturmak.

**Vizyon:** Kullanıcı ile Excel arasındaki tüm "çeviri" katmanlarını kaldırmak.
- Fotoğrafı çek → Excel hazır
- Konuş → Excel hazır
- Metni yapıştır → Excel hazır

---

## ✨ Özellikler

### 3 AI Modeli
- **Gemini 2.5 Flash** - Hızlı & ucuz çıkarma
- **Claude 4.5 Sonnet** - Kaliteli kod üretimi
- **GPT-5** - Çok yönlü yedek

Akıllı routing ile her görev için en uygun model otomatik seçilir.

### 6 Güçlü Araç
1. **Görsel → Excel** - Fiş, fatura, form fotoğrafları
2. **Metin → Excel** - Serbest metin, CSV, JSON, e-posta
3. **PDF → Excel** - PDF belgeler, banka ekstresi
4. **Ses → Excel** - Sesli notlar (Whisper)
5. **Excel Dönüştürme** - Format değişimi, birleştirme
6. **Doğrulama** - Hata tespiti, anomali kontrolü

### Profesyonel Çıktı
- Otomatik stil formatlaması
- Zebra şerit (alternatif satır rengi)
- Güven skoru gösterimi
- Çoklu sayfa desteği
- Sektörel şablonlar

### İş (Fonksiyonellik) Yönetimi
- Farklı Excel türlerini tanımlayın (Fatura Girişi, Stok Sayımı, vs.)
- Her iş için özel şablon ve kurallar
- AI, iş tanımına göre optimize edilmiş Excel oluşturur

---

## 🚀 Kurulum

### 1. Gerekli Paketleri Yükleyin

```bash
# Temel paketler
pip install -r requirements.txt

# AI paketleri (en az bir tanesi gerekli)
pip install google-generativeai  # Gemini için
pip install anthropic            # Claude için
pip install openai              # GPT için
```

### 2. API Anahtarları

En az bir AI provider için API key gereklidir:

**Gemini (Önerilen - Ücretsiz kotası var):**
- https://makersuite.google.com/app/apikey
- Aylık 2M token ücretsiz

**Claude (Kaliteli kod için):**
- https://console.anthropic.com/

**OpenAI (Yedek):**
- https://platform.openai.com/api-keys

### 3. Uygulamayı Başlatın

```bash
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` açılacaktır.

---

## 📖 Kullanım

### İlk Kurulum (3 Adım)

1. **Ayarlar** → En az bir API key girin → Kaydet
2. **İşler** → Bir iş tanımlayın (örn: "Fatura Girişi")
3. **Araçlar** → Excel oluşturmaya başlayın

### İş Tanımlama Örneği

```
İş Adı: Fatura Girişi
Açıklama: Müşteri faturalarını Excel'e kaydetme
Şablon: Fatura / Fiş

İş Adı: Stok Sayımı
Açıklama: Haftalık envanter sayım sonuçları
Şablon: Stok Hareketi
```

### Excel Oluşturma Akışı

1. **Araçlar** → Bir araç seçin (örn: Görsel → Excel)
2. **İş Seçimi** → Hangi iş için? (opsiyonel)
3. **Dosya Yükle** → Fotoğraf/PDF/metin yükleyin
4. **İşle** → AI verileri çıkarır
5. **Önizle & Onayla** → Kontrol edin
6. **Excel İndir** → Hazır!

---

## 📁 Proje Yapısı

```
excel/
├── app.py                     # Ana Streamlit uygulaması
├── requirements.txt           # Bağımlılıklar
├── app_data.db               # SQLite veritabanı
│
├── core/                     # Çekirdek sistem
│   ├── models.py             # Pydantic veri modelleri
│   ├── config.py             # Konfigürasyon yönetimi
│   └── database.py           # SQLite veritabanı + migration
│
├── ai/                       # AI katmanı
│   ├── adapters/             # Model adaptörleri
│   │   ├── base.py           # Soyut adaptör
│   │   ├── gemini_adapter.py # Gemini 2.5 Flash
│   │   ├── claude_adapter.py # Claude 4.5 Sonnet
│   │   └── openai_adapter.py # GPT-5
│   ├── router.py             # Akıllı model yönlendirme
│   ├── pipeline.py           # Çok adımlı iş akışları
│   └── prompts/              # Prompt şablonları
│       ├── extraction.py
│       ├── generation.py
│       └── model_wrapper.py  # Model-spesifik formatlar
│
├── tools/                    # Kullanıcı araçları
│   ├── base_tool.py          # Soyut araç arayüzü
│   ├── image_to_excel.py     # Görsel → Excel
│   ├── text_to_excel.py      # Metin → Excel
│   ├── pdf_to_excel.py       # PDF → Excel
│   ├── voice_to_excel.py     # Ses → Excel
│   ├── excel_transform.py    # Excel dönüştürme
│   └── validator.py          # Doğrulama
│
├── excel_engine/             # Excel oluşturma
│   ├── builder.py            # Ana builder
│   ├── styles.py             # Profesyonel stiller
│   └── sandbox.py            # Güvenli kod çalıştırma
│
├── ui/                       # Streamlit UI
│   └── pages/
│       ├── dashboard.py      # Ana sayfa
│       ├── functions.py      # İş yönetimi (YENİ)
│       ├── tools.py          # Araçlar
│       ├── settings.py       # Ayarlar
│       └── history.py        # Geçmiş
│
└── outputs/                  # Oluşturulan Excel dosyaları
```

---

## 🔧 Teknik Detaylar

### Veritabanı Yapısı

```sql
-- İş profili (otomatik oluşturulur)
business_profile (id, business_name, business_description, sector, is_active)

-- Kullanıcı tanımlı işler
functionalities (id, business_id, name, description, input_fields, excel_template, system_prompt)

-- İşlem geçmişi
generation_history (id, functionality_id, user_inputs, output_file, created_at)
```

### Model Routing Stratejisi

| Görev | Birincil Model | Neden | Maliyet |
|-------|---------------|-------|---------|
| Görsel çıkarma | Gemini Flash | Hızlı, ucuz, multimodal | $0.15/1M |
| Excel kodu | Claude Sonnet | En iyi kod kalitesi | $3/1M |
| Doğrulama | Claude Sonnet | Derin muhakeme | $3/1M |
| Yedek | GPT-5 | Farklı hata profili | Değişken |

### Güvenlik Özellikleri

- **Kod Sandbox:** AI ürettiği kod AST analizi ile kontrol edilir
- **Yasaklı Pattern:** eval, exec, subprocess, __import__ engellidir
- **API Key Encryption:** JSON storage (gelecekte şifreleme eklenecek)

---

## 🐛 Bilinen Sorunlar ve Çözümler

### "Model router başlatılamadı" Hatası

**Neden:** AI paketleri yüklü değil veya API key girilmemiş.

**Çözüm:**
```bash
pip install google-generativeai anthropic openai
```
Sonra Ayarlar → API key girin → Uygulamayı yeniden başlatın.

### Python 3.9 Uyarıları

**Neden:** Python 3.9.0 end-of-life geçti.

**Çözüm:** Şimdilik çalışır. İsterseniz Python 3.10+ güncelleyin.

### Schema Field Uyarısı

**Durum:** ✅ Düzeltildi (v0.2.1)
- `schema` → `data_schema` olarak değiştirildi

---

## 📝 Değişiklik Geçmişi

### v0.2.1 (2025-04-11)
- ✅ Çoklu iş yeri → Fonksiyonellik odaklı yapıya geçiş
- ✅ "İş Yerleri" → "İşler" sayfası
- ✅ Router hata yönetimi iyileştirildi
- ✅ Eksik paket uyarı sistemi eklendi
- ✅ UI'dan emoji kalabalığı temizlendi
- ✅ Database migration sistemi (is_active sütunu)
- ✅ Pydantic schema field çakışması düzeltildi
- ✅ Daha temiz ve odaklanmış UX

### v0.2.0 (2025-04)
- 🎉 İlk çoklu model desteği
- 🎉 6 araç implementasyonu
- 🎉 Profesyonel Excel çıktı motoru
- 🎉 Modüler sayfa yapısı

### v0.1.0 (2025-03)
- 🎉 Temel prototip
- 🎉 OpenAI entegrasyonu
- 🎉 Basit Excel oluşturma

---

## 🧪 Test Senaryoları

### Hızlı Test

```python
# Test metni
test_data = """
Fatura Bilgileri:
Müşteri: ABC Şirketi
Fatura No: F-2025-001
Tarih: 11.04.2025
Tutar: 5.000 TL
KDV: 1.000 TL
Toplam: 6.000 TL
"""

# Beklenen sonuç:
# Excel dosyası 6 sütunlu tablo ile oluşturulmalı
```

Daha fazla test senaryosu için `CLAUDE.md` dosyasına bakın.

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📚 Dokümantasyon

- **CLAUDE.md** - Detaylı proje dokümantasyonu ve mimari
- **CHANGELOG.md** - Sürüm geçmişi (YENİ)

---

## 📝 Lisans

Bu proje MIT lisansı altındadır.

---

## 🙏 Teşekkürler

- **Google Gemini** - Hızlı veri çıkarma
- **Anthropic Claude** - Kaliteli kod üretimi
- **OpenAI GPT** - Güvenilir yedek sistem
- **Streamlit** - Harika web framework

---

## 📞 İletişim

Sorularınız için GitHub Issues kullanın.

**v0.2.1** - Nisan 2025
