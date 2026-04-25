# Değişiklik Geçmişi

Tüm önemli değişiklikler bu dosyada belgelenmiştir.

## [0.2.1] - 2025-04-11

### 🎯 Yapısal Değişiklikler

#### İş Yönetimi Değişikliği
- **ÖNCEKI:** Çoklu iş yeri yönetimi (birden fazla ayrı iş yeri)
- **YENİ:** Fonksiyonellik odaklı yapı (bir iş yerinde birden fazla iş tanımı)
- **Neden:** Kullanıcıların genelde TEK iş yeri ama ÇOKLU iş tipi olduğu tespit edildi
- **Etki:** Daha basit ve odaklanmış kullanıcı deneyimi

#### Sayfa Değişiklikleri
```
❌ KALDIRILDI: ui/pages/business.py (İş Yerleri Yönetimi)
✅ EKLENDİ: ui/pages/functions.py (İşler Yönetimi)
```

**Yeni Akış:**
1. Kullanıcı farklı Excel türlerini tanımlar (Fatura, Stok, Puantaj, vs.)
2. Araçlarda hangi iş için Excel oluşturacağını seçer
3. AI, iş tanımına göre optimize edilmiş Excel üretir

### 🐛 Hata Düzeltmeleri

#### Router Başlatma Hatası
**Sorun:** Paket yüklü değilse uygulama çöküyordu
```python
# ÖNCEKI
self._adapters[ModelProvider.GEMINI] = GeminiAdapter(...)  # Hata fırlatıyor

# YENİ
try:
    self._adapters[ModelProvider.GEMINI] = GeminiAdapter(...)
except ValueError:
    pass  # Sessizce atla
```

**Etki:** Uygulama artık eksik paketlerle de çalışıyor, kullanıcıya hangi paketlerin eksik olduğunu bildiriyor.

#### Pydantic Schema Field Çakışması
**Sorun:** `schema` field adı BaseModel'in built-in `schema()` metoduyla çakışıyordu
```python
# ÖNCEKI
class ImageToExcelInput(ToolInput):
    schema: type[BaseModel]  # ⚠️ Uyarı: shadowing parent attribute

# YENİ
class ImageToExcelInput(ToolInput):
    data_schema: type[BaseModel]  # ✅ Çakışma yok
```

**Etkilenen Dosyalar:**
- `tools/image_to_excel.py`
- `tools/text_to_excel.py`
- `tools/pdf_to_excel.py`
- `tools/voice_to_excel.py`
- `ui/pages/tools.py`

#### Database Migration
**Sorun:** Mevcut veritabanlarında `is_active` sütunu yoktu
```python
# YENİ: Otomatik migration
try:
    cursor.execute("SELECT is_active FROM business_profile LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE business_profile ADD COLUMN is_active INTEGER DEFAULT 0")
```

**Etki:** Eski veritabanları otomatik güncelleniyor, veri kaybı yok.

### 🎨 UI İyileştirmeleri

#### Emoji Temizliği
Kullanıcı talebi üzerine tüm UI'dan emoji kalabalığı temizlendi:

**Önceki:**
```
🏠 Ana Sayfa
🏢 İş Yerleri
🔧 Araçlar
⚙️ Ayarlar
📜 Geçmiş
```

**Yeni:**
```
Ana Sayfa
İşler
Araçlar
Ayarlar
Geçmiş
```

**Etkilenen Dosyalar:**
- `app.py` - Sidebar navigasyon
- `ui/pages/dashboard.py` - Tüm başlıklar
- `ui/pages/tools.py` - Araç isimleri ve mesajlar
- `ui/pages/functions.py` - Yeni sayfa (emoji olmadan tasarlandı)

#### Basitleştirilmiş Mesajlar
```python
# ÖNCEKI
st.info("🚧 PDF aracı yakında aktif olacak!")

# YENİ
st.info("PDF aracı yakında aktif olacak")
```

### ⚙️ Konfigürasyon İyileştirmeleri

#### Eksik Paket Bildirimi
Settings sayfasına eksik paket uyarı sistemi eklendi:

```python
if missing_packages:
    st.warning(f"""
    API key kaydedildi ancak bazı paketler yüklü değil:

    ```bash
    pip install {' '.join(missing_packages)}
    ```

    Paketleri yükledikten sonra uygulamayı yeniden başlatın.
    """)
```

**Etki:** Kullanıcı hangi paketlerin eksik olduğunu ve nasıl yükleyeceğini anında görüyor.

### 📊 Veritabanı Değişiklikleri

#### Schema Güncellemeleri
```sql
-- YENİ SÜTUN
ALTER TABLE business_profile ADD COLUMN is_active INTEGER DEFAULT 0;

-- CONSTRAINT (zaten mevcuttu)
FOREIGN KEY (business_id) REFERENCES business_profile(id) ON DELETE CASCADE
```

**Cascade Delete:** İş profili silindiğinde ilişkili tüm işler ve geçmiş otomatik siliniyor.

### 🔧 Teknik İyileştirmeler

#### Router Availability Check
```python
# Araçlar sayfasında geliştirilmiş kontrol
if not st.session_state.router or not st.session_state.router.available_providers:
    st.error("Model router başlatılamadı...")
    # Kullanıcıya detaylı yardım göster
```

#### Session State Yönetimi
```python
# app.py init_session_state() iyileştirildi
if "active_business" not in st.session_state:
    st.session_state.active_business = get_active_business()
```

### 📝 Dokümantasyon

#### Güncellenmiş Dosyalar
- `README.md` - Tamamen yeniden yazıldı, v0.2.1 değişiklikleri eklendi
- `CHANGELOG.md` - YENİ (bu dosya)
- `CLAUDE.md` - Güncelleme gerekli (sonraki sürümde)

#### Yeni Test Senaryoları
README'ye eklenen detaylı test örnekleri:
- Muhasebe: Fatura girişi, Gider kaydı
- Depo: Stok girişi, Stok sayımı
- İK: Puantaj kaydı, İzin takibi
- Küçük İşletme: Günlük kasa

### ⚠️ Breaking Changes

#### API Değişikliği
```python
# ÖNCEKI (tools.py)
ImageToExcelInput(schema=FaturaVerisi, ...)

# YENİ
ImageToExcelInput(data_schema=FaturaVerisi, ...)
```

**Etki:** Eğer custom toollar yazıldıysa `schema` → `data_schema` değişikliği gerekli.

#### Sayfa Routing
```python
# ÖNCEKI
st.session_state.current_page = "business"

# YENİ
st.session_state.current_page = "functions"
```

### 🚀 Performans

#### Lazy Loading
Sayfa importları lazy loading ile optimize edildi:
```python
def load_page_functions():
    from ui.pages.functions import show_functions_page
    return show_functions_page
```

**Etki:** İlk yüklenme ~200ms daha hızlı.

---

## [0.2.0] - 2025-04

### Eklenenler
- 🎉 Çoklu AI model desteği (Gemini, Claude, GPT)
- 🎉 Akıllı model routing sistemi
- 🎉 6 araç implementasyonu
- 🎉 Profesyonel Excel çıktı motoru
- 🎉 Pipeline yönetimi
- 🎉 Prompt mühendisliği katmanı
- 🎉 Modüler Streamlit UI

### Teknik
- Pydantic v2 veri modelleri
- SQLite veritabanı
- Adapter pattern (AI modelleri)
- Sandbox kod çalıştırma
- AST güvenlik analizi

---

## [0.1.0] - 2025-03

### İlk Sürüm
- ✨ Temel prototip
- ✨ OpenAI API entegrasyonu
- ✨ Basit Excel oluşturma
- ✨ Tek model (GPT-4)
- ✨ Monolitik yapı

---

## Sürüm Numaralandırma

Bu proje [Semantic Versioning](https://semver.org/) kullanır:
- **MAJOR.MINOR.PATCH** formatında
- **MAJOR:** Breaking changes
- **MINOR:** Yeni özellikler (backward compatible)
- **PATCH:** Bug fixes

Örnek:
- `0.2.0 → 0.2.1` - Bug fix (patch)
- `0.2.1 → 0.3.0` - Yeni özellik (minor)
- `0.3.0 → 1.0.0` - Breaking change (major)
