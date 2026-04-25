# ExcelAI — Prompt Mühendisliği Stratejileri

> Son güncelleme: Nisan 2026
> Referanslar: Chain of Draft (2025), CoVe (Meta 2024), Reflexion (2025), Self-Refine (2024), NOWAIT (2025), Focused CoT (2025)

---

## İÇİNDEKİLER

1. [Genel İlkeler ve Token Verimliliği](#1-genel-ilkeler-ve-token-verimliliği)
2. [İş Tanımı Zenginleştirme Promptu](#2-iş-tanımı-zenginleştirme-promptu)
3. [İteratif İyileştirme — Beğenilmeyen Tanımlar](#3-iteratif-iyileştirme--beğenilmeyen-tanımlar)
4. [Algoritma Üretimi — İş Mantığı Kodu](#4-algoritma-üretimi--iş-mantığı-kodu)
5. [Algoritma İterasyon — Başarısız Kod Düzeltme](#5-algoritma-iterasyon--başarısız-kod-düzeltme)
6. [Çalışma Zamanı — Veri Çıkarma Promptu](#6-çalışma-zamanı--veri-çıkarma-promptu)
7. [Yeniden Düzenleme (Reorganize) Promptu](#7-yeniden-düzenleme-reorganize-promptu)
8. [Model-Spesifik Sarmalayıcılar](#8-model-spesifik-sarmalayıcılar)
9. [JSON Format Şartnameleri](#9-json-format-şartnameleri)
10. [Referanslar ve Kaynakça](#10-referanslar-ve-kaynakça)

---

## 1. GENEL İLKELER VE TOKEN VERİMLİLİĞİ

### 1.1 Temel Felsefe

Bu projede AI'dan dört farklı tipte çıktı bekliyoruz. Her birinin prompt stratejisi farklıdır:

| Görev Tipi | Düşünüş Derinliği | Token Stratejisi | Model |
|------------|-------------------|------------------|-------|
| İş tanımı zenginleştirme | Derin — yaratıcı | Serbest ama yapılandırılmış | Claude Sonnet |
| Algoritma üretimi | Çok derin — kod + test | Reflexion blokları ile kontrol | Claude Sonnet |
| Veri çıkarma (runtime) | Sığ — hızlı | Chain of Draft (minimum) | Gemini Flash |
| Yeniden düzenleme | Orta — dikkatli | Assertion-based self-check | Claude Sonnet |

### 1.2 Token Verimlilik Teknikleri

Bu projede kullandığımız dört teknik:

#### A. Chain of Draft (CoD) — Veri Çıkarma İçin
Zoom araştırmacıları (Şubat 2025) tarafından geliştirildi. Standart CoT'a göre %70-90 daha az token kullanır.

**İlke:** "Adım adım düşün ama her adımda sadece 5 kelimelik taslak tut."

**Ne zaman:** Veri çıkarma, sınıflandırma, basit dönüşüm — yani Gemini Flash görevleri.
**Ne zaman DEĞİL:** Kod üretimi — kod için derin muhakeme gerekir, CoD kod kalitesini düşürür.

#### B. Structured Reasoning Blocks — Zenginleştirme ve Reorganize İçin
Serbest "adım adım düşün" yerine etiketli bloklar içinde düşünme:

```
<analiz>
[En fazla 3 madde ile temel örüntüleri belirle]
</analiz>

<karar>
[Tek cümle: sonucun ve neden]
</karar>

<çıktı>
[Sadece yapılandırılmış sonuç]
</çıktı>
```

AI'a düşünme alanı verir ama sınırsız konuşmayı engeller.

#### C. NOWAIT — Tüm Promptlarda
Araştırmalar "Bekle", "Hmm", "Aslında tekrar düşüneyim" gibi tereddüt tokenlerinin bastırılmasının CoT uzunluğunu %27-51 azalttığını gösterdi.

**Uygulama:** Her promptun kurallar bölümüne şu satır eklenir:
```
Tereddüt ifadeleri kullanma ("aslında", "bekle", "tekrar düşüneyim").
Adımlarını kısa ve kesin yaz, sonra sonucu ver.
```

#### D. Focused CoT — Gürültülü Girdiler İçin
Modelden kısa düşünüş istemek yerine, girdideki gürültüyü öncelikle azaltmak:

```
Öncelikle aşağıdaki girdiden SADECE ilgili bilgileri çıkar.
Sonra YALNIZCA çıkartılan bilgiler üzerinden muhakeme yap.
```

Aritmetik problemlerde %50-66 token azalması, doğruluk kaybı yok.

### 1.3 Prompt Tasarım Kuralları (Tüm Promptlar İçin)

1. **Schema-first:** Her prompt çıktı şemasını EN BAŞTA gösterir
2. **Örnek-öncelikli:** 2-3 few-shot örnek > uzun açıklama
3. **Negatif kurallar:** "YAPMA" talimatları "YAP" kadar önemli
4. **Temperature:** Çıkarma=0.0, Kod üretimi=0.2, Zenginleştirme=0.4
5. **Doğrulama:** Her prompt sonunda en az bir assertion içerir

---

## 2. İŞ TANIMI ZENGİNLEŞTİRME PROMPTU

### 2.1 Amaç

Kullanıcının kısa iş tanımını (ad + açıklama + veri tipleri) alıp hem insan hem AI tarafından doğru anlaşılacak kapsamlı bir iş tanımlama belgesine dönüştürmek.

### 2.2 Tasarım İlkeleri

1. **Kullanıcı perspektifi:** Zenginleştirme kullanıcının gözünden düşünülmeli — teknik jargon değil, iş süreci dili
2. **Akıcılık:** Tanım birbirini takip eden mantıksal bir akış içinde sunulmalı
3. **Örnek senaryolar:** İş tanımının içerisindeki her madde için somut örnekler, belgenin en altında toplanmalı
4. **Dual okunabilirlik:** Hem insanın okuyup "evet bu benim işim" diyeceği hem de AI'ın şema/kural çıkaracağı formatta

### 2.3 Prompt Şablonu

```
Sen bir iş süreci analisti ve bilgi mimarısın.

<görev>
Kullanıcının verdiği kısa iş tanımını analiz et. Bu tanımdan kapsamlı, yapılandırılmış
ve hem insan hem yapay zeka tarafından net anlaşılacak bir iş tanımı belgesi oluştur.
</görev>

<kullanıcı_girdisi>
İş adı: {iş_adı}
Açıklama: {açıklama}
Sektör: {sektör}
Kabul edilen veri tipleri: {veri_tipleri_listesi}
</kullanıcı_girdisi>

<zenginleştirme_talimatları>

================================================================
ÖNCELİKLE: İŞ TANIMINI ANLA
================================================================

Kullanıcının verdiği iş tanımını kullanıcının gözünden düşün. Kullanıcı bu işi günlük
hayatında nasıl yapıyor? Hangi verilerle çalışıyor? Hangi zorluklar yaşıyor? Kullanıcının
bu tanımla gerçekte ne demek istediğini, hangi iş akışını dijitalleştirmek istediğini,
bu işin sonunda nasıl bir Excel beklediğini kendi kelimeleriyle — teknik dil kullanmadan,
bir iş insanının anlayacağı dilde — en az bir paragraf olarak yaz. Bu paragraf senin
iş tanımını ne kadar iyi anladığının kanıtı olacak. İş tanımını yetersiz düşünürsen
yanlış çıkarımlar yapacaksın, o yüzden bu adımı atlamadan ve kısaltmadan tamamla.

<anlama>
[Burada kullanıcının iş tanımını kendi kelimeleriyle, kullanıcının bakış açısından,
en az bir paragraf olarak açıkla. Kullanıcının günlük iş akışını, karşılaştığı
zorlukları, bu sistemden beklentisini ve iş tanımının amacını KENDİ ANLADIĞIN
ŞEKİLDE yaz. Bu bölümdeki anlayışın tüm belgenin temelini oluşturacak.]
</anlama>

================================================================
BÖLÜM 1 — İŞ ÖZETİ
================================================================

Yukarıdaki anlamanın üzerine inşa ederek iş tanımını kullanıcının perspektifinden
akıcı ve tutarlı bir şekilde özetle. Bu özet:
- Kimin için, ne amaçla, hangi süreçte kullanıldığını açıklamalı
- Kullanıcının günlük iş akışındaki yerini tanımlamalı
- Hem insan hem AI tarafından okunabilir bir dilde yazılmalı
- İş tanımının kapsamını net olarak çizmeli

================================================================
BÖLÜM 2 — VERİ YAPISI (SÜTUNLAR)
================================================================

Her sütun için:
- Sütun adı (Türkçe, anlaşılır)
- Veri tipi (metin/sayı/tarih/para/yüzde/seçim/formül)
- Zorunlu mu? (evet/hayır)
- Varsayılan değer (varsa)
- Formül (varsa — Excel formül mantığı olarak yaz)
- Doğrulama kuralı (varsa)
- Açıklama (kullanıcının bu sütunu nasıl anlaması gerektiği)

================================================================
BÖLÜM 3 — İŞ KURALLARI
================================================================

- Matematiksel tutarlılık kuralları (örn: Toplam = Ara Toplam + KDV)
- Format kuralları (tarih formatı, para birimi, ondalık basamak)
- Mantıksal kısıtlamalar (örn: tarih gelecekte olamaz)
- Veri tipleri arası ilişkiler

================================================================
BÖLÜM 4 — GÖRSEL VE SUNUM
================================================================

- Sayfa adı önerisi
- Sıralama tercihi (hangi sütuna göre, ASC/DESC)
- Gruplama (varsa)
- Toplam/özet satırı gereken sütunlar
- Özel formatlama notları

================================================================
BÖLÜM 5 — ÖRNEK SENARYOLAR
================================================================

Yukarıdaki BÖLÜM 2, 3 ve 4'teki maddelerden referans alarak somut senaryolar yaz.
Her senaryo iş tanımının içerisindeki belirli bir maddeyi veya madde grubunu somutlaştırır.

Her senaryo şu formatta olsun:

  Senaryo: [Kısa başlık]
  Referans: [Bölüm X, madde Y — hangi kural/sütun/özellik test ediliyor]
  Girdi: [Kullanıcının ne verdiğini tarif et — foto/metin/PDF olarak]
  Beklenen çıktı: [Satırların Excel'de nasıl görüneceği — tablo satırı olarak]
  Açıklama: [Bu senaryonun neden önemli olduğu, hangi iş kuralını gösterdiği]

Senaryolar iş tanımını somutlaştırmalı — soyut kalmamalı.
Toplam 3-7 senaryo yeterli — abartma.
Senaryolar belgenin EN ALTINDA yer almalı.

</zenginleştirme_talimatları>

<kalite_kuralları>
- Tereddüt ifadeleri kullanma ("belki", "muhtemelen", "sanırım").
- Sütun isimlerini Türkçe ve anlaşılır tut.
- Formülleri Excel formül mantığı ile yaz (Python değil).
- Her kuralın gerekçesini kullanıcının anlayacağı dilde aç.
- İş tanımı hem insanın okuyup "evet bu benim işim" diyeceği hem de
  AI'ın şema/kural/mantık çıkaracağı bir dilde ve yapıda sunulmalı.
- Sonuç SADECE zenginleştirilmiş iş tanımı belgesi olsun — ek yorum ekleme.
</kalite_kuralları>
```

### 2.4 Çıktı Format Şartnamesi

AI'ın döndüreceği zenginleştirilmiş tanım, JSON olarak veritabanına kaydedilir:

```json
{
  "iş_özeti": "...",
  "sütunlar": [
    {
      "ad": "Tarih",
      "tip": "date",
      "format": "DD.MM.YYYY",
      "zorunlu": true,
      "varsayılan": null,
      "formül": null,
      "doğrulama": "Gelecek tarih olamaz",
      "açıklama": "Faturanın kesildiği tarih"
    }
  ],
  "iş_kuralları": [
    "Toplam = Ara Toplam + KDV",
    "KDV Oranı 0 ile 1 arasında olmalı"
  ],
  "sunum": {
    "sayfa_adı": "Faturalar",
    "sıralama": {"sütun": "Tarih", "yön": "ASC"},
    "gruplama": null,
    "toplam_sütunları": ["Ara Toplam", "KDV", "Toplam"]
  },
  "senaryolar": [
    {
      "başlık": "Tek kalemli basit fatura",
      "referans": "Bölüm 2: Tarih, Satıcı, Ara Toplam sütunları; Bölüm 3: KDV hesaplama kuralı",
      "girdi": "Foto: ABC Ltd'den 5000 TL'lik ofis malzemesi faturası",
      "beklenen_çıktı": {"Tarih": "15.03.2025", "Satıcı": "ABC Ltd", "...": "..."},
      "referans_sütunlar": ["Tarih", "Satıcı", "Ara Toplam"],
      "açıklama": "En temel kullanım senaryosu — tek satırlık fatura girişi"
    }
  ]
}
```

---

## 3. İTERATİF İYİLEŞTİRME — BEĞENİLMEYEN TANIMLAR

### 3.1 Mekanizma

Kullanıcı zenginleştirilmiş tanımı beğenmediyse:
1. Kullanıcı "eksikler ve öneriler" alanına neden beğenmediğini yazar
2. Beğenilmeyen tanım + kullanıcı geri bildirimi veritabanında saklanır
3. Yeni üretim isteğinde TÜM geçmiş başarısız denemeler prompt'a dahil edilir
4. AI geçmiş hatalardan ders alarak yeni tanım üretir

### 3.2 Veritabanı Yapısı

```sql
CREATE TABLE enrichment_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    functionality_id INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    enriched_definition TEXT NOT NULL,        -- Üretilen zenginleştirilmiş tanım (JSON)
    user_feedback TEXT DEFAULT NULL,          -- Kullanıcı geri bildirimi (eksikler + öneriler)
    status TEXT DEFAULT 'rejected',           -- 'rejected' | 'accepted'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (functionality_id) REFERENCES functionalities(id) ON DELETE CASCADE
);
```

### 3.3 Yeniden Üretim Promptu (Cumulative Error Log + Self-Refine + PDR)

Bu prompt Self-Refine (2024) ve Preference-Driven Refinement (2025) tekniklerini birleştirir.
Kritik nokta: AI önce kullanıcının orijinal isteğiyle başbaşa kalır ve onu anlamaya çalışır,
sonra başarısız denemeleri neden başarısız olduklarıyla birlikte görür, ve ancak ONDAN SONRA
yeni bir tanım üretir.

```
Sen bir iş süreci analisti ve bilgi mimarısın.

<görev>
Kullanıcı daha önce üretilen iş tanımlarından memnun kalmadı.
Kullanıcının orijinal isteğini, başarısız denemeleri ve geri bildirimleri
inceleyerek DAHA İYİ bir zenginleştirilmiş iş tanımı oluştur.
</görev>

================================================================
ADIM 1: KULLANICININ ORİJİNAL İSTEĞİNİ ANLA
================================================================

<orijinal_istek>
İş adı: {iş_adı}
Açıklama: {kullanıcı_açıklaması}
Sektör: {sektör}
Veri tipleri: {veri_tipleri}
</orijinal_istek>

Öncelikle kullanıcının orijinal isteğini dikkatlice oku. Kullanıcının bu iş
tanımıyla GERÇEKTE ne yapmak istediğini anlamaya çalış. Kullanıcının bakış
açısından düşün — teknik değil, iş süreci odaklı. Kullanıcının günlük hayatında
bu işi nasıl yaptığını, hangi sorunlarla karşılaştığını, bu sistemden ne
beklediğini kendi kelimeleriyle en az bir paragraf olarak yaz:

<kullanıcı_niyeti>
[Kullanıcının iş tanımını kendi anladığın şekilde, kullanıcının gözünden yaz.
Bu bölümdeki anlayışın tüm belgenin temelini oluşturacak.]
</kullanıcı_niyeti>

================================================================
ADIM 2: BAŞARISIZ DENEMELERİ İNCELE
================================================================

<başarısız_denemeler>
Aşağıdaki denemeler kullanıcı tarafından reddedildi.
Her denemeyi kullanıcının geri bildirimiyle birlikte oku.
Kullanıcının ne demek istediğini DÜŞÜN — sadece kelimelerine değil,
arkasındaki niyete odaklan.

{--- Her deneme için tekrarlanan blok ---}

--- Deneme {n} ({tarih}): ---

Üretilen tanım:
{önceki_zenginleştirilmiş_tanım_json}

Kullanıcının eksikler ve önerileri:
"{kullanıcı_geri_bildirimi}"

--- / ---

{--- Blok sonu ---}

</başarısız_denemeler>

Şimdi başarısız denemeleri ve kullanıcının geri bildirimlerini düşün:

<deneme_analizi>
[Her denemenin neden başarısız olduğunu tek cümleyle özetle.
Kullanıcının geri bildirimlerindeki ortak tema(lar)ı belirle.
Kullanıcının söylediklerinin arkasındaki gerçek isteği çıkar.
Önceki denemelerde tekrarlanan hataları listele — bunları ASLA tekrarlama.]
</deneme_analizi>

================================================================
ADIM 3: YENİ İŞ TANIMI OLUŞTUR
================================================================

Şimdi kullanıcının orijinal isteğini (ADIM 1) ve başarısız denemelerden
çıkardığın dersleri (ADIM 2) göz önünde bulundurarak yeni bir zenginleştirilmiş
iş tanımı oluştur.

KURALLAR:
- Kullanıcının geri bildirimlerindeki HER maddeyi adresle
- Daha önce reddedilen yaklaşımları TEKRARLAMA
- Kullanıcının öneride bulundukları kısımları ÖNCELİKLE uygula
- İş tanımı Bölüm 2'deki zenginleştirme talimatlarının TAMAMINA uygun olmalı
  (ANLAMA + BÖLÜM 1-5 yapısı)

[Bölüm 2.3'teki zenginleştirme talimatlarının TAMAMI buraya eklenir]

================================================================
ADIM 4: KALİTE KONTROL
================================================================

Yeni tanımı döndürmeden önce şu kontrolleri yap:

<kalite_kontrol>
- [ ] Kullanıcının her geri bildirim maddesini adresliyor muyum?
- [ ] Önceki denemelerin reddedilme sebeplerinden herhangi birini tekrarlıyor muyum?
- [ ] İş tanımını kullanıcının gözünden yeterince anladım mı (ANLAMA bölüsü dolu mu)?
- [ ] Tanım kullanıcının bakış açısından akıcı ve anlaşılır mı?
- [ ] Senaryolar iş tanımının içerisindeki maddelere referans veriyor mu?
- [ ] Senaryolar somut ve gerçekçi mi?
Herhangi bir kontrol başarısızsa, tanımı düzelt ve tekrar kontrol et.
</kalite_kontrol>

Sonucu SADECE zenginleştirilmiş iş tanımı JSON olarak döndür.
```

### 3.4 Otomatik Kısıtlama Çıkarımı

Her beğenilmeyen denemeden otomatik olarak "öğrenilmiş kısıtlama" çıkarılır:

```python
def extract_constraints_from_feedback(feedback_history: list[dict]) -> list[str]:
    """
    Geçmiş geri bildirimlerden tekrar eden kalıpları tespit et.

    Örnek:
    feedback: "Sütun isimleri çok teknik, anlaşılmıyor"
    → constraint: "Sütun isimlerini sade Türkçe ile yaz, teknik terim kullanma"

    feedback: "KDV hesabı eksik"
    → constraint: "Para içeren iş tanımlarında KDV hesabı MUTLAKA yer almalı"
    """
    # Bu fonksiyon basit keyword matching ile çalışabilir
    # veya AI ile çıkarılabilir (ucuz bir Gemini Flash çağrısı)
```

---

## 4. ALGORİTMA ÜRETİMİ — İŞ MANTIĞI KODU

### 4.1 Amaç

Beğenilen zenginleştirilmiş iş tanımını alıp, o iş için `create_excel(data, output_path)` fonksiyonunu üreten prompt. Bu fonksiyon bir kez üretilir ve tekrar tekrar kullanılır.

### 4.2 Prompt Stratejisi: Reflexion + Generate-Verify-Fix

Kod üretiminde CoD (Chain of Draft) KULLANILMAZ — araştırmalar kod için derin muhakemenin gerekli olduğunu göstermiştir (Chain of Draft for Software Engineering, Haziran 2025). Bunun yerine Reflexion paterni kullanılır:

```
ADIM 1: İş tanımını anla → Senaryolar tanımla
ADIM 2: Senaryolara dayanarak kodu yaz
ADIM 3: Kodu senaryolarla zihinsel olarak test et
ADIM 4: Hata varsa düzelt ve tekrar test et
ADIM 5: Başarılıysa belirli JSON formatında döndür
```

### 4.3 Prompt Şablonu

```
Sen bir Python Excel otomasyon uzmanısın. openpyxl kütüphanesiyle çalışan,
güvenli ve profesyonel Excel dosyaları oluşturan kod yazıyorsun.

<görev>
Aşağıdaki iş tanımına göre create_excel fonksiyonu üret.
Bu fonksiyon bir kez yazılacak ve aynı iş tanımı için tekrar tekrar kullanılacak.
Fonksiyon SADECE veriyi Excel'e yazmaktan sorumlu — veri işlemez, dönüştürmez.
</görev>

<iş_tanımı>
{zenginleştirilmiş_tanım_json}
</iş_tanımı>

================================================================
AŞAMA 1: İŞ TANIMINI ANLA
================================================================

İş tanımını ve içerisindeki örnek senaryoları dikkatlice oku.
Bu iş tanımının ne yaptığını, hangi verileri işleyeceğini, hangi formatlama
ve hesaplama kurallarına uyacağını TAM OLARAK anlamaya çalış.

<anlama>
[İş tanımını kendi kelimeleriyle en az bir paragraf olarak açıkla.
Bu işin amacını, veri akışını, kritik kuralları ve özel durumlarını
KENDİ ANLADIĞIN ŞEKİLDE yaz. Bu paragraf senin iş tanımını ne kadar
iyi kavradığının kanıtı olacak — yetersiz anlarsan yanlış kod yazarsın.]

Teknik detaylar:
• Kaç sütun var ve tipleri neler? (liste)
• Formül içeren sütunlar hangileri? (liste)
• Toplam/özet satırı gerekli mi? (evet/hayır + hangi sütunlar)
• Özel formatlama gereken alanlar? (liste)
</anlama>

================================================================
AŞAMA 2: GELİŞMİŞ SENARYOLAR TANIMLA
================================================================

İş tanımını anladığın için şimdi iş tanımındaki her önemli özellik/madde
için 3-5 arası gelişmiş test senaryosu tanımla. Bu senaryolar iş tanımını
KAPSAYICI olmalı — basit durumlardan karmaşık uç durumlara kadar.

Her senaryo için:
1. Senaryoyu tanımla
2. Bu senaryonun iş tanımına göre NASIL çözülmesi gerektiğini düşün
3. Çözümün arkasındaki mantığı not et

Bu senaryolar kodunu yazmadan ÖNCE iş mantığı kavramanı sağlayacak.

<senaryolar>
Senaryo 1: [Başlık]
  Durum: [Bu senaryo neyi test ediyor — iş tanımındaki hangi madde/kural]
  Girdi: data = {"satirlar": [{...}, {...}]}
  Beklenen: [Ne olmalı — hangi hücrede ne değeri, hangi formül, hangi stil]
  Çözüm mantığı: [Bu senaryonun doğru işlemesi için kodda ne olmalı]

Senaryo 2: [Başlık]
  Durum: Boş veri durumu
  Girdi: data = {"satirlar": []}
  Beklenen: Sadece başlık satırı yazılmalı, hata vermemeli
  Çözüm mantığı: Boş liste kontrolü, satırlar döngüsü girmemeli

Senaryo 3: [Başlık]
  Durum: Formül içeren tek satırlık veri
  Girdi: data = {"satirlar": [{...tek satır, formül içeren...}]}
  Beklenen: Formüllerin doğru hücre referanslarıyla yazılması
  Çözüm mantığı: Formül referansları dinamik satır numarasına bağlı olmalı

[...iş tanımındaki her madde için 3-5 senaryo — abartısız ama kapsayıcı...]
</senaryolar>

================================================================
AŞAMA 3: KODU YAZ
================================================================

İş tanımının mantığı örnek senaryolar ile tamamen anlaşıldı.
Şimdi sandbox sınırlamalarına uygun olarak, senaryoların ve iş mantığının
altında yatan temel mantığı gözeterek create_excel fonksiyonunu yaz.

<kısıtlamalar>
FONKSİYON İMZASI: create_excel(data: dict, output_path: str) -> None

GİRDİ FORMATI: data["satirlar"] bir liste — her eleman bir dict.
Sütun isimleri: {sütun_adı_listesi}

İZİN VERİLEN İMPORTLAR:
- openpyxl (tüm alt modülleri: styles, utils, worksheet, chart)
- datetime, date, timedelta
- os.path (SADECE path işlemleri)
- json, re, math, decimal

KESİNLİKLE YASAK:
- eval(), exec(), compile()
- subprocess, os.system(), os.popen()
- __import__(), importlib
- open() (openpyxl wb.save() HARİÇ)
- input(), raw_input()
- globals(), locals() değiştirme
- socket, http, urllib

EXCEL KURALLARI:
- Satır/sütun 1-indexed (A1 = row=1, column=1)
- Sayfa adı max 31 karakter
- Renk değerleri "RRGGBB" (# olmadan)
- Büyük veri (>10000 satır) için write_only=True
</kısıtlamalar>

<stil_gereksinimleri>
BAŞLIK SATIRI:
- Font: Calibri 11pt, bold, beyaz (FFFFFF)
- Arka plan: Koyu mavi (1E3A5F), solid fill
- Hizalama: Ortalı, wrap_text=True
- Kenarlık: Medium, gri (999999)

VERİ SATIRLARI:
- Zebra: Çift satırlar açık gri (F2F2F2), tek satırlar beyaz
- Kenarlık: İnce, gri (CCCCCC)
- Metin: sola hizalı
- Sayı: sağa hizalı, format #,##0
- Para: sağa hizalı, format #,##0.00 "TL"
- Tarih: ortalı, format DD.MM.YYYY
- Yüzde: ortalı, format 0.00%

TOPLAM SATIRI (varsa):
- Font: Bold
- Üst çizgi: medium border
- Arka plan: Açık mavi (D6EAF8)
- SUM formülleri: =SUM(C2:C{son_satır})

SAYFA AYARLARI:
- freeze_panes = "A2"
- Landscape, fit to page, A4
</stil_gereksinimleri>

Şimdi create_excel fonksiyonunu yaz:

<kod>
[Fonksiyonu buraya yaz]
</kod>

================================================================
AŞAMA 4: KARMAŞIK SENARYOLARLA ZİHİNSEL TEST
================================================================

Fonksiyonun AŞAMA 2'de hazırladığın karmaşık senaryoları doğru işleyip
işlemediğini kontrol et. Her senaryoyu kodun üzerinden zihinsel olarak
adım adım geçir:

<karmaşık_test_sonuçları>
Senaryo 1: [Başlık]
  Satır 1 başlık yazıldı mı? ✓/✗
  Veri satırları doğru hücrelere yazıldı mı? ✓/✗
  Formül doğru mu? ✓/✗
  Stil uygulandı mı? ✓/✗
  Çözüm mantığındaki beklenti karşılandı mı? ✓/✗
  Sonuç: GEÇTİ / KALDI

Senaryo 2: [Başlık]
  [aynı kontroller]
  Sonuç: GEÇTİ / KALDI

[...tüm karmaşık senaryolar...]
</karmaşık_test_sonuçları>

Eğer herhangi bir karmaşık senaryo KALDIYSA:

<hata_analizi>
Senaryo X başarısız:
  Sorun: [Sorunun ne olduğu — 1 cümle]
  Sebep: [Koddaki hangi satır/mantık hatalı]
  Çözüm: [Ne değişmeli — düşüncelerin]
</hata_analizi>

Gerekli değişiklikleri koda uygula ve AŞAMA 4'ü tekrarla.
(Bu döngü maks 3 kez tekrarlanır. 3. denemede de başarısızsa AŞAMA 6'ya git.)

================================================================
AŞAMA 5: BASİT SENARYOLARLA EK DOĞRULAMA
================================================================

Karmaşık senaryoların TAMAMINI geçen fonksiyonu şimdi 10 basit farklı
senaryo ile de test et. Bu senaryolar genel sağlamlık ve uç durum kontrolü
içindir:

<basit_testler>
1. Boş satırlar listesi → Sadece başlık satırı olmalı ✓/✗
2. Tek satırlı veri → 1 başlık + 1 veri satırı ✓/✗
3. 5 satırlı standart veri → Tüm stiller doğru ✓/✗
4. null değer içeren satır → Hata vermemeli ✓/✗
5. Çok uzun metin içeren alan → wrap_text çalışmalı ✓/✗
6. Negatif sayı → Format doğru uygulanmalı ✓/✗
7. Tarih alanı boş → Hata vermemeli ✓/✗
8. Formül sütunu → Excel formülü yazılmalı (Python hesaplama değil) ✓/✗
9. 100 satırlık veri → Otomatik genişlik çalışmalı ✓/✗
10. Türkçe karakter içeren sütun adı → Doğru yazılmalı ✓/✗
Sonuç: {geçen}/{toplam}
</basit_testler>

Eğer basit testlerden herhangi biri KALDIYSA, AŞAMA 4'teki aynı düzeltme
sürecini uygula (hata analizi → düzeltme → tekrar test). Maks 3 deneme.

================================================================
AŞAMA 6: SONUÇ
================================================================

Fonksiyon hem karmaşık hem basit testlerin TAMAMINI geçiyorsa,
fonksiyonu bizim response içerisinden ayırt edeceğimiz şekilde
aşağıdaki JSON formatında EKSİKSİZ olarak yeniden yaz:

```json
{
  "status": "success",
  "code": "[create_excel fonksiyonunun TAM kodu — importlar dahil]",
  "test_summary": {
    "senaryo_testleri": {"gecen": X, "toplam": Y},
    "ek_testler": {"gecen": X, "toplam": 10}
  },
  "notlar": "[Varsa özel durumlar veya uyarılar]"
}
```

Eğer 3 denemede de testler geçemiyorsa:

```json
{
  "status": "failure",
  "son_kod": "[En son denenen kodun TAMI]",
  "basarisiz_testler": [
    {
      "senaryo": "[Başlık]",
      "beklenen": "[Ne olmalıydı]",
      "gerceklesen": "[Ne oldu]",
      "tahmin_edilen_sebep": "[Neden başarısız]"
    }
  ],
  "oneri": "[Sorunu çözmek için ne yapılabilir]",
  "deneme_sayisi": 3
}
```
```

### 4.4 Neden Bu Yapı?

| Aşama | Teknik | Amaç |
|-------|--------|------|
| AŞAMA 1 | Derin Anlama (paragraf) | İş tanımını yetersiz anlamak = yanlış kod. Min 1 paragraf zorunlu |
| AŞAMA 2 | Scenario-Based Enrichment + Çözüm Mantığı | Her madde için 3-5 senaryo + çözüm mantığı not edilir |
| AŞAMA 3 | Constrained Code Generation | Sandbox sınırlamaları içinde güvenli kod üretimi |
| AŞAMA 4 | Reflexion + Self-Debug | Karmaşık senaryolarla zihinsel test, hata → düzelt → tekrar |
| AŞAMA 5 | LLMLOOP (2025 ICSME) | 10 basit senaryo ile sağlamlık doğrulaması |
| AŞAMA 6 | Schema-first output | Başarı/başarısızlık JSON formatında programatik ayrıştırma |

### 4.5 Token Bütçesi

Bu prompt uzun görünüyor ama AI'ın ürettiği tokenler kontrol altında:
- AŞAMA 1: ~250-300 token (anlama paragrafı + teknik detay listesi — bu adım kritik, kısaltılmamalı)
- AŞAMA 2: ~300 token (5 senaryo × 60 token — durum + çözüm mantığı dahil)
- AŞAMA 3: Bütçe yok — fonksiyon kodu ne kadar gerekiyorsa o kadar token kullanır
- AŞAMA 4: ~150 token (karmaşık test sonuçları — ✓/✗ formatında)
- AŞAMA 5: ~200 token (10 basit test — her test için yeterli açıklama)
- AŞAMA 6: JSON çıktı (fonksiyon kodu eksiksiz yeniden yazılıyor — bu zorunlu)

AŞAMA 1'deki derin anlama paragrafı token maliyeti artırsa da bu yatırım kodun doğru
olması için kritik — yetersiz anlama = yanlış kod. AŞAMA 3'e bütçe koymuyoruz çünkü
fonksiyon kodu iş tanımının karmaşıklığına göre değişir, kısıtlamak kaliteyi düşürür.
Bu kod BİR KEZ üretiliyor, her istekte değil.

---

## 5. ALGORİTMA İTERASYON — BAŞARISIZ KOD DÜZELTME

### 5.1 Durum

İki durumda bu bölüm devreye girer:

**Durum A — AI kendi testini geçemedi:** AI algoritma üretirken 3 denemede de testleri
geçemezse, başarısızlık JSON raporunu üretir ve bu rapor veritabanında saklanır.
Kullanıcı tekrar "iş mantığı oluştur" istediğinde bu rapor prompt'a dahil edilir.

**Durum B — Kullanıcı kodun yanlış çalıştığını gördü:** AI başarılı olduğunu düşündü
ama kullanıcı pratikte kodun doğru çalışmadığını gördü. Kullanıcı "yeni iş mantığı oluştur"
diyerek eksiklik ve önerilerini yazar. Bu bilgiler algoritma oluşturma promptunda
uygun bir alana yerleştirilir.

### 5.2 Veritabanı

```sql
CREATE TABLE algorithm_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    functionality_id INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    code TEXT NOT NULL,
    status TEXT DEFAULT 'failed',  -- 'failed' | 'success'
    test_results TEXT,             -- JSON: test sonuçları
    user_feedback TEXT,            -- Kullanıcı geri bildirimi (varsa)
    ai_failure_report TEXT,        -- JSON: AI'ın hata raporu (varsa)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (functionality_id) REFERENCES functionalities(id) ON DELETE CASCADE
);
```

### 5.3 Yeniden Üretim Promptu (Cumulative Error Log + Reflexion)

```
Sen bir Python Excel otomasyon uzmanısın.

<görev>
Daha önce bu iş tanımı için algoritma üretildi ancak başarısız oldu.
Geçmiş denemeleri ve hata raporlarını inceleyerek DOĞRU çalışan bir
create_excel fonksiyonu üret.
</görev>

<iş_tanımı>
{zenginleştirilmiş_tanım_json}
</iş_tanımı>

<hata_geçmişi>
AŞAĞIDAKİ HATALARI KESİNLİKLE TEKRARLAMA.
Her denemeyi dikkatlice incele — hem AI'ın kendi hata raporunu hem de
kullanıcının geri bildirimini oku. Aynı hatalara DÜŞME.

{geçmiş_denemeler_listesi}

--- Deneme {n} ({tarih}): ---
Kod:
```python
{önceki_kod}
```

Başarısız testler (AI'ın kendi testi):
{test_sonuçları}

AI'ın başarısızlık raporu (varsa):
{ai_failure_report_json}

Kullanıcının eksikler ve önerileri (varsa):
"{kullanıcı_geri_bildirimi_veya_yok}"
--- / ---

</hata_geçmişi>

<öğrenilmiş_dersler>
Geçmiş denemelerden çıkarılan kurallar (İHLAL ETME):
1. {ders_1}
2. {ders_2}
[...]
</öğrenilmiş_dersler>

<talimat>
Şimdi yeni bir create_excel fonksiyonu üret. Bölüm 4.3'teki AŞAMA 1-6
prosedürünü AYNEN uygula, ancak şu EK kurallara da uy:

- AŞAMA 1'de iş tanımını anlarken geçmiş hataları da göz önünde bulundur
- AŞAMA 2'de senaryo tanımlarken ÖNCEKİ denemelerde başarısız olan
  senaryoları ÖNCELİKLE dahil et
- AŞAMA 3'te kod yazarken geçmiş denemelerdeki hatalı yaklaşımları KULLANMA,
  farklı bir yaklaşım dene
- AŞAMA 4'te test ederken önceki başarısız senaryoları İLK SIRAYA koy
- Kullanıcının eksikler ve önerilerindeki HER maddeyi adresle
</talimat>
```

---

## 6. ÇALIŞMA ZAMANI — VERİ ÇIKARMA PROMPTU

### 6.1 Amaç

Runtime'da kullanıcı girdi sağladığında (foto/PDF/metin/ses/form), AI'dan SADECE yapılandırılmış JSON çıkarmasını istemek. AI Excel kodu ÜRETMEZ.

### 6.2 Prompt Stratejisi: Chain of Draft + Schema Enforcement

Veri çıkarma için CoD kullanılır çünkü:
- Hızlı olmalı (Gemini Flash)
- Token maliyeti minimum
- Çıktı yapısı kesin (JSON)
- Derin muhakeme gerekmiyor

### 6.3 Prompt Şablonu

```
Aşağıdaki {girdi_tipi} içeriğinden verileri çıkar.

<sütunlar>
{sütun_listesi_ve_tipleri}
</sütunlar>

<çıktı_formatı>
{
  "satirlar": [
    {örnek_satır_json}
  ]
}
</çıktı_formatı>

<kurallar>
- TÜM satırları çıkar, HİÇBİRİNİ atlama
- Sütun isimlerini AYNEN kullan: {sütun_isimleri_listesi}
- Sayıları sayı olarak döndür (string değil)
- Tarihleri YYYY-MM-DD formatında döndür
- Boş/belirsiz alanlar: null
- Para tutarlarını ondalık sayı olarak yaz (sembol ekleme)
- Formül sütunlarını null bırak (Excel hesaplayacak)
- SADECE JSON döndür, ek açıklama ekleme
</kurallar>

<doğrulama>
Çıktını döndürmeden önce:
1. Tüm satırları saydın mı? Girdi: ~{beklenen_satır_sayısı} satır
2. Tüm sütunlar her satırda mevcut mu?
3. Veri tipleri doğru mu (sayı=sayı, tarih=tarih)?
Eksik varsa düzelt.
</doğrulama>

Girdi:
{kullanıcı_girdisi}
```

### 6.4 Key Verification Entegrasyonu

Veri çıkarma promptunun BAŞINA eklenen anahtar çıkarma adımı:

```
ÖNCELİKLE: Aşağıdaki girdideki tüm kayıtları tanımlayan benzersiz
anahtar değerlerini listele.

Anahtar sütun: {key_column_adı}
Anahtar değerler listesi: [değer1, değer2, ...]

SONRA: Bu değerlerin HEPSİNİ içeren tam veriyi çıkar.

KENDİNİ DOĞRULA:
Çıkarttığın satır sayısı: ___
Beklenen satır sayısı (anahtar değer sayısı): ___
Eksik anahtar var mı? Varsa listele.
```

### 6.5 Gemini Flash İçin Optimize Edilmiş Versiyon

Gemini Flash minimal talimatla en iyi sonucu verir:

```
Bu {girdi_tipi}'dan veri çıkar. Çıktı JSON:

{"satirlar": [{"Tarih": "YYYY-MM-DD", "Satıcı": "str", "Tutar": number, ...}]}

Sütunlar: {sütun_listesi}
Kurallar: Hepsini çıkar, null=boş, sayı=sayı, tarih=YYYY-MM-DD.
Doğrula: Satır sayısı = anahtar sayısı.

Girdi:
{kullanıcı_girdisi}
```

Bu versiyon ~100 token prompt ile aynı sonucu verir.

---

## 7. YENİDEN DÜZENLEME (REORGANIZE) PROMPTU

### 7.1 Amaç

Mevcut Excel verisini yeniden sıralamak/gruplamat/düzenlemek. AI veriyi dönüştürür ama HİÇBİR satırı silmez/eklemez.

### 7.2 Prompt Stratejisi: Assertion-Based Self-Check

```
Aşağıdaki Excel verilerini kullanıcının talimatına göre yeniden düzenle.

<mevcut_veri>
{json_satırlar}
</mevcut_veri>

<talimat>
{kullanıcı_talimatı}
</talimat>

<anahtar_bilgisi>
Anahtar sütun: {key_column}
Mevcut anahtar değerler ({sayı} adet):
{key_values_listesi}
</anahtar_bilgisi>

<değişmezlik_kuralları>
1. TÜM satırları döndür — HİÇBİRİNİ silme
2. YENİ satır EKLEME
3. Veri DEĞERLERİNİ değiştirme — sadece sıralama/gruplama/pozisyon değiş
4. Aynı JSON formatında döndür: {"satirlar": [...]}
5. Çıktı satır sayısı = girdi satır sayısı = {beklenen_satır_sayısı}
</değişmezlik_kuralları>

<doğrulama>
Çıktını döndürmeden önce şu assertion'ları kontrol et:
- [ ] Çıktı satır sayısı == {beklenen_satır_sayısı}
- [ ] Tüm anahtar değerler çıktıda mevcut
- [ ] Hiçbir yeni anahtar eklenmemiş
- [ ] Veri değerleri değişmemiş (sadece sıra değişmiş)
Herhangi biri başarısızsa DÜZELT.
</doğrulama>

SADECE JSON döndür:
```

---

## 8. MODEL-SPESİFİK SARMALAYICILAR

### 8.1 Mimari

Çekirdek prompt model-agnostik yazılır, her model için ince bir sarmalayıcı eklenir:

```python
def wrap_prompt(core_prompt: str, model: str) -> str:
    if model.startswith("gemini"):
        return _wrap_gemini(core_prompt)
    elif model.startswith("claude"):
        return _wrap_claude(core_prompt)
    elif model.startswith("gpt"):
        return _wrap_openai(core_prompt)
    return core_prompt
```

### 8.2 Gemini Flash Sarmalayıcı

Gemini minimal talimatla en iyi çalışır. Prompt kısa tutulur, `response_schema` ile JSON garanti edilir.

```python
def _wrap_gemini(core_prompt: str) -> str:
    # Gemini için: XML etiketlerini kaldır, kısa tut
    # response_schema API parametresiyle garanti zaten var
    prompt = core_prompt
    # XML etiketlerini düzyazı paragrafına çevir
    prompt = re.sub(r'<(\w+)>', r'\n\1:\n', prompt)
    prompt = re.sub(r'</\w+>', '', prompt)
    return prompt.strip()
```

**API çağrısında:**
```python
generation_config = {
    "response_mime_type": "application/json",
    "response_schema": VerifiedExcelData  # Pydantic model
}
```

### 8.3 Claude Sonnet Sarmalayıcı

Claude XML etiketli yapıları sever. Kod üretiminde en iyi performansı gösterir.

```python
def _wrap_claude(core_prompt: str) -> str:
    # Claude için: XML yapısı koru, talimatlar net
    return f"""<instructions>
{core_prompt}
</instructions>

<output_rules>
Yanıtını SADECE istenen formatta ver.
Ek açıklama, yorum veya giriş cümlesi EKLEME.
</output_rules>"""
```

**API çağrısında (tool_use ile yapılandırılmış çıktı):**
```python
tools = [{
    "name": "veri_kaydet",
    "description": "Çıkartılan veriyi kaydeder",
    "input_schema": VerifiedExcelData.model_json_schema()
}]
```

### 8.4 OpenAI/GPT Sarmalayıcı

GPT system message + strict JSON schema ile en iyi çalışır.

```python
def _wrap_openai(core_prompt: str) -> dict:
    return {
        "system": "Sen bir veri işleme API'sisin. SADECE geçerli JSON döndürürsün. Asla ek metin ekleme.",
        "user": core_prompt
    }
```

**API çağrısında:**
```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,
        "schema": VerifiedExcelData.model_json_schema()
    }
}
```

---

## 9. JSON FORMAT ŞARTNAMELERİ

### 9.1 Başarı Formatı (Algoritma Üretimi)

```json
{
  "status": "success",
  "code": "from openpyxl import Workbook\nfrom openpyxl.styles import ...\n\ndef create_excel(data: dict, output_path: str) -> None:\n    ...",
  "test_summary": {
    "senaryo_testleri": {"gecen": 5, "toplam": 5},
    "ek_testler": {"gecen": 10, "toplam": 10}
  },
  "notlar": "Formül sütunları Excel formülüyle yazıldı, Python hesaplama yapılmadı."
}
```

### 9.2 Başarısızlık Formatı (Algoritma Üretimi)

```json
{
  "status": "failure",
  "son_kod": "from openpyxl import Workbook\n...",
  "basarisiz_testler": [
    {
      "senaryo": "Çok satırlı formül hesaplama",
      "beklenen": "SUM formülü C2:C50 aralığını kapsamalı",
      "gerceklesen": "SUM formülü sabit C2:C10 yazılmış",
      "tahmin_edilen_sebep": "Satır sayısı dinamik değil, hardcoded"
    }
  ],
  "oneri": "Toplam satırı formülünde son veri satırını dinamik hesaplamak gerekiyor. `len(data['satirlar']) + 1` ile son satır numarası bulunabilir.",
  "deneme_sayisi": 3
}
```

### 9.3 Zenginleştirilmiş İş Tanımı Formatı

```json
{
  "iş_özeti": "Tedarikçi faturalarını sistematik olarak Excel'e kaydetme. Muhasebe departmanının aylık fatura takibi için kullanılır.",
  "sütunlar": [
    {
      "ad": "Tarih",
      "tip": "date",
      "format": "DD.MM.YYYY",
      "zorunlu": true,
      "varsayılan": null,
      "formül": null,
      "doğrulama": "Gelecek tarih olamaz",
      "açıklama": "Faturanın düzenlendiği tarih"
    },
    {
      "ad": "KDV",
      "tip": "currency",
      "format": "#,##0.00 TL",
      "zorunlu": false,
      "varsayılan": null,
      "formül": "=Ara_Toplam * KDV_Oranı",
      "doğrulama": "Sıfır veya pozitif olmalı",
      "açıklama": "Otomatik hesaplanan KDV tutarı"
    }
  ],
  "iş_kuralları": [
    "Toplam = Ara Toplam + KDV",
    "KDV Oranı 0 ile 1 arasında olmalı (örn: 0.20 = %20)",
    "Fatura numarası aynı iş yeri içinde benzersiz olmalı"
  ],
  "sunum": {
    "sayfa_adı": "Faturalar",
    "sıralama": {"sütun": "Tarih", "yön": "ASC"},
    "gruplama": null,
    "toplam_sütunları": ["Ara Toplam", "KDV", "Toplam"]
  },
  "senaryolar": [
    {
      "başlık": "Tek kalemli basit fatura",
      "referans": "Bölüm 2: Tarih, Satıcı, Ara Toplam sütunları; Bölüm 3: KDV hesaplama kuralı",
      "girdi": "ABC Ltd'den 15.03.2025 tarihli, F-001 numaralı, 5000 TL tutarlı ofis malzemesi faturası",
      "beklenen_çıktı": {
        "Tarih": "2025-03-15",
        "Satıcı": "ABC Ltd",
        "Fatura No": "F-001",
        "Açıklama": "Ofis malzemesi",
        "Ara Toplam": 5000.00,
        "KDV Oranı": 0.20,
        "KDV": "=formül",
        "Toplam": "=formül"
      },
      "referans_sütunlar": ["Tarih", "Satıcı", "Fatura No", "Ara Toplam"],
      "açıklama": "En temel kullanım — tek satırlık fatura girişi"
    },
    {
      "başlık": "KDV oranı farklı fatura",
      "girdi": "XYZ AŞ'den gıda faturası, KDV %10",
      "beklenen_çıktı": {"KDV Oranı": 0.10},
      "referans_sütunlar": ["KDV Oranı", "KDV", "Toplam"],
      "açıklama": "Farklı KDV oranlarının doğru işlenmesi"
    }
  ]
}
```

### 9.4 Veri Çıkarma Çıktısı (Runtime)

```json
{
  "key_column": "Fatura No",
  "key_values": ["F-001", "F-002", "F-003"],
  "satirlar": [
    {
      "Tarih": "2025-03-15",
      "Satıcı": "ABC Ltd",
      "Fatura No": "F-001",
      "Açıklama": "Ofis malzemesi",
      "Ara Toplam": 5000.00,
      "KDV Oranı": 0.20,
      "KDV": null,
      "Toplam": null,
      "Ödeme Durumu": "Bekliyor"
    }
  ]
}
```

---

## 10. REFERANSLAR VE KAYNAKÇA

### Akademik Kaynaklar

| Teknik | Kaynak | Yıl | Bulgu |
|--------|--------|-----|-------|
| Chain of Draft (CoD) | Zoom Communications, arXiv:2502.18600 | 2025 | %70-90 token azalması, doğruluk korunuyor |
| CoD for SE (uyarı) | arXiv:2506.10987 | 2025 | CoD kod görevlerinde başarısız — derin muhakeme gerekli |
| Focused CoT (F-CoT) | arXiv:2511.22176 | 2025 | Gürültülü girdilerde %50-66 token azalması |
| NOWAIT | ACL 2025 Findings | 2025 | Tereddüt tokenlerini bastırmak %27-51 kısaltma sağlar |
| Chain-of-Verification (CoVe) | Meta Research | 2024 | Halüsinasyon %77 azalma (2.95 → 0.68) |
| Self-Refine | arXiv:2303.17651 | 2024 | İteratif iyileştirme ile %15-25 kalite artışı |
| Reflexion | arXiv:2303.11366 | 2025 | Kod görevlerinde %10-17 doğruluk artışı |
| ReflexiCoder | arXiv:2603.05863 | 2026 | RL ile self-reflect, %17 iyileştirme |
| LLMLOOP | ICSME 2025 | 2025 | Kod + test birlikte üretim, %14 pass@10 artışı |
| Self-Debug (ACL) | ACL 2025 Long | 2025 | In-execution debugging > post-execution |
| Skeleton-of-Thought | ICLR 2024 | 2024 | Paralel üretimle 2x hızlanma |
| Early Stopping CoT | arXiv:2509.14004 | 2025 | ~%41 token azalması |
| Preference-Driven Refinement | W&M CS | 2025 | Kullanıcı tercihlerini kural olarak kodlama |

### Pratik Kaynaklar

- Anthropic Claude Prompting Best Practices (2025)
- OpenAI Structured Outputs Developer Guide (2025)
- IBM Prompt Engineering Guide (2026)
- Lakera Prompt Engineering Best Practices (2026)
- HuggingFace AI Trends: Test-Time Reasoning (2026)

### Anahtar Prensip Özeti

| # | Prensip | Uygulama Noktası |
|---|---------|-----------------|
| 1 | CoD kullan, kod hariç | Veri çıkarma (Gemini Flash) |
| 2 | Kod için Reflexion kullan | Algoritma üretimi (Claude Sonnet) |
| 3 | CoVe sadece yüksek riskli çıktılar için | Finansal veri doğrulama |
| 4 | Cumulative Error Log ile hatalardan öğren | İteratif iyileştirme |
| 5 | Assertion-based self-check her promptta | Tüm promptlar |
| 6 | NOWAIT ile tereddüt tokenleri engelle | Tüm promptlar |
| 7 | Schema-first çıktı | Tüm JSON çıktıları |
| 8 | Few-shot > uzun açıklama | Karmaşık/domain-specific görevler |
| 9 | Structured reasoning blocks | Zenginleştirme, reorganize |
| 10 | Temperature 0.0 çıkarma, 0.2 kod, 0.4 yaratıcı | Model-spesifik ayar |
