"""Veri cikarma prompt sablonlari -- dort katmanli yapi."""
from typing import Any, Optional
from pydantic import BaseModel
from core.models import ModelProvider


# ---------------------------------------------------------------------------
# Sektorel few-shot ornekler
# ---------------------------------------------------------------------------

INVOICE_EXAMPLES = [
    {
        "input": "Fatura gorseli: ABC Ticaret Ltd., Fatura No: F-2025-0042, "
                 "Tarih: 15.03.2025, 5 adet Laptop 32000 TL, KDV %20 = 32000 TL, "
                 "Genel Toplam: 192000 TL",
        "output": {
            "tarih": "2025-03-15",
            "satici": "ABC Ticaret Ltd.",
            "fatura_no": "F-2025-0042",
            "kalemler": [
                {"urun": "Laptop", "miktar": 5, "birim": "adet",
                 "birim_fiyat": 32000, "toplam": 160000}
            ],
            "ara_toplam": 160000,
            "kdv_orani": 0.20,
            "kdv": 32000,
            "toplam": 192000,
            "odeme_durumu": "Bekliyor"
        }
    },
    {
        "input": "E-Fatura PDF: XYZ Gida A.S., No: EFT2025001234, "
                 "10.01.2025, 100 kg Un (12 TL/kg) + 50 lt Sut (28 TL/lt), "
                 "Ara Toplam 2600 TL, KDV %10 = 260 TL, Toplam 2860 TL, Odendi",
        "output": {
            "tarih": "2025-01-10",
            "satici": "XYZ Gida A.S.",
            "fatura_no": "EFT2025001234",
            "kalemler": [
                {"urun": "Un", "miktar": 100, "birim": "kg",
                 "birim_fiyat": 12, "toplam": 1200},
                {"urun": "Sut", "miktar": 50, "birim": "lt",
                 "birim_fiyat": 28, "toplam": 1400}
            ],
            "ara_toplam": 2600,
            "kdv_orani": 0.10,
            "kdv": 260,
            "toplam": 2860,
            "odeme_durumu": "Odendi"
        }
    },
]

RECEIPT_EXAMPLES = [
    {
        "input": "Fis: Migros, 20.02.2025, Ekmek 12.50, Sut 45.00, "
                 "Peynir 89.90, Toplam: 147.40 TL, Kredi Karti",
        "output": {
            "tarih": "2025-02-20",
            "satici": "Migros",
            "kategori": "Market",
            "tutar": 147.40,
            "odeme_yontemi": "Kredi Karti",
            "vergi_indirilebilir": False,
            "not": "Ekmek, Sut, Peynir"
        }
    },
]

INVENTORY_EXAMPLES = [
    {
        "input": "Irsaliye: 50 kutu Vida M8 (B-3 rafi), 20 adet Matkap Ucu "
                 "(A-1 rafi), 15.03.2025, Tedarikci: Demir A.S.",
        "output": {
            "tarih": "2025-03-15",
            "islem_tipi": "Giris",
            "hareketler": [
                {"urun_kodu": "", "urun_adi": "Vida M8", "miktar": 50,
                 "birim": "kutu", "depo": "B-3"},
                {"urun_kodu": "", "urun_adi": "Matkap Ucu", "miktar": 20,
                 "birim": "adet", "depo": "A-1"}
            ],
            "aciklama": "Tedarikci: Demir A.S."
        }
    },
]

# Senaryo -> ornek eslestirmesi
SECTOR_EXAMPLES = {
    "muhasebe": INVOICE_EXAMPLES,
    "fatura": INVOICE_EXAMPLES,
    "fis": RECEIPT_EXAMPLES,
    "masraf": RECEIPT_EXAMPLES,
    "stok": INVENTORY_EXAMPLES,
    "depo": INVENTORY_EXAMPLES,
    "envanter": INVENTORY_EXAMPLES,
}


class ExtractionPromptBuilder:
    """
    Veri cikarma promptlari olusturur.

    Dort Katmanli Yapi:
    1. SEMA TANIMI  -- Ciktinin JSON semasi
    2. ORNEK (Few-Shot) -- 2-3 tamamlanmis ornek
    3. IS KURALLARI -- Domain bilgisi ve kisitlar
    4. KALITE TALIMATLARI -- Hata yonetimi ve guven metrikleri
    """

    # ------------------------------------------------------------------
    # Ana prompt olusturucu
    # ------------------------------------------------------------------
    @staticmethod
    def build_basic_extraction(
        schema: type[BaseModel],
        business_context: dict[str, Any],
        examples: Optional[list[dict]] = None,
        custom_rules: Optional[list[str]] = None,
    ) -> str:
        """
        Temel veri cikarma promptu.

        Args:
            schema: Hedef Pydantic semasi
            business_context: Is baglami
            examples: Ornek girdi/cikti ciftleri
            custom_rules: Ozel is kurallari

        Returns:
            Tamamlanmis prompt
        """
        # ---- KATMAN 1: Sema tanimi ----
        schema_section = f"""<target_schema>
Ciktin su JSON semasina uygun olmalidir:

{schema.model_json_schema()}
</target_schema>"""

        # ---- KATMAN 2: Ornekler (Few-Shot) ----
        # Otomatik ornek secimi: oncelikle parametre ile gelen,
        # yoksa sektorden cikarim
        effective_examples = examples
        if not effective_examples:
            sector = (business_context.get("sector") or "").lower()
            for key, sector_examples in SECTOR_EXAMPLES.items():
                if key in sector:
                    effective_examples = sector_examples
                    break

        examples_section = ""
        if effective_examples and len(effective_examples) > 0:
            examples_section = "\n<examples>\n"
            for i, example in enumerate(effective_examples[:3], 1):
                examples_section += f"\nOrnek {i}:\n"
                examples_section += f"Girdi: {example.get('input', '')}\n"
                examples_section += f"Cikti: {example.get('output', '')}\n"
            examples_section += "</examples>\n"

        # ---- KATMAN 3: Is kurallari ----
        rules_section = ExtractionPromptBuilder._build_business_rules(
            business_context,
            custom_rules,
        )

        # ---- KATMAN 4: Kalite talimatlari ----
        quality_section = """<quality_instructions>
VERI CIKARMA KALITE KURALLARI:

1. Tum metin/gorsel icerigini dikkatlice oku, hicbir ogeyi atlama.
2. Sayisal degerleri number tipinde dondur (string degil).
   - Binlik ayirici (1.000 veya 1,000) varsa kaldir, saf sayi dondur.
   - Turkce ondalik ayirici virguldur: "3,50" -> 3.50
3. Tarih formati: YYYY-MM-DD (ciktida).
   - Turkce tarih girdi ornekleri: "15.03.2025", "15 Mart 2025", "2025-03-15"
   - Hepsini YYYY-MM-DD olarak dondur.
4. Para birimi: Varsayilan TL. Farkli para birimi gorursen acikca belirt.
5. Belirsiz degerler icin:
   {"value": "en iyi tahmin", "confidence": 0.5}
6. Bulunamayan / okunamayan alanlar: null
7. Her alan icin guven skoru ver (0.0-1.0):
   - 0.95+ : Kesinlikle dogru, net okunan deger
   - 0.85-0.94 : Cok yuksek guven, ufak belirsizlik
   - 0.70-0.84 : Yuksek guven ama dogrulama onerilir
   - 0.50-0.69 : Orta guven, kullanici kontrol etmeli
   - <0.50 : Belirsiz tahmin, muhtemelen hatali

KENDINI DOGRULAMA (Chain-of-Verification):
- Toplamlar: kalem toplami = ara_toplam oldugundan emin ol.
- KDV: ara_toplam * kdv_orani = kdv degerini dogrula.
- Genel toplam: ara_toplam + kdv = toplam oldugundan emin ol.
- Mantik: Gelecek tarih, negatif tutar, bos zorunlu alan varsa
  confidence'i dusur ve "warning" notu ekle.
</quality_instructions>"""

        # ---- Birlestir ----
        prompt = f"""Sen bir veri cikarma uzmanisin. Turkce ve Ingilizce kaynaklari analiz edip
yapilandirilmis JSON cikti uretiyorsun. Turkce karakterleri (c, g, i, o, s, u)
dogru kullan. Kisaltmalari ac (KDV = Katma Deger Vergisi, vb.).

{schema_section}

{examples_section}
{rules_section}
{quality_section}

Simdi verilen girdiyi isle ve JSON formatinda dondur.
"""
        return prompt

    # ------------------------------------------------------------------
    # Gorsel cikarma
    # ------------------------------------------------------------------
    @staticmethod
    def build_image_extraction(
        schema: type[BaseModel],
        business_context: dict[str, Any],
        image_type: str = "receipt",  # receipt, invoice, form, document
    ) -> str:
        """Gorsel cikarma icin ozel prompt."""

        type_hints = {
            "receipt": (
                "Bu bir fis/makbuz fotografi. Tum tutarlari, tarihi, "
                "saticiyi ve kalemleri cikar. Termal kagit solebilir, "
                "okunamayan kisimlar icin confidence dusur."
            ),
            "invoice": (
                "Bu bir fatura gorseli. Fatura no, tarih, satici bilgileri, "
                "kalemler (urun, miktar, birim fiyat, toplam), ara toplam, "
                "KDV ve genel toplami cikar. E-fatura ve kagit fatura "
                "formatlari farkli olabilir."
            ),
            "form": (
                "Bu doldurulmus bir form. Tum alanlari dikkatlice oku, "
                "el yazisi varsa ekstra dikkat goster. Isaretlenmis "
                "kutucuklari (checkbox) kontrol et."
            ),
            "document": (
                "Bu bir belge gorseli. Ilgili tum bilgileri cikar ve yapilandir."
            ),
        }

        image_hint = type_hints.get(image_type, type_hints["document"])

        base_prompt = ExtractionPromptBuilder.build_basic_extraction(
            schema=schema,
            business_context=business_context,
        )

        image_instructions = f"""<image_processing_instructions>
{image_hint}

Gorsel Kalite Kontrolleri:
- Bulanik/okunamaz gorsel: tum confidence skorlarini 0.2 dusur.
- El yazisi: daha dikkatli oku, belirsizliklerde confidence < 0.65.
- Egik/donuk gorsel: metni dogru yone cevirerek oku.
- Tablolar varsa: satir ve sutunlari dogru eslestir, satir atlama.
- Coklu para birimi varsa: her birimi acikca belirt.
- Turkce ozel karakterleri dogru cikar (C/c, G/g, I/i, O/o, S/s, U/u).
- Termal fislerde: solmus metin icin en iyi tahmini yap, dusuk confidence ile.
</image_processing_instructions>
"""

        return image_instructions + "\n" + base_prompt

    # ------------------------------------------------------------------
    # Coklu kaynak cikarma
    # ------------------------------------------------------------------
    @staticmethod
    def build_multimodal_extraction(
        schema: type[BaseModel],
        business_context: dict[str, Any],
        has_text: bool = True,
        has_image: bool = True,
        has_table: bool = False,
    ) -> str:
        """Coklu kaynak (metin + gorsel + tablo) cikarma."""

        multimodal_section = "<multimodal_processing>\n"
        multimodal_section += "Bu gorevde birden fazla veri kaynagi var:\n"

        if has_text:
            multimodal_section += (
                "- Metin icerigi: Dikkatlice oku, Turkce karakterleri koru.\n"
            )
        if has_image:
            multimodal_section += (
                "- Gorsel icerik: OCR ile metni cikar, tablolari tespit et.\n"
            )
        if has_table:
            multimodal_section += (
                "- Tablo yapisi: Satir ve sutunlari dogru eslestir, "
                "baslik satirini alanlarla esle.\n"
            )

        multimodal_section += """
Tum kaynaklardan gelen bilgileri birlestir ve tutarli tek bir cikti olustur.
Celiskili bilgi varsa:
  1. En guvenilir kaynak hangisi ise onu tercih et.
  2. Diger kaynagi "alternatif" olarak belirt.
  3. Celiskili alanlarda confidence skorunu 0.60 altina dusur.
</multimodal_processing>
"""

        base_prompt = ExtractionPromptBuilder.build_basic_extraction(
            schema=schema,
            business_context=business_context,
        )

        return multimodal_section + "\n" + base_prompt

    # ------------------------------------------------------------------
    # Is kurallari yardimcisi
    # ------------------------------------------------------------------
    @staticmethod
    def _build_business_rules(
        context: dict[str, Any],
        custom_rules: Optional[list[str]] = None,
    ) -> str:
        """Is kurallari bolumunu olustur."""
        section = "<business_rules>\n"

        if context.get("sector"):
            section += f"Sektor: {context['sector']}\n"

        if context.get("business_name"):
            section += f"Is yeri: {context['business_name']}\n"

        # Varsayilan kurallar
        default_rules = [
            "Tarihler DD.MM.YYYY veya YYYY-MM-DD formatinda olmali",
            "Para birimleri acikca belirtilmeli (TL, $, EUR)",
            "Sayisal degerler pozitif olmali (negatif deger anomali)",
            "Zorunlu alanlar bos birakilmamali",
            "Turkce buyuk I = I, kucuk i = i; buyuk I harfi dikkat (I vs I)",
            "KDV oranlari: %1, %10, %20 (Turkiye standart oranlari)",
        ]

        section += "\nGenel kurallar:\n"
        for rule in default_rules:
            section += f"- {rule}\n"

        # Sektorel ek kurallar
        sector = (context.get("sector") or "").lower()
        sector_rules = _get_sector_rules(sector)
        if sector_rules:
            section += "\nSektorel kurallar:\n"
            for rule in sector_rules:
                section += f"- {rule}\n"

        # Kullanici ozel kurallari
        if custom_rules:
            section += "\nOzel is kurallari:\n"
            for rule in custom_rules:
                section += f"- {rule}\n"

        section += "</business_rules>\n"
        return section

    # ------------------------------------------------------------------
    # Chain-of-Verification (CoVe) destegi
    # ------------------------------------------------------------------
    @staticmethod
    def build_with_cove(
        schema: type[BaseModel],
        business_context: dict[str, Any],
    ) -> tuple[str, list[str]]:
        """
        Chain-of-Verification (CoVe) promptu.

        Iki adimli surec:
        1. Ana cikarma promptu
        2. Dogrulama sorulari

        Returns:
            (extraction_prompt, verification_questions)
        """
        extraction_prompt = ExtractionPromptBuilder.build_basic_extraction(
            schema=schema,
            business_context=business_context,
        )

        # Dogrulama sorulari (semadan otomatik uret)
        verification_questions = []
        schema_props = schema.model_json_schema().get("properties", {})

        for field_name, field_info in schema_props.items():
            field_type = field_info.get("type", "unknown")

            if field_type == "number" or field_type == "integer":
                verification_questions.append(
                    f"'{field_name}' degeri mantikli mi? Normal aralikta mi? "
                    f"Negatif veya asiri buyuk deger yok mu?"
                )
            elif field_type == "string" and "date" in field_name.lower():
                verification_questions.append(
                    f"'{field_name}' gecerli bir tarih mi? "
                    f"Gelecek tarih degil mi? Format YYYY-MM-DD mi?"
                )
            elif "total" in field_name.lower() or "toplam" in field_name.lower():
                verification_questions.append(
                    f"'{field_name}' matematiksel olarak dogru hesaplanmis mi? "
                    f"Kalemlerin toplami ile uyumlu mu?"
                )
            elif "kdv" in field_name.lower() or "tax" in field_name.lower():
                verification_questions.append(
                    f"'{field_name}' degeri dogru KDV oranina (%1/%10/%20) gore "
                    f"hesaplanmis mi?"
                )
            elif field_type == "array":
                verification_questions.append(
                    f"'{field_name}' listesinde tum ogeler eksiksiz mi? "
                    f"Kaynak belgedeki sayi ile eslestiyor mu?"
                )

        return extraction_prompt, verification_questions


# ---------------------------------------------------------------------------
# Sektorel kural deposu
# ---------------------------------------------------------------------------

def _get_sector_rules(sector: str) -> list[str]:
    """Sektore ozel ek kurallar dondur."""
    rules_map = {
        "muhasebe": [
            "Fatura numarasi benzersiz olmali",
            "KDV orani: %1 (temel gida), %10 (bazi hizmetler), %20 (genel)",
            "Fatura tarihi gelecekte olamaz",
            "Ara toplam + KDV = Genel Toplam olmali",
            "Fatura/irsaliye ayrimi: belge tipini belirle",
        ],
        "stok": [
            "Stok miktari negatif olamaz (sifir olabilir)",
            "Birim standardizasyonu: adet, kutu, kg, lt, mt, m2, m3",
            "Depo/raf kodu formati: [Harf]-[Sayi] (ornegin B-3)",
            "Giris/cikis islem tipi belirtilmeli",
        ],
        "insan kaynaklari": [
            "Gunluk calisma suresi max 11 saat (yasal sinir)",
            "Haftalik calisma max 45 saat (normal), ustu mesai",
            "Mesai carpani: hafta ici 1.5x, hafta sonu 2x",
            "SGK prim orani: isveren %20.5, calisan %14",
            "AGI ve gelir vergisi dilimlerini dikkate al",
        ],
        "insaat": [
            "Birim fiyat pozlari: Cevre ve Sehircilik Bakanligi listesi referans",
            "Metraj birimleri: m, m2, m3, kg, ton, adet",
            "Is kalemi kodlari kontrol edilmeli",
            "Hakedis donemi belirtilmeli",
        ],
        "egitim": [
            "Not araligi: 0-100 (Turkiye sistemi)",
            "Harf notu: AA(90-100), BA(85-89), BB(80-84), CB(75-79), "
            "CC(70-74), DC(65-69), DD(60-64), FD(50-59), FF(0-49)",
            "Devamsizlik siniri: ders saatinin %30'u",
        ],
        "saglik": [
            "ICD-10 kodu formati: [Harf][2Sayi].[Sayi] (ornegin J06.9)",
            "SUT kodu kontrolu yapilmali",
            "Hasta TC kimlik 11 haneli olmali",
        ],
    }

    for key, rules in rules_map.items():
        if key in sector:
            return rules
    return []


# ---------------------------------------------------------------------------
# Yardimci fonksiyonlar
# ---------------------------------------------------------------------------

def quick_extraction_prompt(
    schema: type[BaseModel],
    context: dict = None,
    image_mode: bool = False,
) -> str:
    """Hizli prompt olustur."""
    if image_mode:
        return ExtractionPromptBuilder.build_image_extraction(
            schema=schema,
            business_context=context or {},
        )
    else:
        return ExtractionPromptBuilder.build_basic_extraction(
            schema=schema,
            business_context=context or {},
        )
