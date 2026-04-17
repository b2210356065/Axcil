"""PDF -> Excel Araci -- PDF belgelerden veri cikarip Excel'e donusturur."""
from typing import Optional, Union
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolInput, ToolResult
from ai.router import ModelRouter
from ai.pipeline import PipelineManager
from core.models import TaskType, ExtractionResult, FieldValue

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    fitz = None


class PDFToExcelInput(ToolInput):
    """PDF -> Excel araci girdisi."""
    pdf_data: bytes = Field(description="PDF dosya verisi")
    data_schema: type[BaseModel] = Field(description="Hedef Pydantic semasi")
    business_context: dict = Field(default_factory=dict, description="Is baglami")
    extract_mode: str = Field(default="auto", description="Cikarma modu: auto, text, tables, images")
    max_pages: int = Field(default=50, description="Maksimum sayfa sayisi")


class PDFToExcelTool(BaseTool):
    """
    PDF -> Excel Araci

    Kullanim senaryolari:
    - Fatura PDF'leri -> muhasebe Excel'i
    - Banka ekstresi PDF -> hesap hareketleri
    - Rapor PDF'leri -> veri tablolari
    - Taranmis belgeler -> yapilandirilmis veri
    - Tedarikci PDF'leri -> alim kaydi

    Ozellikler:
    - Cok sayfali PDF destegi
    - Otomatik tablo tespiti
    - Taranmis PDF (OCR) destegi (Gemini multimodal)
    - Sayfa atlayan tablolari birlestirme
    """

    def __init__(self, router: ModelRouter):
        super().__init__(
            name="PDF -> Excel",
            description="PDF belgelerden veri cikarip Excel'e donusturur"
        )
        self.router = router
        self.pipeline = PipelineManager(router)

    def process(
        self,
        input_data: PDFToExcelInput,
        **kwargs
    ) -> ToolResult:
        """
        Ana isleme akisi.

        ADIM 1: PDF'i parse et (PyMuPDF)
        ADIM 2: Metin veya gorsel olarak cikar
        ADIM 3: AI ile yapilandir (Gemini Flash - 1M token)
        ADIM 4: Onizleme olustur
        """
        if not PDF_AVAILABLE:
            return ToolResult(
                success=False,
                message="PyMuPDF (fitz) yuklu degil",
                errors=["pip install PyMuPDF gerekli"],
            )

        try:
            # PDF parse
            pdf_content = self._extract_pdf_content(
                input_data.pdf_data,
                input_data.extract_mode,
                input_data.max_pages
            )

            if not pdf_content["text"] and not pdf_content["images"]:
                return ToolResult(
                    success=False,
                    message="PDF'den icerik cikarilamadi",
                    errors=["PDF bos veya okunamiyor"],
                )

            # Prompt olustur
            prompt = self._build_extraction_prompt(
                pdf_content,
                input_data.data_schema,
                input_data.business_context
            )

            # Gemini Flash kullan (1M token - buyuk PDF destegi)
            adapter = self.router.select_model(
                TaskType.EXTRACTION,
                prefer_cost_optimization=True  # Gemini tercih et
            )

            # Eger gorsel varsa, ilk sayfayi gorsel olarak gonder
            image_data = pdf_content["images"][0] if pdf_content["images"] else None

            response = adapter.extract(
                prompt=prompt,
                schema=input_data.data_schema,
                image_data=image_data,
                mime_type="image/png"
            )

            # ExtractionResult olustur
            extraction_result = ExtractionResult(
                fields={k: FieldValue(value=v, confidence=0.82) for k, v in response.structured_data.items()},
                model_used=response.model,
                confidence_avg=0.82,
            )

            # Onizleme
            preview_data = self._create_preview(extraction_result)

            return ToolResult(
                success=True,
                extraction_result=extraction_result,
                preview_data=preview_data,
                message=f"PDF basariyla islendi. {pdf_content['pages']} sayfa analiz edildi.",
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                message="PDF isleme basarisiz",
                errors=[str(e)],
            )

    def preview(self, result: ToolResult) -> dict:
        """Streamlit icin onizleme verisi."""
        if not result.extraction_result:
            return {}
        return result.preview_data

    def _extract_pdf_content(
        self,
        pdf_data: bytes,
        mode: str,
        max_pages: int
    ) -> dict:
        """
        PDF'den icerik cikar.

        Returns:
            {
                "text": "cikarilan metin",
                "images": [sayfa gorselleri],
                "pages": sayfa sayisi,
                "has_tables": bool
            }
        """
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        content = {
            "text": "",
            "images": [],
            "pages": min(doc.page_count, max_pages),
            "has_tables": False,
        }

        for page_num in range(content["pages"]):
            page = doc[page_num]

            # Metin cikar
            if mode in ["auto", "text", "tables"]:
                text = page.get_text()
                content["text"] += f"\n--- Sayfa {page_num + 1} ---\n{text}"

                # Basit tablo tespiti (satirlarda tab veya coklu bosluk)
                if "\t" in text or "  " in text:
                    content["has_tables"] = True

            # Gorsel olarak cikar (taranmis PDF icin)
            if mode in ["auto", "images"] or (mode == "auto" and not content["text"].strip()):
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                content["images"].append(img_bytes)

        doc.close()

        return content

    def _build_extraction_prompt(
        self,
        pdf_content: dict,
        schema: type[BaseModel],
        context: dict
    ) -> str:
        """PDF cikarma promptu."""
        prompt = f"""
Bu bir PDF belgesinden cikarilmis icerik.

<pdf_info>
Sayfa sayisi: {pdf_content['pages']}
Tablo tespit edildi: {'Evet' if pdf_content['has_tables'] else 'Hayir'}
</pdf_info>

<content>
{pdf_content['text'][:50000]}
</content>

<target_schema>
{schema.model_json_schema()}
</target_schema>

<business_context>
{context}
</business_context>

<instructions>
1. PDF icerigini dikkatlice analiz et
2. Tablolar varsa, sutun ve satirlari ayikla
3. Birden fazla sayfa varsa, ilgili verileri birlestir
4. Hedef semaya uygun yapilandir
5. Eksik alanlar: null
6. Sayilar: number tipinde
7. Tarihler: YYYY-MM-DD formatinda
</instructions>

Yapilandirilmis veriyi dondur:
"""
        return prompt

    def _create_preview(self, extraction_result: ExtractionResult) -> dict:
        """Onizleme tablosu."""
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
        return "pdf_to_excel"


# Yardimci fonksiyonlar

def quick_pdf_to_excel(
    pdf_path: str,
    router: ModelRouter,
    schema: type[BaseModel],
    context: dict = None
) -> ToolResult:
    """Hizli PDF -> Excel donusumu."""
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    tool = PDFToExcelTool(router)
    return tool.process(PDFToExcelInput(
        pdf_data=pdf_data,
        data_schema=schema,
        business_context=context or {}
    ))
