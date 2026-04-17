"""Soyut araç arayüzü — tüm araçların uyması gereken temel yapı."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field
from core.models import ExtractionResult


class ToolInput(BaseModel):
    """Araç girdisi — her araç kendi input modelini tanımlar."""
    pass


class ToolResult(BaseModel):
    """Araç sonucu — standart çıktı formatı."""
    success: bool
    extraction_result: Optional[ExtractionResult] = None
    excel_path: Optional[str] = None
    preview_data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


class BaseTool(ABC):
    """
    Tüm araçların uyması gereken temel arayüz.

    Her araç şu akışı takip eder:
    1. Girdi alma
    2. AI ile işleme (extract/transform)
    3. Önizleme oluşturma
    4. Kullanıcı onayı
    5. Excel üretimi
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def process(self, input_data: ToolInput, **kwargs) -> ToolResult:
        """
        Ana işleme fonksiyonu.

        Args:
            input_data: Araç girdisi
            **kwargs: Ekstra parametreler

        Returns:
            ToolResult
        """
        pass

    @abstractmethod
    def preview(self, result: ToolResult) -> dict[str, Any]:
        """
        Önizleme verisi oluştur (Streamlit'te gösterilecek).

        Returns:
            Önizleme için dictionary (tablo formatında)
        """
        pass

    @property
    @abstractmethod
    def tool_type(self) -> str:
        """Araç tipi identifier."""
        pass
