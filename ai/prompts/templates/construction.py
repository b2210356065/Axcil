"""İnşaat sektörü prompt şablonları."""


class ConstructionPrompts:
    """İnşaat işlemleri için özelleştirilmiş promptlar."""

    DOMAIN_KNOWLEDGE = """
<construction_domain_knowledge>
POZ SİSTEMİ:
- Poz: Yapı işlerinde birim fiyat teklif sistemi
- Her iş kalemi bir poz numarasına sahip
- Örnek: 03.450/P - Beton Dökümü C25/30

İŞ KALEMLERİ:
- Hafriyat (m3)
- Beton (m3)
- Demir (kg/ton)
- Duvar (m2)
- Sıva (m2)
- Boyama (m2)
- Döşeme (m2)

METRAJ HESAPLAMA:
- Alan: Uzunluk x Genişlik (m2)
- Hacim: Uzunluk x Genişlik x Yükseklik (m3)
- Fire payı: Genelde %5-10 eklenir
</construction_domain_knowledge>
"""

    @staticmethod
    def site_report_extraction() -> str:
        """Saha raporu çıkarma."""
        return """
<task>
Şantiye günlük raporu. İşçilik, malzeme, ilerleme bilgilerini çıkar.
</task>

<required_fields>
1. Tarih
2. Proje Adı/Kodu
3. Hava Durumu
4. İşçi Sayıları:
   - Usta
   - Kalfa
   - İşçi
   - Toplam
5. Yapılan İşler (detaylı)
6. Kullanılan Malzemeler (miktar + birim)
7. İlerleme Yüzdesi (%)
8. Sorunlar/Aksaklıklar (varsa)
9. Ertesi Gün Planı
</required_fields>

<extraction_hints>
- El yazısı olabilir, dikkatli oku
- Sayılar rakam veya yazı ile olabilir ("üç usta" → 3)
- Malzeme miktarları: "50 torba çimento" → miktar:50, birim:torba, malzeme:çimento
</extraction_hints>

JSON formatında döndür.
"""

    @staticmethod
    def metraj_extraction() -> str:
        """Metraj çıkarma."""
        return """
<task>
Metraj cetveli. Her iş kalemi için miktar bilgilerini çıkar.
</task>

<required_fields>
1. Poz No (varsa)
2. İş Kalemi Açıklaması
3. Birim (m2, m3, kg, adet, vb.)
4. Miktar
5. Birim Fiyat (varsa)
6. Toplam Tutar (Miktar x Birim Fiyat)
7. Yer/Lokasyon (varsa)
</required_fields>

<validation>
- Toplam = Miktar x Birim Fiyat (matematiksel kontrol)
- Birimler standart olmalı (m2, m3, kg, ton, adet)
- Miktarlar pozitif
</validation>

JSON formatında döndür.
"""
