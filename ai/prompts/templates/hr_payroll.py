"""İK ve bordro sektörü prompt şablonları."""


class HRPayrollPrompts:
    """İK ve bordro işlemleri için özelleştirilmiş promptlar."""

    DOMAIN_KNOWLEDGE = """
<hr_payroll_domain_knowledge>
TÜRK İŞ HUKUKU:
- Haftalık çalışma: 45 saat (günlük 7.5-9 saat arası)
- Fazla mesai: Haftalık 45 saat üzeri, %50 zamlı
- Hafta sonu/tatil: %100 zamlı
- Yıllık izin: Kıdeme göre 14-26 gün

SGK PRİMLERİ (2024):
- İşçi payı: %14
- İşveren payı: %20.5
- Toplam: %34.5

GELİR VERGİSİ DİLİMLERİ:
- 0-70,000 TL: %15
- 70,001-150,000 TL: %20
- 150,001-550,000 TL: %27
- 550,001+ TL: %35
</hr_payroll_domain_knowledge>
"""

    @staticmethod
    def timesheet_extraction() -> str:
        """Puantaj çıkarma."""
        return """
<task>
Puantaj belgesi. Çalışma saatlerini çıkar.
</task>

<required_fields>
1. Sicil No / Personel ID
2. Ad Soyad
3. Departman
4. Tarih aralığı veya günlük detay
5. Normal Çalışma Saati
6. Fazla Mesai Saati
7. Hafta Sonu/Tatil Çalışması
8. İzin Günleri
9. Toplam Çalışma Saati
</required_fields>

<calculation_rules>
- Haftalık 45 saate kadar: Normal
- 45 saat üzeri: Fazla mesai (%50 zamlı)
- Hafta sonu/tatil: %100 zamlı
- İzinler çalışma saatinden düşülmeli
</calculation_rules>

JSON formatında döndür.
"""

    @staticmethod
    def payroll_calculation() -> str:
        """Bordro hesaplama."""
        return """
<task>
Bordro hesaplama. Brüt maaştan net maaş hesapla.
</task>

<calculation_steps>
1. Brüt Maaş (temel + primler + yan haklar)
2. SGK İşçi Payı Kesintisi (%14)
3. İşsizlik Sigortası İşçi Payı (%1)
4. Gelir Vergisi Matrahı = Brüt - SGK - İşsizlik
5. Gelir Vergisi (dilimler'e göre)
6. Damga Vergisi (%0.759)
7. NET MAAŞ = Brüt - (SGK + İşsizlik + GV + Damga)

İşveren maliyeti:
- SGK İşveren Payı (%20.5)
- İşsizlik İşveren (%2)
</calculation_steps>

JSON formatında hesaplamaları döndür.
"""
