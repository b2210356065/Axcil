"""Ses -> Excel Araci -- sesli notlari Excel'e donusturur."""
from typing import Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolInput, ToolResult
from ai.router import ModelRouter
from ai.pipeline import PipelineManager
from core.models import TaskType, ExtractionResult, ModelProvider, FieldValue

try:
    import openai
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    openai = None


class VoiceToExcelInput(ToolInput):
    """Ses -> Excel araci girdisi."""
    audio_data: bytes = Field(description="Ses dosyasi verisi")
    audio_format: str = Field(default="mp3", description="Ses formati: mp3, wav, m4a, ogg")
    data_schema: type[BaseModel] = Field(description="Hedef Pydantic semasi")
    business_context: dict = Field(default_factory=dict, description="Is baglami")
    language: str = Field(default="tr", description="Dil kodu (tr, en, vb.)")


class VoiceToExcelTool(BaseTool):
    """
    Ses -> Excel Araci

    Kullanim senaryolari:
    - Saha muhendisi sesli rapor -> Excel
    - Satici toplanti notu -> yapilandirilmis veri
    - Depocu sesli sayim -> envanter Excel'i
    - Muhasebeci fis aciklamasi -> masraf kaydi
    - Doktor hasta notu -> hasta kaydi

    Ozellikler:
    - Whisper API ile transkripsiyon
    - Turkce ve 90+ dil destegi
    - Gemini Flash ile yapilandirma
    - Uzun ses kayitlari (25 MB'a kadar)

    Kullanim ornekleri:
    - "Bugun 3 usta 2 kalfa calisti, 50 torba cimento kullanildi"
      -> Insaat saha raporu Excel'i
    - "Mehmet Bey ile gorustum, 50 bin liralik teklif verdim"
      -> Satis pipeline Excel'i
    - "B-3 rafina 200 adet X urunu yerlestirildi"
      -> Stok hareketi Excel'i
    """

    def __init__(self, router: ModelRouter, openai_api_key: Optional[str] = None):
        super().__init__(
            name="Ses -> Excel",
            description="Sesli notlari transkript edip Excel'e donusturur"
        )
        self.router = router
        self.pipeline = PipelineManager(router)
        self.openai_api_key = openai_api_key

    def process(
        self,
        input_data: VoiceToExcelInput,
        **kwargs
    ) -> ToolResult:
        """
        Ana isleme akisi.

        ADIM 1: Whisper API ile transkripsiyon
        ADIM 2: Gemini Flash ile transkripti yapilandir
        ADIM 3: Onizleme olustur
        """
        if not WHISPER_AVAILABLE:
            return ToolResult(
                success=False,
                message="OpenAI paketi yuklu degil",
                errors=["pip install openai gerekli"],
            )

        if not self.openai_api_key:
            return ToolResult(
                success=False,
                message="OpenAI API key gerekli (Whisper icin)",
                errors=["OPENAI_API_KEY ayarlanmali"],
            )

        try:
            # ADIM 1: Transkripsiyon
            transcript = self._transcribe_audio(
                input_data.audio_data,
                input_data.audio_format,
                input_data.language
            )

            if not transcript:
                return ToolResult(
                    success=False,
                    message="Transkripsiyon basarisiz",
                    errors=["Ses dosyasi okunamadi veya bos"],
                )

            # ADIM 2: Yapilandirma (Gemini Flash - ucuz)
            prompt = self._build_structuring_prompt(
                transcript,
                input_data.data_schema,
                input_data.business_context
            )

            adapter = self.router.select_model(
                TaskType.EXTRACTION,
                prefer_cost_optimization=True
            )

            response = adapter.extract(
                prompt=prompt,
                schema=input_data.data_schema,
            )

            # ExtractionResult
            extraction_result = ExtractionResult(
                fields={k: FieldValue(value=v, confidence=0.80) for k, v in response.structured_data.items()},
                model_used=response.model,
                confidence_avg=0.80,
                raw_data={"transcript": transcript}
            )

            # Onizleme
            preview_data = self._create_preview(extraction_result)

            return ToolResult(
                success=True,
                extraction_result=extraction_result,
                preview_data=preview_data,
                message=f"Ses basariyla islendi. Transkript: {len(transcript)} karakter",
                cost_usd=response.cost_usd + 0.006,  # Whisper maliyeti (~$0.006/dakika)
                latency_ms=response.latency_ms,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                message="Ses isleme basarisiz",
                errors=[str(e)],
            )

    def preview(self, result: ToolResult) -> dict:
        """Streamlit icin onizleme verisi."""
        if not result.extraction_result:
            return {}

        # Transkripti de goster
        preview = result.preview_data.copy()
        if result.extraction_result.raw_data:
            transcript = result.extraction_result.raw_data.get("transcript", "")
            preview["transcript"] = transcript[:500]  # Ilk 500 karakter

        return preview

    def _transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> str:
        """
        Whisper API ile transkripsiyon.

        Returns:
            Transkript metni
        """
        client = openai.OpenAI(api_key=self.openai_api_key)

        # Gecici dosya (Whisper API file-like object bekliyor)
        import io
        audio_file = io.BytesIO(audio_data)
        audio_file.name = f"audio.{audio_format}"

        # Transkripsiyon
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text"
        )

        return transcript

    def _build_structuring_prompt(
        self,
        transcript: str,
        schema: type[BaseModel],
        context: dict
    ) -> str:
        """Transkript yapilandirma promptu."""
        prompt = f"""
Asagida bir sesli notun transkripti var. Icindeki bilgiyi yapilandirilmis veriye donustur.

<transcript>
{transcript}
</transcript>

<target_schema>
{schema.model_json_schema()}
</target_schema>

<business_context>
Is yeri: {context.get('business_name', 'Belirsiz')}
Sektor: {context.get('sector', 'Belirsiz')}
Kullanim senaryosu: {context.get('use_case', 'Genel veri girisi')}
</business_context>

<instructions>
1. Transkripti dikkatlice oku
2. Konusma dilindeki ifadeleri yapilandirilmis veriye cevir
3. Sayilari rakama donustur ("elli" -> 50)
4. Tarihleri tespit et ("bugun" -> bugunun tarihi)
5. Eksik alanlar: null
6. Hedef semaya uygun formatta dondur
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
        return "voice_to_excel"


# Yardimci fonksiyonlar

def quick_voice_to_excel(
    audio_path: str,
    router: ModelRouter,
    schema: type[BaseModel],
    openai_api_key: str,
    context: dict = None
) -> ToolResult:
    """Hizli ses -> Excel donusumu."""
    import os

    audio_format = os.path.splitext(audio_path)[1][1:]  # .mp3 -> mp3

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    tool = VoiceToExcelTool(router, openai_api_key)
    return tool.process(VoiceToExcelInput(
        audio_data=audio_data,
        audio_format=audio_format,
        data_schema=schema,
        business_context=context or {}
    ))
