"""Pydantic veri modelleri — tüm sistemin tek kaynak şema tanımları."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ModelProvider(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"


class TaskType(str, Enum):
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    SIMPLE_TRANSFORM = "simple_transform"
    COMPLEX_TRANSFORM = "complex_transform"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    ANOMALY_DETECTION = "anomaly_detection"


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    LIST = "list"
    IMAGE = "image"
    VOICE = "voice"
    SELECT = "select"


class ColumnType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    FORMULA = "formula"


class InputField(BaseModel):
    name: str
    type: FieldType = FieldType.TEXT
    description: str = ""
    required: bool = True
    options: list[str] = Field(default_factory=list)


class ExcelColumn(BaseModel):
    name: str
    type: ColumnType = ColumnType.TEXT
    description: str = ""


class ExcelSheet(BaseModel):
    name: str
    columns: list[ExcelColumn] = Field(default_factory=list)


class ExcelTemplate(BaseModel):
    sheets: list[ExcelSheet] = Field(default_factory=list)


class APIConfig(BaseModel):
    gemini_key: str = ""
    claude_key: str = ""
    openai_key: str = ""
    gemini_model: str = "models/gemini-3-flash-preview"
    claude_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o-mini"
    confidence_high: float = 0.90
    confidence_low: float = 0.70

    def available_providers(self) -> list[ModelProvider]:
        providers = []
        if self.gemini_key:
            providers.append(ModelProvider.GEMINI)
        if self.claude_key:
            providers.append(ModelProvider.CLAUDE)
        if self.openai_key:
            providers.append(ModelProvider.OPENAI)
        return providers


class FieldValue(BaseModel):
    value: Union[str, int, float, bool, date, datetime, Decimal, None]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def status(self) -> str:
        if self.confidence >= 0.90:
            return "valid"
        elif self.confidence >= 0.70:
            return "warning"
        return "error"


class ExtractionResult(BaseModel):
    fields: dict[str, FieldValue] = Field(default_factory=dict)
    raw_data: dict[str, Union[str, int, float, bool, list, dict, None]] = Field(default_factory=dict)
    model_used: str = ""
    confidence_avg: float = 0.0

    def model_post_init(self, __context: Any) -> None:
        if self.fields:
            self.confidence_avg = sum(f.confidence for f in self.fields.values()) / len(self.fields)


class ValidationIssue(BaseModel):
    field: str
    status: str  # "warning" | "error"
    message: str
    suggestion: str = ""


class ValidationResult(BaseModel):
    is_valid: bool = True
    issues: list[ValidationIssue] = Field(default_factory=list)
    corrected_data: dict[str, Union[str, int, float, bool, list, dict, None]] = Field(default_factory=dict)


class AIResponse(BaseModel):
    content: str
    structured_data: Optional[dict[str, Union[str, int, float, bool, list, dict, None]]] = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0


class PromptMetrics(BaseModel):
    model: str
    tool: str
    task_type: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    success: bool = True
    confidence_avg: float = 0.0
    user_corrections: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# Sektörel veri modelleri
class FaturaKalemi(BaseModel):
    urun: str = ""
    miktar: float = 0.0
    birim: str = "adet"
    birim_fiyat: Decimal = Decimal("0")
    toplam: Decimal = Decimal("0")


class FaturaVerisi(BaseModel):
    tarih: Optional[date] = None
    satici: str = ""
    fatura_no: str = ""
    kalemler: list[FaturaKalemi] = Field(default_factory=list)
    ara_toplam: Decimal = Decimal("0")
    kdv_orani: float = 0.20
    kdv: Decimal = Decimal("0")
    toplam: Decimal = Decimal("0")
    odeme_durumu: str = "Bekliyor"


class StokHareketi(BaseModel):
    tarih: Optional[date] = None
    islem_tipi: str = "Giriş"
    urun_kodu: str = ""
    urun_adi: str = ""
    miktar: float = 0.0
    birim: str = "adet"
    birim_fiyat: Decimal = Decimal("0")
    depo: str = "Ana Depo"
    aciklama: str = ""


class PuantajSatiri(BaseModel):
    sicil_no: str = ""
    ad_soyad: str = ""
    departman: str = ""
    normal_saat: float = 0.0
    mesai_saat: float = 0.0
    izin_gun: float = 0.0


class MasrafKaydi(BaseModel):
    tarih: Optional[date] = None
    satici: str = ""
    kategori: str = ""
    tutar: Decimal = Decimal("0")
    odeme_yontemi: str = ""
    not_: str = Field(default="", alias="not")
    vergi_indirilebilir: bool = False


# Zenginleştirilmiş İş Tanımı Modelleri

class EnrichedColumn(BaseModel):
    ad: str
    tip: str = "text"
    format: Optional[str] = None
    zorunlu: bool = True
    varsayilan: Optional[Any] = None
    formul: Optional[str] = None
    dogrulama: Optional[str] = None
    aciklama: str = ""

class EnrichedDefinition(BaseModel):
    is_ozeti: str = ""
    sutunlar: list[EnrichedColumn] = Field(default_factory=list)
    is_kurallari: list[str] = Field(default_factory=list)
    sunum: dict = Field(default_factory=dict)
    senaryolar: list[dict] = Field(default_factory=list)

class AlgorithmResult(BaseModel):
    status: str  # "success" | "failure"
    code: Optional[str] = None
    test_summary: Optional[dict] = None
    basarisiz_testler: Optional[list[dict]] = None
    oneri: Optional[str] = None
    notlar: Optional[str] = None
    deneme_sayisi: int = 0

class RuntimeExtraction(BaseModel):
    key_column: Optional[str] = None
    key_values: list[str] = Field(default_factory=list)
    satirlar: list[dict] = Field(default_factory=list)
