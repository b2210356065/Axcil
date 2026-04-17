"""Muhasebe sektörü özel prompt şablonları."""


class AccountingPrompts:
    """Muhasebe işlemleri için özelleştirilmiş promptlar."""

    # Sektörel domain bilgisi
    DOMAIN_KNOWLEDGE = """
<accounting_domain_knowledge>
TÜRK VERGİ SİSTEMİ:
- KDV oranları: %1 (temel gıda), %10 (kitap, eğitim), %20 (genel)
- Fatura zorunlu alanları: Tarih, Seri-No, Satıcı VKN, Alıcı VKN, Tutarlar
- e-Fatura: Elektronik fatura sistemi, standart XML formatı

FATURA TİPLERİ:
- Satış Faturası
- İade Faturası
- İhracat Faturası
- Tevkifatlı Fatura

FİŞ TİPLERİ:
- Perakende Satış Fişi
- Ödeme Kaydedici Fiş (EKAF)
- Serbest Meslek Makbuzu

MUHASEBEDEKİ HESAP PLANI:
- 100-199: Dönen Varlıklar
- 200-299: Duran Varlıklar
- 300-399: Kısa Vadeli Yabancı Kaynaklar
- 600-699: Gelir Hesapları
- 700-799: Maliyet Hesapları
</accounting_domain_knowledge>
"""

    VALIDATION_RULES = [
        "Fatura tarihi gelecek tarih olamaz",
        "KDV oranı %1, %10 veya %20 olmalı (Türkiye için)",
        "Ara Toplam + KDV = Genel Toplam (matematiksel tutarlılık)",
        "Fatura numarası boş olamaz",
        "Satıcı bilgisi zorunlu",
        "Tutarlar pozitif olmalı (iade faturası hariç)",
        "VKN (Vergi Kimlik Numarası) 10 haneli olmalı",
    ]

    @staticmethod
    def invoice_extraction() -> str:
        """Fatura çıkarma promptu."""
        return f"""
{AccountingPrompts.DOMAIN_KNOWLEDGE}

<task>
Bu bir fatura belgesi. Aşağıdaki bilgileri çıkar:
</task>

<required_fields>
ZORUNLU ALANLAR:
1. Fatura Numarası (Seri-No): Örnek "AAA2024000123"
2. Tarih: DD.MM.YYYY formatında
3. Satıcı Bilgileri:
   - Ünvan
   - Adres
   - VKN (10 haneli)
4. Alıcı Bilgileri (varsa)
5. Fatura Kalemleri:
   - Ürün/Hizmet Açıklaması
   - Miktar
   - Birim
   - Birim Fiyat
   - Tutar
6. Ara Toplam
7. KDV Oranı ve Tutarı
8. Genel Toplam
9. Ödeme Şekli (varsa): Nakit, Kredi Kartı, Havale, vb.

İSTEĞE BAĞLI ALANLAR:
- Sipariş No
- İrsaliye No
- Vade Tarihi
- Açıklamalar
</required_fields>

<extraction_hints>
- Fatura numarası genelde sol üst köşede, kalın yazı ile
- Tarih formatı DD.MM.YYYY veya DD/MM/YYYY olabilir
- KDV satırını "KDV", "KDVLI", "Katma Değer Vergisi" kelimeleri ile ara
- Toplam satırını "TOPLAM", "GENEL TOPLAM", "ÖDENECEK TUTAR" ile ara
- Tablo yapısındaki kalemleri dikkatle ayır
</extraction_hints>

<validation>
Çıkarma sonrası şu kontrolleri yap:
{chr(10).join(f"- {rule}" for rule in AccountingPrompts.VALIDATION_RULES)}
</validation>

JSON formatında döndür.
"""

    @staticmethod
    def receipt_extraction() -> str:
        """Fiş çıkarma promptu."""
        return f"""
{AccountingPrompts.DOMAIN_KNOWLEDGE}

<task>
Bu bir fiş/makbuz. Masraf kaydı için bilgileri çıkar.
</task>

<required_fields>
1. Tarih
2. Satıcı/İşletme Adı
3. Tutar (Toplam)
4. KDV Dahil mi? (Evet/Hayır)
5. Ödeme Yöntemi (varsa)
</required_fields>

<optional_fields>
- Fiş No
- Kalemler (eğer detay varsa)
- KDV Oranı ve Tutarı
- Kategori (otomatik tahmin et)
</optional_fields>

<category_inference>
Satıcı adına göre kategori tahmin et:
- Migros, Carrefour, BİM, A101 → Market
- Shell, BP, Opet → Akaryakıt
- Starbucks, Kahve Dünyası → Yemek/İçecek
- D&R, Pandora → Kırtasiye/Kitap
- Turkcell, Vodafone → İletişim
- Diğer → Genel
</category_inference>

<extraction_hints>
- Fişler genelde termal kağıt, düşük kalite olabilir
- Toplam tutar genelde en altta, büyük puntolu
- Tarih üstte, küçük punto
- Bazı fişlerde KDV ayrıştırılmış, bazılarında dahil
</extraction_hints>

JSON formatında döndür.
"""

    @staticmethod
    def bank_statement_extraction() -> str:
        """Banka ekstresi çıkarma promptu."""
        return """
<task>
Bu bir banka ekstresi/hesap özeti. Tüm hareketleri çıkar.
</task>

<required_fields_per_transaction>
1. Tarih
2. Açıklama/İşlem Detayı
3. Tutar (Giden/Gelen olarak ayır)
4. Bakiye (varsa)
5. İşlem Tipi: Havale, EFT, Pos, Çekim, vb.
</required_fields_per_transaction>

<extraction_strategy>
- Tablo formatındaki her satır bir işlemdir
- "Giden" ve "Gelen" sütunları varsa, negatif/pozitif olarak belirt
- Tarih formatını standartlaştır (YYYY-MM-DD)
- Tutarları number olarak döndür (virgülü noktaya çevir)
- Bakiye sütunu varsa, her işlem için kaydet
</extraction_strategy>

<validation>
- Matematiksel tutarlılık: Önceki Bakiye +/- İşlem = Yeni Bakiye
- Tarihler kronolojik sırada olmalı
- Tutarlar pozitif (yön bilgisi ayrıca)
</validation>

Her işlem için ayrı JSON objesi oluştur, liste olarak döndür.
"""

    @staticmethod
    def expense_categorization() -> str:
        """Masraf kategorizasyonu promptu."""
        return """
<task>
Verilen masraf kaydını doğru kategoriye ata.
</task>

<categories>
TÜRKİYE VERGİ İNDİRİM KATEGORİLERİ:
1. Ofis Malzemeleri (kırtasiye, yazıcı toner, vb.)
2. Ulaşım (akaryakıt, toplu taşıma, taksi)
3. Yemek & İçecek
4. İletişim (telefon, internet)
5. Kira & Faturalar (elektrik, su, doğalgaz)
6. Pazarlama & Reklam
7. Eğitim & Seminer
8. Danışmanlık & Profesyonel Hizmetler
9. Vergi & Resmi Ödemeler
10. Diğer İşletme Giderleri
</categories>

<tax_deductible_rules>
VERGİDEN İNDİRİLEBİLİR mi kontrol et:
- Fatura/fiş var mı?
- İş ile ilgili mi?
- Makul tutar sınırları içinde mi?
- Yasal gereklilikler karşılanıyor mu?

GENELDE İNDİRİLEMEZ:
- Kişisel harcamalar
- Cezalar, para cezaları
- Vergisi ödenmeyen
</tax_deductible_rules>

Kategori + vergi indirilebilir flag döndür.
"""


# Yardımcı fonksiyonlar

def get_accounting_prompt(prompt_type: str) -> str:
    """Muhasebe promptlarını al."""
    prompts = {
        "invoice": AccountingPrompts.invoice_extraction(),
        "receipt": AccountingPrompts.receipt_extraction(),
        "bank_statement": AccountingPrompts.bank_statement_extraction(),
        "categorization": AccountingPrompts.expense_categorization(),
    }
    return prompts.get(prompt_type, "")
