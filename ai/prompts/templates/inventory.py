"""Stok/Depo yönetimi sektörü prompt şablonları."""


class InventoryPrompts:
    """Stok ve depo işlemleri için özelleştirilmiş promptlar."""

    DOMAIN_KNOWLEDGE = """
<inventory_domain_knowledge>
STOK YÖNETİMİ TERİMLERİ:
- SKU (Stock Keeping Unit): Ürün kodu
- Lot/Parti: Üretim partisi
- FIFO: First In First Out (İlk giren ilk çıkar)
- LIFO: Last In First Out (Son giren ilk çıkar)
- Reorder Point: Yeniden sipariş noktası
- Safety Stock: Güvenlik stoku

İŞLEM TİPLERİ:
- Giriş (Satın Alma, İade)
- Çıkış (Satış, Fire, İade)
- Transfer (Depo arası)
- Sayım (Envanter)
</inventory_domain_knowledge>
"""

    @staticmethod
    def stock_movement_extraction() -> str:
        """Stok hareketi çıkarma."""
        return """
<task>
Stok hareketi belgesi (irsaliye, sevk belgesi). Bilgileri çıkar.
</task>

<required_fields>
1. Tarih
2. İşlem Tipi (Giriş/Çıkış/Transfer)
3. Ürün Kodu (SKU)
4. Ürün Adı
5. Miktar
6. Birim (adet, kg, lt, m3, vb.)
7. Birim Fiyat (varsa)
8. Depo/Lokasyon
9. Belge No (irsaliye/sevk no)
</required_fields>

<extraction_hints>
- Tablo formatında ürünler listelenmiş olabilir
- Miktar ve birim birlikte yazılmış olabilir ("50 adet" → miktar:50, birim:adet)
- Lokasyon A-1, B-3 gibi kod olabilir
</extraction_hints>

JSON formatında döndür.
"""

    @staticmethod
    def inventory_count() -> str:
        """Envanter sayımı."""
        return """
<task>
Envanter sayım listesi. Her ürün için mevcut stok bilgisini çıkar.
</task>

<required_fields>
1. SKU
2. Ürün Adı
3. Kategori
4. Sayım Miktarı (fiziksel sayım)
5. Sistem Miktarı (varsa)
6. Fark (Sayım - Sistem)
7. Lokasyon
8. Son Sayım Tarihi
</required_fields>

<validation>
- Fark = Sayım - Sistem (matematiksel kontrol)
- Büyük farklar (>%10) uyarı ver
- Negatif stok olamaz
</validation>

JSON formatında döndür.
"""
