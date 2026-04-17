"""Metin -> Excel Araci -- serbest metinleri yapilandirilmis Excel'e donusturur."""
from typing import Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolInput, ToolResult
from ai.router import ModelRouter
from ai.pipeline import PipelineManager
from core.models import TaskType, ExtractionResult, FieldValue


class TextToExcelInput(ToolInput):
    """Metin -> Excel araci girdisi."""
    text: str = Field(description="Islenecek metin")
    data_schema: type[BaseModel] = Field(description="Hedef Pydantic semasi")
    business_context: dict = Field(default_factory=dict, description="Is baglami")
    text_type: str = Field(default="freeform", description="Metin tipi: freeform, csv, json, email, chat")


class TextToExcelTool(BaseTool):
    """
    Metin -> Excel Araci

    Kullanim senaryolari:
    - Serbest metin aciklamalari -> Excel
    - E-posta icerigi -> yapilandirilmis veri
    - WhatsApp/mesaj metinleri -> Excel
    - Kopyala-yapistir web tablolari -> Excel
    - CSV/TSV verisi -> formatlanmis Excel
    - JSON verisi -> Excel

    Ozellikler:
    - Otomatik format tespiti (CSV, JSON, serbest metin)
    - Birden fazla kayit iceren metinleri ayristirma
    - "Bunu da ekle" destegi (mevcut veriye satir ekleme)
    """

    def __init__(self, router: ModelRouter):
        super().__init__(
            name="Metin -> Excel",
            description="Serbest metin veya yapilandirilmis metinleri Excel'e donusturur"
        )
        self.router = router
        self.pipeline = PipelineManager(router)

    def process(
        self,
        input_data: TextToExcelInput,
        **kwargs
    ) -> ToolResult:
        """
        Ana isleme akisi.

        ADIM 1: Format tespiti
        ADIM 2: Uygun modeli sec (basit -> Gemini, karmasik -> Claude)
        ADIM 3: Metni parse et ve yapilandir
        ADIM 4: Onizleme olustur
        """
        try:
            # Format tespiti
            detected_format = self._detect_format(input_data.text)

            # Basit formatlar (CSV, JSON) icin Gemini yeterli
            if detected_format in ["csv", "json"]:
                task_type = TaskType.SIMPLE_TRANSFORM
            else:
                task_type = TaskType.EXTRACTION

            # Prompt olustur
            prompt = self._build_extraction_prompt(
                input_data.text,
                detected_format,
                input_data.data_schema,
                input_data.business_context
            )

            # AI ile cikarma
            adapter = self.router.select_model(task_type)
            response = adapter.extract(
                prompt=prompt,
                schema=input_data.data_schema,
            )

            # ExtractionResult olustur
            extraction_result = ExtractionResult(
                fields={k: FieldValue(value=v, confidence=0.85) for k, v in response.structured_data.items()},
                model_used=response.model,
                confidence_avg=0.85,
            )

            # Onizleme
            preview_data = self._create_preview(extraction_result)

            return ToolResult(
                success=True,
                extraction_result=extraction_result,
                preview_data=preview_data,
                message=f"Metin basariyla islendi. Format: {detected_format}",
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                message="Metin isleme basarisiz",
                errors=[str(e)],
            )

    def process_batch(
        self,
        texts: list[str],
        schema: type[BaseModel],
        business_context: dict,
        **kwargs
    ) -> list[ToolResult]:
        """
        Coklu metin toplu isleme.

        Kullanim: Birden fazla e-posta, mesaj veya not
        """
        results = []

        for i, text in enumerate(texts):
            input_data = TextToExcelInput(
                text=text,
                data_schema=schema,
                business_context=business_context,
            )

            result = self.process(input_data)
            result.message = f"Metin {i+1}/{len(texts)}: {result.message}"
            results.append(result)

        return results

    def preview(self, result: ToolResult) -> dict:
        """Streamlit icin onizleme verisi."""
        if not result.extraction_result:
            return {}
        return result.preview_data

    def _detect_format(self, text: str) -> str:
        """
        Metin formatini otomatik tespit et.

        Returns:
            "csv", "json", "freeform", "table", "list"
        """
        text_stripped = text.strip()

        # JSON tespiti
        if (text_stripped.startswith("{") and text_stripped.endswith("}")) or \
           (text_stripped.startswith("[") and text_stripped.endswith("]")):
            return "json"

        # CSV/TSV tespiti (tab veya virgul ile ayrilmis)
        lines = text_stripped.split('\n')
        if len(lines) > 1:
            first_line = lines[0]
            if '\t' in first_line or ',' in first_line:
                # Ikinci satirda da ayni ayirici var mi?
                second_line = lines[1] if len(lines) > 1 else ""
                if ('\t' in second_line) or (',' in second_line):
                    return "csv"

        # Liste tespiti (satir baslarinda -, *, vb.)
        if any(line.strip().startswith(('-', '*')) for line in lines):
            return "list"

        # Tablo tespiti (| karakteri)
        if '|' in text and len(lines) > 2:
            return "table"

        # Varsayilan: serbest metin
        return "freeform"

    def _build_extraction_prompt(
        self,
        text: str,
        format_type: str,
        schema: type[BaseModel],
        context: dict
    ) -> str:
        """Metin cikarma promptu olustur."""

        format_hints = {
            "csv": "Bu CSV/TSV formatinda veri. Her satir bir kayit.",
            "json": "Bu JSON formatinda veri. Parse et ve semaya uyarla.",
            "freeform": "Bu serbest metin. Icindeki bilgiyi cikar ve yapilandir.",
            "table": "Bu tablo formatinda veri. Sutunlari ve satirlari ayikla.",
            "list": "Bu liste formatinda veri. Her maddeyi ayri kayit olarak isle.",
        }

        prompt = f"""
Asagidaki metni analiz et ve yapilandirilmis veriye donustur.

<text>
{text}
</text>

<format_hint>
{format_hints.get(format_type, "Metin formatini otomatik tespit et.")}
</format_hint>

<target_schema>
{schema.model_json_schema()}
</target_schema>

<business_context>
{context}
</business_context>

<instructions>
1. Metni dikkatlice oku
2. Ilgili bilgileri cikar
3. Hedef semaya uygun formata donustur
4. Eksik alanlari null olarak birak
5. Sayilari number tipinde dondur
6. Tarihleri YYYY-MM-DD formatinda dondur
</instructions>

Yapilandirilmis veriyi dondur:
"""
        return prompt

    def _create_preview(self, extraction_result: ExtractionResult) -> dict:
        """Onizleme tablosu olustur."""
        rows = []

        for field_name, field_value in extraction_result.fields.items():
            rows.append({
                "Alan": field_name,
                "Deger": str(field_value.value),
                "Guven": f"{field_value.confidence:.0%}",
            })

        return {
            "headers": ["Alan", "Deger", "Guven"],
            "rows": rows,
        }

    @property
    def tool_type(self) -> str:
        return "text_to_excel"


# Yardimci fonksiyonlar

def quick_text_to_excel(
    text: str,
    router: ModelRouter,
    schema: type[BaseModel],
    context: dict = None
) -> ToolResult:
    """Hizli metin -> Excel donusumu."""
    tool = TextToExcelTool(router)
    return tool.process(TextToExcelInput(
        text=text,
        data_schema=schema,
        business_context=context or {}
    ))
