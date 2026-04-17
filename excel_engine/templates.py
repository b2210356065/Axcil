"""Sektörel Excel şablon kütüphanesi."""
from typing import Optional
from pydantic import BaseModel, Field
from core.models import ColumnType, ExcelColumn, ExcelSheet, ExcelTemplate


class TemplateLibrary:
    """
    Sektörel Excel şablonları.

    Her sektör için önceden tanımlanmış şablonlar:
    - Muhasebe (fatura, fiş, banka)
    - Stok/Depo (envanter, irsaliye)
    - İK/Bordro (puantaj, izin)
    - İnşaat (saha raporu, metraj)
    - Perakende (satış, kasa)
    - Sağlık (hasta kayıt, faturalama)
    """

    @staticmethod
    def get_template(sector: str, template_name: str) -> Optional[ExcelTemplate]:
        """
        Şablon al.

        Args:
            sector: Sektör adı (accounting, inventory, hr, construction, vb.)
            template_name: Şablon adı

        Returns:
            ExcelTemplate veya None
        """
        templates = {
            "accounting": TemplateLibrary._accounting_templates(),
            "inventory": TemplateLibrary._inventory_templates(),
            "hr": TemplateLibrary._hr_templates(),
            "construction": TemplateLibrary._construction_templates(),
            "retail": TemplateLibrary._retail_templates(),
            "healthcare": TemplateLibrary._healthcare_templates(),
        }

        sector_templates = templates.get(sector, {})
        return sector_templates.get(template_name)

    @staticmethod
    def list_templates(sector: Optional[str] = None) -> dict[str, list[str]]:
        """
        Mevcut şablonları listele.

        Returns:
            {"sector": ["template1", "template2"]}
        """
        all_templates = {
            "accounting": list(TemplateLibrary._accounting_templates().keys()),
            "inventory": list(TemplateLibrary._inventory_templates().keys()),
            "hr": list(TemplateLibrary._hr_templates().keys()),
            "construction": list(TemplateLibrary._construction_templates().keys()),
            "retail": list(TemplateLibrary._retail_templates().keys()),
            "healthcare": list(TemplateLibrary._healthcare_templates().keys()),
        }

        if sector:
            return {sector: all_templates.get(sector, [])}

        return all_templates

    # Muhasebe şablonları
    @staticmethod
    def _accounting_templates() -> dict[str, ExcelTemplate]:
        """Muhasebe sektörü şablonları."""
        return {
            "fatura": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Faturalar",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Satıcı", type=ColumnType.TEXT),
                        ExcelColumn(name="Fatura No", type=ColumnType.TEXT),
                        ExcelColumn(name="Açıklama", type=ColumnType.TEXT),
                        ExcelColumn(name="Kategori", type=ColumnType.TEXT),
                        ExcelColumn(name="Ara Toplam", type=ColumnType.CURRENCY),
                        ExcelColumn(name="KDV", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Toplam", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Ödeme Durumu", type=ColumnType.TEXT),
                    ]
                )]
            ),
            "masraf": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Masraflar",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Satıcı", type=ColumnType.TEXT),
                        ExcelColumn(name="Kategori", type=ColumnType.TEXT),
                        ExcelColumn(name="Tutar", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Ödeme Yöntemi", type=ColumnType.TEXT),
                        ExcelColumn(name="Vergi İndirilebilir", type=ColumnType.TEXT),
                        ExcelColumn(name="Not", type=ColumnType.TEXT),
                    ]
                )]
            ),
            "banka_ekstresi": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Banka Hareketleri",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Açıklama", type=ColumnType.TEXT),
                        ExcelColumn(name="Giden", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Gelen", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Bakiye", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Kategori", type=ColumnType.TEXT),
                    ]
                )]
            ),
        }

    # Stok/Depo şablonları
    @staticmethod
    def _inventory_templates() -> dict[str, ExcelTemplate]:
        """Stok/Depo sektörü şablonları."""
        return {
            "stok_hareketi": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Stok Hareketleri",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="İşlem Tipi", type=ColumnType.TEXT),
                        ExcelColumn(name="Ürün Kodu", type=ColumnType.TEXT),
                        ExcelColumn(name="Ürün Adı", type=ColumnType.TEXT),
                        ExcelColumn(name="Miktar", type=ColumnType.NUMBER),
                        ExcelColumn(name="Birim", type=ColumnType.TEXT),
                        ExcelColumn(name="Birim Fiyat", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Depo", type=ColumnType.TEXT),
                        ExcelColumn(name="Açıklama", type=ColumnType.TEXT),
                    ]
                )]
            ),
            "envanter": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Envanter",
                    columns=[
                        ExcelColumn(name="SKU", type=ColumnType.TEXT),
                        ExcelColumn(name="Ürün", type=ColumnType.TEXT),
                        ExcelColumn(name="Kategori", type=ColumnType.TEXT),
                        ExcelColumn(name="Mevcut Stok", type=ColumnType.NUMBER),
                        ExcelColumn(name="Minimum Stok", type=ColumnType.NUMBER),
                        ExcelColumn(name="Birim Fiyat", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Toplam Değer", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Lokasyon", type=ColumnType.TEXT),
                    ]
                )]
            ),
        }

    # İK/Bordro şablonları
    @staticmethod
    def _hr_templates() -> dict[str, ExcelTemplate]:
        """İK/Bordro sektörü şablonları."""
        return {
            "puantaj": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Puantaj",
                    columns=[
                        ExcelColumn(name="Sicil No", type=ColumnType.TEXT),
                        ExcelColumn(name="Ad Soyad", type=ColumnType.TEXT),
                        ExcelColumn(name="Departman", type=ColumnType.TEXT),
                        ExcelColumn(name="Normal Saat", type=ColumnType.NUMBER),
                        ExcelColumn(name="Mesai Saat", type=ColumnType.NUMBER),
                        ExcelColumn(name="İzin (Gün)", type=ColumnType.NUMBER),
                        ExcelColumn(name="Toplam Saat", type=ColumnType.NUMBER),
                        ExcelColumn(name="Ücret", type=ColumnType.CURRENCY),
                    ]
                )]
            ),
            "izin_takip": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="İzin Kayıtları",
                    columns=[
                        ExcelColumn(name="Sicil No", type=ColumnType.TEXT),
                        ExcelColumn(name="Ad Soyad", type=ColumnType.TEXT),
                        ExcelColumn(name="İzin Tipi", type=ColumnType.TEXT),
                        ExcelColumn(name="Başlangıç", type=ColumnType.DATE),
                        ExcelColumn(name="Bitiş", type=ColumnType.DATE),
                        ExcelColumn(name="Gün Sayısı", type=ColumnType.NUMBER),
                        ExcelColumn(name="Durum", type=ColumnType.TEXT),
                    ]
                )]
            ),
        }

    # İnşaat şablonları
    @staticmethod
    def _construction_templates() -> dict[str, ExcelTemplate]:
        """İnşaat sektörü şablonları."""
        return {
            "saha_raporu": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Saha Raporu",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Proje", type=ColumnType.TEXT),
                        ExcelColumn(name="İşçi Sayısı", type=ColumnType.NUMBER),
                        ExcelColumn(name="Yapılan İş", type=ColumnType.TEXT),
                        ExcelColumn(name="Kullanılan Malzeme", type=ColumnType.TEXT),
                        ExcelColumn(name="İlerleme (%)", type=ColumnType.PERCENTAGE),
                        ExcelColumn(name="Sorunlar", type=ColumnType.TEXT),
                    ]
                )]
            ),
            "metraj": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Metraj",
                    columns=[
                        ExcelColumn(name="Poz No", type=ColumnType.TEXT),
                        ExcelColumn(name="İş Kalemi", type=ColumnType.TEXT),
                        ExcelColumn(name="Birim", type=ColumnType.TEXT),
                        ExcelColumn(name="Miktar", type=ColumnType.NUMBER),
                        ExcelColumn(name="Birim Fiyat", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Toplam", type=ColumnType.CURRENCY),
                    ]
                )]
            ),
        }

    # Perakende şablonları
    @staticmethod
    def _retail_templates() -> dict[str, ExcelTemplate]:
        """Perakende sektörü şablonları."""
        return {
            "satis": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Satışlar",
                    columns=[
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Fiş No", type=ColumnType.TEXT),
                        ExcelColumn(name="Ürün", type=ColumnType.TEXT),
                        ExcelColumn(name="Miktar", type=ColumnType.NUMBER),
                        ExcelColumn(name="Birim Fiyat", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Toplam", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Ödeme Tipi", type=ColumnType.TEXT),
                    ]
                )]
            ),
        }

    # Sağlık şablonları
    @staticmethod
    def _healthcare_templates() -> dict[str, ExcelTemplate]:
        """Sağlık sektörü şablonları."""
        return {
            "hasta_kayit": ExcelTemplate(
                sheets=[ExcelSheet(
                    name="Hasta Kayıtları",
                    columns=[
                        ExcelColumn(name="Hasta ID", type=ColumnType.TEXT),
                        ExcelColumn(name="Ad Soyad", type=ColumnType.TEXT),
                        ExcelColumn(name="Tarih", type=ColumnType.DATE),
                        ExcelColumn(name="Doktor", type=ColumnType.TEXT),
                        ExcelColumn(name="Tanı", type=ColumnType.TEXT),
                        ExcelColumn(name="Tedavi", type=ColumnType.TEXT),
                        ExcelColumn(name="Tutar", type=ColumnType.CURRENCY),
                        ExcelColumn(name="Sigorta", type=ColumnType.TEXT),
                    ]
                )]
            ),
        }


# Yardımcı fonksiyonlar

def get_template_for_sector(sector: str, default: str = "fatura") -> ExcelTemplate:
    """
    Sektör için varsayılan şablonu al.

    Args:
        sector: Sektör adı
        default: Varsayılan şablon adı

    Returns:
        ExcelTemplate
    """
    lib = TemplateLibrary()
    template = lib.get_template(sector, default)

    if not template:
        # Fallback: genel fatura şablonu
        template = lib.get_template("accounting", "fatura")

    return template
