# Yeni Mimari Tasarimi: AI Algoritma Ayirma Stratejisi

## Problem

Mevcut sistemde her kullanici istegi geldiginde AI'dan hem veri cikarmasi hem de Excel olusturma kodu uretmesi isteniyor. Bu yaklasim:

1. **Tekrarlayan maliyet:** Ayni is tanimi icin her seferinde ayni Excel kodu yeniden uretiliyor
2. **Tutarsizlik riski:** AI her seferinde farkli kod uretebilir (farkli stil, farkli sutun sirasi)
3. **Buyuk veri riski:** AI kodu uretirken veriyi de isliyor — satir atlama/halusinasyon tehlikesi
4. **Gereksiz gecikme:** Kod uretimi her istekte ~5-10 saniye ekliyor

## Cozum: Uretim Zamani vs Calisma Zamani Ayirma

```
MEVCUT AKIS (her istek):
  Girdi → AI cikar → AI kod uret → Sandbox calistir → Excel

YENI AKIS:
  [Bir kez] Is tanimi → AI zenginlestir → AI algoritma uret → Kaydet
  [Her istek] Girdi → AI JSON cikar → Sabit fonksiyon(JSON, algoritma) → Excel
```

---

## BOLUM 1: IS TANIMI ZENGINLESTIRME

### 1.1 Mevcut Durum

Kullanici is tanimi olustururken sadece sunlari giriyor:
- **Ad:** "Fatura Isleme"
- **Aciklama:** "Musterilerden gelen faturalari Excel'e kaydet"
- **Veri tipleri:** [Gorsel, PDF, Metin]

Bu bilgi AI'in kaliteli Excel kodu uretmesi icin yetersiz.

### 1.2 Zenginlestirme Pipeline'i

Kullanici is tanimi kaydettikten sonra, AI bu tanimi otomatik zenginlestirir:

```
KULLANICI GIRDISI:
  Ad: "Fatura Isleme"
  Aciklama: "Musterilerden gelen faturalari Excel'e kaydet"

AI ZENGINLESTIRME PROMPTU:
  "Bu is tanimini analiz et ve detaylandir:
   - Hangi sutunlar gerekli?
   - Her sutunun veri tipi nedir?
   - Hangi dogrulama kurallari var?
   - Hangi formul/hesaplamalar gerekli?
   - Hangi siralama/gruplama mantikli?
   Sektör: {sektor}
   Mevcut veri tipleri: {veri_tipleri}"

AI CIKTISI (zenginlestirilmis tanim):
  {
    "sutunlar": [
      {"ad": "Tarih", "tip": "date", "format": "DD.MM.YYYY", "zorunlu": true},
      {"ad": "Satici", "tip": "text", "zorunlu": true},
      {"ad": "Fatura No", "tip": "text", "zorunlu": true, "benzersiz": true},
      {"ad": "Aciklama", "tip": "text", "zorunlu": false},
      {"ad": "Kategori", "tip": "select", "secenekler": ["Hammadde", "Hizmet", "Diger"]},
      {"ad": "Ara Toplam", "tip": "currency", "format": "#,##0.00 TL"},
      {"ad": "KDV Orani", "tip": "percentage", "varsayilan": 0.20},
      {"ad": "KDV", "tip": "currency", "formul": "=Ara_Toplam * KDV_Orani"},
      {"ad": "Toplam", "tip": "currency", "formul": "=Ara_Toplam + KDV"},
      {"ad": "Odeme Durumu", "tip": "select", "secenekler": ["Odendi", "Bekliyor", "Gecikti"]}
    ],
    "siralama": "Tarih ASC",
    "gruplama": null,
    "toplam_satiri": ["Ara Toplam", "KDV", "Toplam"],
    "dogrulama_kurallari": [
      "Toplam = Ara Toplam + KDV",
      "KDV Orani 0-1 arasinda olmali",
      "Tarih gelecekte olmamali"
    ]
  }
```

### 1.3 Kullanici Onay Adimi

AI zenginlestirdikten sonra kullanici sonucu gorur:
- Sutunlari ekleyebilir/cikarabilir
- Isimleri degistirebilir
- Veri tiplerini degistirebilir
- Formulleri ayarlayabilir

Onaylaninca **zenginlestirilmis tanim** veritabanina kaydedilir.

### 1.4 Veritabani Degisikligi

`functionalities` tablosuna yeni sutun:

```sql
ALTER TABLE functionalities ADD COLUMN enriched_definition TEXT DEFAULT NULL;
-- JSON formatinda zenginlestirilmis tanim
-- NULL ise henuz zenginlestirilmemis demek
```

---

## BOLUM 2: ALGORITMA URETIMI VE DEPOLAMA

### 2.1 Sabit Dosya Formati

Her is tanimi icin uretilen algoritma, standart bir Python dosyasi olarak saklanir:

```
excel/
├── algorithms/
│   ├── __init__.py
│   ├── func_1.py          # Is tanimi ID=1 icin algoritma
│   ├── func_2.py          # Is tanimi ID=2 icin algoritma
│   ├── func_3.py          # ...
│   └── _template.py       # Bos sablon (referans)
```

### 2.2 Standart Fonksiyon Imzasi

Her algoritma dosyasi **tek bir fonksiyon** icerir:

```python
# algorithms/func_{id}.py
# Otomatik uretilmis — Bu dosyayi elle degistirmeyin
# Is Tanimi: {is_adi}
# Olusturulma: {tarih}
# Model: {model_adi}

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime, date
import math

def create_excel(data: dict, output_path: str) -> None:
    """
    {is_adi} icin Excel olusturma algoritmasi.

    Args:
        data: {
            "satirlar": [
                {"Tarih": "2025-03-15", "Satici": "ABC Ltd", ...},
                {"Tarih": "2025-03-16", "Satici": "XYZ AS", ...},
            ]
        }
        output_path: Cikti dosya yolu (.xlsx)
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "{is_adi}"[:31]

    # ... stil tanimlari (mevcut generation.py sablonundaki gibi) ...
    # ... baslik satiri ...
    # ... veri satirlari (data["satirlar"] uzerinde dongu) ...
    # ... formul satirlari ...
    # ... otomatik genislik ...
    # ... yazdirma ayarlari ...

    wb.save(output_path)
```

**Kritik kural:** Fonksiyon `data["satirlar"]` listesini alir ve bu listeyi **oldugu gibi** Excel'e yazar. AI'in veriyle hicbir islemi yoktur — sadece format/stil/formul uygular.

### 2.3 Algoritma Uretim Promptu

Zenginlestirilmis tanim kullanilarak AI'dan algoritma uretmesi istenir:

```
SEN BIR PYTHON EXCEL OTOMASYON UZMANISIN.

Asagidaki is tanimi icin openpyxl ile create_excel fonksiyonu uret.

<is_tanimi>
{zenginlestirilmis_tanim_json}
</is_tanimi>

<zorunlu_kurallar>
1. Fonksiyon imzasi: create_excel(data: dict, output_path: str) -> None
2. data["satirlar"] bir liste — her eleman bir satir dict'i
3. Sutun isimleri ve siralamasi: {sutun_listesi}
4. VERI UZERINDE HICBIR ISLEM YAPMA — sadece yaz
5. Formul sutunlari: Excel formullerini kullan (Python hesaplama degil)
   Ornek: KDV = "=F{row}*G{row}" seklinde formul yaz
6. data["satirlar"] bos olabilir — bos durumda sadece baslik satiri yaz
</zorunlu_kurallar>

<stil_gereksinimleri>
{mevcut generation.py'deki stil sablonu — header, zebra, border, vs.}
</stil_gereksinimleri>

<izin_verilen_importlar>
openpyxl (tum alt modulleri), datetime, os.path, json, re, math, decimal
</izin_verilen_importlar>

<yasakli_patternler>
eval, exec, compile, subprocess, os.system, __import__, open (save haric)
</yasakli_patternler>

SADECE create_excel fonksiyonunu uret. Aciklama ekleme.
```

### 2.4 Guvenlik Taramasi ve Kayit

AI kodu urettikten sonra:

```python
# 1. CodeSandbox ile guvenlik taramasi
from excel_engine.sandbox import CodeSandbox

is_safe, error = CodeSandbox.validate_code(generated_code)
if not is_safe:
    # Yeniden uret veya kullaniciya bildir
    raise SecurityViolation(error)

# 2. Test calistirma (bos veri ile)
CodeSandbox.execute_safe(
    code=generated_code,
    function_name="create_excel",
    kwargs={
        "data": {"satirlar": []},  # Bos test
        "output_path": temp_path
    }
)

# 3. Dosyaya kaydet
algorithm_path = f"algorithms/func_{func_id}.py"
with open(algorithm_path, "w", encoding="utf-8") as f:
    f.write(generated_code)

# 4. Veritabanina path kaydet
# functionalities tablosuna:
# ALTER TABLE functionalities ADD COLUMN algorithm_path TEXT DEFAULT NULL;
```

### 2.5 Algoritma Guncelleme

Is tanimi degistirildiginde:
1. Zenginlestirilmis tanim yeniden olusturulur (kullanici onayiyla)
2. Yeni algoritma uretilir
3. Eski algoritma yedeklenir: `func_{id}_v1.py` → `func_{id}_v2.py`
4. Yeni algoritma `func_{id}.py` olarak kaydedilir

---

## BOLUM 3: CALISMA ZAMANI AKISI

### 3.1 Girdi → JSON Cikarma (AI)

Kullanici herhangi bir veri tipiyle girdi sagladiginda, AI SADECE JSON cikarir:

```
AI PROMPTU:
  "Asagidaki {girdi_tipi}'den verileri cikar.
   Sutunlar: {zenginlestirilmis_tanimdaki_sutun_listesi}

   CIKTI FORMATI:
   {
     "satirlar": [
       {"Tarih": "2025-03-15", "Satici": "...", ...},
       ...
     ]
   }

   KURALLAR:
   - Tum satirlari cikar, hicbirini atlama
   - Sutun isimlerini AYNEN kullan (buyuk/kucuk harf dahil)
   - Sayilari sayi olarak dondur
   - Tarihler: YYYY-MM-DD
   - Bos/belirsiz alanlar: null"
```

**Onemli:** Bu adimda AI HIC Excel kodu uretmez. Sadece yapilandirilmis JSON cikarir. Bu, mevcut key verification sistemiyle birlikte calisir.

### 3.2 Sabit Calistirma Fonksiyonu

Yeni bir "runner" fonksiyonu tum akisi yonetir:

```python
# core/algorithm_runner.py

import importlib.util
import os
from excel_engine.sandbox import CodeSandbox

def run_algorithm(func_id: int, data: dict, output_path: str) -> str:
    """
    Is tanimi icin kayitli algortimayi calistir.

    Args:
        func_id: Is tanimi ID'si
        data: {"satirlar": [...]} formatinda veri
        output_path: Excel cikti yolu

    Returns:
        Olusturulan dosya yolu
    """
    algorithm_path = f"algorithms/func_{func_id}.py"

    if not os.path.exists(algorithm_path):
        raise FileNotFoundError(
            f"Algoritma dosyasi bulunamadi: {algorithm_path}. "
            f"Is tanimini yeniden kaydedin."
        )

    # Algoritma kodunu oku
    with open(algorithm_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Guvenlik kontrolu (her calistirmada — dosya disaridan degistirilmis olabilir)
    is_safe, error = CodeSandbox.validate_code(code)
    if not is_safe:
        raise SecurityViolation(f"Algoritma guvenlik kontrolunden gecemedi: {error}")

    # Sandbox icinde calistir
    CodeSandbox.execute_safe(
        code=code,
        function_name="create_excel",
        kwargs={"data": data, "output_path": output_path}
    )

    return output_path
```

### 3.3 Tam Akis Diyagrami

```
KULLANICI GIRDISI (foto/PDF/metin/ses/form/Excel)
    │
    ↓
┌────────────────────────────────────────────┐
│  ADIM 1: ANAHTAR CIKARMA (mevcut sistem)   │
│  AI girdiyi analiz eder                     │
│  key_column ve key_values listesi cikarir   │
└──────────────────┬─────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│  ADIM 2: VERI CIKARMA (AI — sadece JSON)   │
│  Zenginlestirilmis tanimdaki sutunlara      │
│  gore yapilandirilmis JSON cikarir          │
│  {"satirlar": [...]}                        │
└──────────────────┬─────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│  ADIM 3: KEY DOGRULAMA (programatik)       │
│  Cikartilan key_values vs JSON satirlari   │
│  Eksik satirlar varsa → isaretle           │
└──────────────────┬─────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│  ADIM 4: ONIZLEME & ONAY                  │
│  Kullanici tabloyu gorur                    │
│  Dusuk guvenli alanlar sari                 │
│  Onaylar veya duzeltir                      │
└──────────────────┬─────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│  ADIM 5: ALGORITMA CALISTIR               │
│  run_algorithm(func_id, data, output_path) │
│  Kayitli create_excel kodu Sandbox'ta      │
│  calistirilir                               │
│  AI BU ADIMDA HIC DEVREYE GIRMEZ          │
└──────────────────┬─────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│  ADIM 6: SONUC                             │
│  Excel dosyasi hazir → indirme butonu       │
│  Eksik key'ler varsa → uyari satirlari      │
│  Gecmise kaydet                             │
└────────────────────────────────────────────┘
```

---

## BOLUM 4: CRUD ISLEMLERI

### 4.1 Ekleme (Append) — Degisiklik Yok

Mevcut algoritmik append sistemi aynen kalir:
- AI yeni satirlari JSON olarak cikarir
- `_append_to_excel()` mevcut dosyaya satirlari ekler
- AI Excel dosyasina dokunmaz

### 4.2 Silme (Delete) — Degisiklik Yok

Mevcut algoritmik silme sistemi aynen kalir:
- AI `DeleteInstruction` (key_column + delete_keys) cikarir
- `_delete_from_excel()` programatik olarak satirlari siler
- AI Excel dosyasina dokunmaz

### 4.3 Duzenleme (Edit) — Degisiklik Yok

Mevcut algoritmik duzenleme sistemi aynen kalir:
- AI `EditInstruction` (key_column + edits) cikarir
- `_edit_excel()` programatik olarak hucreleri gunceller
- AI Excel dosyasina dokunmaz

### 4.4 Yeniden Duzenleme (Reorganize) — Yeni Pipeline

Mevcut sistemde reorganize icin AI'dan tam Excel kodu uretiliyor. Yeni mimariyle:

```
REORGANIZE AKISI:
1. Mevcut Excel okunur → JSON'a donusturulur
2. AI'ya JSON + yeni duzenleme talimati gonderilir
3. AI donusturulmus JSON dondurur (sirali/gruplanmis/duzenlenmis)
4. Key dogrulama yapilir (tum satirlar korunmus mu?)
5. Kayitli algoritma yeni JSON ile calistirilir → Yeni Excel

AVANTAJ:
- AI veriyi isleme alir ama Excel olusturma sorumlulugu yok
- Veri kaybi key dogrulama ile yakalanir
- Format tutarliligi garanti (hep ayni algoritma)
```

**Reorganize AI Promptu:**

```
Asagidaki Excel verilerini yeniden duzenle.

<mevcut_veri>
{json_satirlar}
</mevcut_veri>

<talimat>
{kullanici_talimati — "tarihe gore sirala", "kategoriye gore grupla", vs.}
</talimat>

<anahtar_bilgisi>
Anahtar sutun: {key_column}
Mevcut anahtar degerleri (HEPSINI KORU): {key_values_listesi}
</anahtar_bilgisi>

<kurallar>
- TUM satirlari dondur, HICBIRINI silme
- Sadece siralama/gruplama/format degistir
- Yeni satir EKLEME
- Veri degerleri DEGISTIRME (sadece siralamayi degistir)
- Ayni JSON formatinda dondur: {"satirlar": [...]}
</kurallar>

KENDINI DOGRULA:
Ciktindaki satirlari say ve girdi satirlariyla karsilastir.
Satir sayisi: {beklenen_satir_sayisi}
Eksik anahtar var mi? Varsa listeye ekle.
```

---

## BOLUM 5: VERITABANI DEGISIKLIKLERI

```sql
-- 1. Zenginlestirilmis tanim (JSON)
ALTER TABLE functionalities ADD COLUMN enriched_definition TEXT DEFAULT NULL;

-- 2. Algoritma dosya yolu
ALTER TABLE functionalities ADD COLUMN algorithm_path TEXT DEFAULT NULL;

-- 3. Algoritma versiyonu (guncelleme takibi)
ALTER TABLE functionalities ADD COLUMN algorithm_version INTEGER DEFAULT 0;

-- 4. Son algoritma uretim tarihi
ALTER TABLE functionalities ADD COLUMN algorithm_generated_at TEXT DEFAULT NULL;
```

### Migration Stratejisi

Mevcut is tanimlari icin `enriched_definition` ve `algorithm_path` NULL olacak. Bu durumda:
- Eski akis devam eder (AI her seferinde kod uretir)
- Kullanici is tanimini duzenlediginde "Algoritmaya Donustur" butonu gosterilir
- Butona basilinca zenginlestirme + algoritma uretimi yapilir

Bu sayede geriye uyumluluk korunur.

---

## BOLUM 6: AVANTAJLAR VE RISKLER

### Avantajlar

| Avantaj | Aciklama |
|---------|----------|
| **Maliyet azalma** | Her istekte kod uretimi yok — AI sadece JSON cikarir (Gemini Flash yeterli, Claude gerekmez) |
| **Hiz artisi** | Kod uretimi + guvenlik taramasi adimi atlanir (~5-10 sn tasarruf) |
| **Tutarlilik** | Her seferinde ayni Excel formati (ayni stiller, ayni sutun sirasi) |
| **Guvenlik** | Algoritma bir kez taranir ve kaydedilir — her calistirmada tekrar taranir ama kod degismez |
| **Veri guvenligi** | AI ASLA Excel koduna dokunmaz — sadece JSON cikarir. Veri kaybi riski minimuma iner |
| **Olceklenebilirlik** | 1000 satirlik veri geldiginde AI 1000 satirlik kod uretmek zorunda kalmaz |
| **Debug kolayligi** | Algoritma dosyasi okunabilir, test edilebilir, gerekirse elle duzeltebilir |

### Riskler ve Cozumler

| Risk | Cozum |
|------|-------|
| AI kotu algoritma uretirse | Bos veri ile test calistir + kullanici onizleme + versiyon yedekleme |
| Is tanimi degisirse algoritma uyumsuz kalir | Tanim degisikliginde otomatik yeniden uretim teklif et |
| Algoritma dosyasi silinirse/bozulursa | Veritabaninda yedek kod saklama + otomatik yeniden uretim |
| Zenginlestirme yanlissa | Kullanici onay adimi — her sutunu gorup duzeltebilir |
| Farkli girdi formatlari (foto vs metin) | AI JSON cikarma bu farki yonetir — algoritma her zaman ayni JSON alir |

---

## BOLUM 7: UYGULAMA SIRASI

### Faz 1: Veritabani ve Altyapi
1. `functionalities` tablosuna yeni sutunlar ekle (migration)
2. `algorithms/` dizini olustur
3. `core/algorithm_runner.py` dosyasi olustur (run_algorithm fonksiyonu)

### Faz 2: Zenginlestirme Pipeline'i
4. Zenginlestirme promptu olustur
5. `functions.py` sayfasina "Zenginlestir" butonu ekle
6. Zenginlestirilmis tanimi onizleme + duzenleme arayuzu
7. Onaylanan tanimi veritabanina kaydet

### Faz 3: Algoritma Uretimi
8. Algoritma uretim promptu olustur (generation.py'yi referans al)
9. Uretilen kodu CodeSandbox ile dogrula
10. Bos veri ile test calistir
11. `algorithms/func_{id}.py` olarak kaydet

### Faz 4: Calisma Zamani Entegrasyonu
12. `tools.py`'de "Olustur" akisini degistir:
    - Algoritma varsa → run_algorithm kullan
    - Algoritma yoksa → eski akis (AI kod uretimi)
13. Reorganize akisini yeni pipeline'a gecir
14. Key dogrulama sistemini entegre et

### Faz 5: Kullanici Deneyimi
15. Is tanimi listesinde algoritma durumu goster (var/yok/eski)
16. "Algoritmaya Donustur" butonu
17. Algoritma onizleme (uretilen kodu gosterme — ileri kullanici icin)
18. Hata durumlarinda bilgilendirme mesajlari

---

## BOLUM 8: ORNEK SENARYO — UCTAN UCA

### Senaryo: Muhasebeci Ayse "Fatura Isleme" tanimi olusturuyor

**ADIM 1: Is Tanimi Olusturma**
```
Ad: Fatura Isleme
Aciklama: Tedarikci faturalarini Excel'e kaydet
Veri Tipleri: [Gorsel, PDF, Metin]
→ [Kaydet]
```

**ADIM 2: AI Zenginlestirme (otomatik)**
```
AI analiz eder ve oneriler sunar:
- Sutunlar: Tarih, Satici, Fatura No, Aciklama, Kategori, Ara Toplam, KDV Orani, KDV, Toplam, Odeme Durumu
- Formul: KDV = Ara Toplam × KDV Orani, Toplam = Ara Toplam + KDV
- Toplam satiri: Ara Toplam, KDV, Toplam icin SUM
- Siralama: Tarih ASC
→ Ayse gozden gecirir, "Fatura No"yu "Belge No" olarak degistirir
→ [Onayla]
```

**ADIM 3: Algoritma Uretimi (otomatik)**
```
AI create_excel fonksiyonu uretir:
- 10 sutunlu baslik
- Zebra sitil, mavi baslik
- KDV ve Toplam icin Excel formuleri
- SUM toplam satiri
- Otomatik genislik
→ CodeSandbox taramasindan gecer
→ Bos veri ile test basarili
→ algorithms/func_7.py olarak kaydedilir
```

**ADIM 4: Ilk Kullanim — Fatura Fotografindan**
```
Ayse bir fatura fotografini yukler:
1. Gemini Flash fotografi analiz eder
2. JSON cikarir: {"satirlar": [{"Tarih": "2025-03-15", "Satici": "ABC Ltd", ...}]}
3. Key dogrulama: Belge No = "F-2025-001" ✓
4. Onizleme gosterilir — Ayse onaylar
5. run_algorithm(7, data, "fatura.xlsx") calistirilir
6. Excel hazir — indir
```

**ADIM 5: Ikinci Kullanim — PDF Fatura**
```
Ayse bir PDF yukler:
1. Gemini Flash PDF'i analiz eder
2. AYNI JSON formatinda cikarir: {"satirlar": [...]}
3. AYNI algoritma calisir → AYNI Excel formati
4. Tutarli sonuc — her seferinde ayni gorunum
```

**ADIM 6: Toplu Ekleme**
```
Ayse 5 fis fotografini toplu yukler:
1. Her fis icin JSON cikarilir
2. Tum satirlar birlesitirilir
3. Mevcut Excel'e _append_to_excel ile eklenir (algoritmik)
4. Veya yeni Excel icin run_algorithm cagrilir
```

---

## BOLUM 9: DATA["SATIRLAR"] STANDART YAPISI

Tum sistem bu standart JSON yapisini kullanir:

```json
{
  "satirlar": [
    {
      "Tarih": "2025-03-15",
      "Satici": "ABC Ltd Sti",
      "Belge No": "F-2025-001",
      "Aciklama": "Ofis malzemeleri",
      "Kategori": "Genel Gider",
      "Ara Toplam": 5000.00,
      "KDV Orani": 0.20,
      "KDV": null,
      "Toplam": null,
      "Odeme Durumu": "Bekliyor"
    },
    {
      "Tarih": "2025-03-16",
      "Satici": "XYZ AS",
      "Belge No": "F-2025-002",
      "Aciklama": "Hammadde alimi",
      "Kategori": "Hammadde",
      "Ara Toplam": 12500.00,
      "KDV Orani": 0.20,
      "KDV": null,
      "Toplam": null,
      "Odeme Durumu": "Odendi"
    }
  ]
}
```

**Notlar:**
- KDV ve Toplam `null` olabilir — algoritma Excel formuluyle hesaplar
- Sutun isimleri Turkce ve zenginlestirilmis tanimdaki isimlerle birebir uyumlu
- AI cikarma promptu bu sutun isimlerini acikca belirtir
- Algoritma bu isimleri sabitlenmis olarak bilir

---

## BOLUM 10: MEVCUT KODLA ENTEGRASYON NOKTALARI

### Etkilenen Dosyalar

| Dosya | Degisiklik |
|-------|------------|
| `core/database.py` | Yeni sutunlar (enriched_definition, algorithm_path, algorithm_version) |
| `ui/pages/functions.py` | Zenginlestirme butonu + onizleme + onay arayuzu |
| `ui/pages/tools.py` | Olustur akisinda run_algorithm kullanma (algoritma varsa) |
| `ai/prompts/generation.py` | Algoritma uretim promptu ekleme |
| `excel_engine/sandbox.py` | Degisiklik yok — oldugu gibi kullanilir |
| `ai/pipeline.py` | Degisiklik yok — extraction pipeline aynen kalir |

### Yeni Dosyalar

| Dosya | Amac |
|-------|------|
| `core/algorithm_runner.py` | run_algorithm fonksiyonu |
| `core/enrichment.py` | Is tanimi zenginlestirme pipeline'i |
| `algorithms/__init__.py` | Algoritma dizini |
| `algorithms/_template.py` | Referans sablon |

### Degismeyen Sistemler

- Key verification sistemi — aynen kalir
- CRUD islemleri (_append, _delete, _edit) — aynen kalir
- CodeSandbox — aynen kullanilir
- Model Router / RetryHandler — aynen kullanilir
- Veri cikarma (extraction) promptlari — kuculur (sadece JSON cikarma, kod uretme yok)
