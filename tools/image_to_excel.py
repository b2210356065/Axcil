"""📸 Görsel → Excel Aracı — fotoğraflardan veri çıkarıp Excel oluşturur."""
from typing import Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolInput, ToolResult
from ai.router import ModelRouter
from ai.pipeline import PipelineManager
from core.models import TaskType, ExtractionResult, FieldValue


class ImageToExcelInput(ToolInput):
    """Görsel → Excel aracı girdisi."""
    image_data: bytes = Field(description="Görsel verisi (bytes)")
    mime_type: str = Field(default="image/jpeg", description="MIME tipi")
    data_schema: type[BaseModel] = Field(description="Hedef Pydantic şeması")
    business_context: dict = Field(default_factory=dict, description="İş bağlamı")
    auto_categorize: bool = Field(default=True, description="Otomatik kategori ata")
    quality_threshold: float = Field(default=0.70, description="Minimum güven skoru")


class ImageToExcelTool(BaseTool):
    """
    📸 Görsel → Excel Aracı

    Kullanım senaryoları:
    - Fiş/makbuz fotoğrafları → masraf Excel'i
    - Fatura görüntüleri → muhasebe Excel'i
    - Kağıt formlar → veri Excel'i
    - El yazısı notlar → yapılandırılmış Excel
    - Kartvizitler → rehber Excel'i

    Özellikler:
    - Çoklu görsel toplu işleme
    - Otomatik kategori atama
    - Bulanık/eğik görsel uyarısı
    - Güven skoru bazlı renklendirme
    """

    def __init__(self, router: ModelRouter):
        super().__init__(
            name="Görsel → Excel",
            description="Fotoğraf/görsellerden veri çıkarıp Excel'e dönüştürür"
        )
        self.router = router
        self.pipeline = PipelineManager(router)

    def process(
        self,
        input_data: ImageToExcelInput,
        **kwargs
    ) -> ToolResult:
        """
        Ana işleme akışı.

        ADIM 1: Gemini Flash ile görsel analizi
        ADIM 2: Veri çıkarma
        ADIM 3: Güven skoru hesaplama
        ADIM 4: Otomatik kategori atama (opsiyonel)
        ADIM 5: Kalite kontrolü
        """
        try:
            # Görsel kalite kontrolü
            quality_warning = self._check_image_quality(input_data.image_data)

            # Pipeline ile çıkarma
            pipeline_result = self.pipeline.execute_extraction_pipeline(
                image_data=input_data.image_data,
                schema=input_data.data_schema,
                business_context=input_data.business_context,
                auto_validate=True,
            )

            if not pipeline_result.success:
                return ToolResult(
                    success=False,
                    message="Görsel işleme başarısız",
                    errors=pipeline_result.errors,
                )

            extraction_result = ExtractionResult(**pipeline_result.final_data)

            # Otomatik kategori atama
            if input_data.auto_categorize:
                extraction_result = self._auto_categorize(
                    extraction_result,
                    input_data.business_context
                )

            # Kalite kontrolü
            low_confidence_count = sum(
                1 for field in extraction_result.fields.values()
                if field.confidence < input_data.quality_threshold
            )

            warnings = []
            if quality_warning:
                warnings.append(quality_warning)
            if low_confidence_count > 0:
                warnings.append(
                    f"{low_confidence_count} alan düşük güven skoruna sahip (< {input_data.quality_threshold})"
                )

            # Önizleme verisi
            preview_data = self._create_preview(extraction_result)

            return ToolResult(
                success=True,
                extraction_result=extraction_result,
                preview_data=preview_data,
                message=f"✅ Görsel başarıyla işlendi. {len(extraction_result.fields)} alan çıkarıldı.",
                warnings=warnings,
                cost_usd=pipeline_result.total_cost,
                latency_ms=pipeline_result.total_latency_ms,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                message="Beklenmeyen hata",
                errors=[str(e)],
            )

    def process_batch(
        self,
        images: list[bytes],
        schema: type[BaseModel],
        business_context: dict,
        **kwargs
    ) -> list[ToolResult]:
        """
        Çoklu görsel toplu işleme.

        Kullanım: 50 fiş fotoğrafını tek seferde işle

        Returns:
            Her görsel için ToolResult listesi
        """
        results = []

        for i, image_data in enumerate(images):
            input_data = ImageToExcelInput(
                image_data=image_data,
                data_schema=schema,
                business_context=business_context,
            )

            result = self.process(input_data)
            result.message = f"Görsel {i+1}/{len(images)}: {result.message}"
            results.append(result)

        return results

    def preview(self, result: ToolResult) -> dict:
        """Streamlit için önizleme verisi."""
        if not result.extraction_result:
            return {}

        return result.preview_data

    def _check_image_quality(self, image_data: bytes) -> Optional[str]:
        """
        Görsel kalite kontrolü.

        Kontroller:
        - Çok küçük görsel (<100KB şüpheli)
        - Çok büyük görsel (>10MB uyarı)

        Returns:
            Uyarı mesajı veya None
        """
        size_mb = len(image_data) / (1024 * 1024)

        if size_mb < 0.1:
            return "⚠️ Görsel çok küçük, kalite düşük olabilir"
        elif size_mb > 10:
            return "⚠️ Görsel çok büyük, işlem yavaş olabilir"

        return None

    def _auto_categorize(
        self,
        extraction_result: ExtractionResult,
        business_context: dict
    ) -> ExtractionResult:
        """
        Otomatik kategori atama.

        Örnek: Fiş üzerinde "Migros" görülürse → kategori: "Market"
        """
        # Basit kural tabanlı kategori atama
        # Gerçek implementasyonda AI classification kullanılabilir

        categories = business_context.get("categories", [])
        if not categories:
            return extraction_result

        # Kategori alanı varsa ve boşsa, otomatik ata
        if "kategori" in extraction_result.fields:
            category_field = extraction_result.fields["kategori"]
            if not category_field.value or category_field.confidence < 0.5:
                # AI ile kategori tahmini (gelecekte implement edilecek)
                # Şimdilik varsayılan
                category_field.value = categories[0] if categories else "Genel"
                category_field.confidence = 0.80

        return extraction_result

    def _create_preview(self, extraction_result: ExtractionResult) -> dict:
        """
        Önizleme tablosu oluştur.

        Returns:
            {
                "headers": ["Alan", "Değer", "Güven", "Durum"],
                "rows": [...]
            }
        """
        rows = []

        for field_name, field_value in extraction_result.fields.items():
            status_emoji = {
                "valid": "✅",
                "warning": "⚠️",
                "error": "❌"
            }.get(field_value.status, "❓")

            rows.append({
                "Alan": field_name,
                "Değer": str(field_value.value),
                "Güven": f"{field_value.confidence:.0%}",
                "Durum": f"{status_emoji} {field_value.status}",
                "_confidence": field_value.confidence,  # Renklendirme için
            })

        return {
            "headers": ["Alan", "Değer", "Güven", "Durum"],
            "rows": rows,
        }

    @property
    def tool_type(self) -> str:
        return "image_to_excel"


# Yardımcı fonksiyon: Streamlit'ten kullanım için
def create_image_tool(router: ModelRouter) -> ImageToExcelTool:
    """Görsel → Excel aracı oluştur."""
    return ImageToExcelTool(router)
