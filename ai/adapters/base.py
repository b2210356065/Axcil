"""Soyut model adaptör arayüzü — tüm AI provider'ları için ortak interface."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
from core.models import AIResponse, TaskType


class BaseModelAdapter(ABC):
    """Tüm AI model adaptörlerinin uyması gereken temel arayüz."""

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """API key ve model adını doğrula."""
        pass

    @abstractmethod
    def extract(
        self,
        prompt: str,
        schema: type[BaseModel],
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
    ) -> AIResponse:
        """
        Veri çıkarma — görsel/metin → yapılandırılmış JSON.

        Args:
            prompt: Çıkarma talimatları
            schema: Pydantic model (çıktı şeması)
            image_data: Opsiyonel görsel verisi
            mime_type: Görsel MIME tipi

        Returns:
            AIResponse with structured_data as dict
        """
        pass

    @abstractmethod
    def generate_code(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> AIResponse:
        """
        Kod üretimi — iş mantığı → Python/openpyxl kodu.

        Args:
            prompt: Kod üretme talimatları
            context: İş bağlamı (şablon, şema, örnekler)

        Returns:
            AIResponse with content as Python code string
        """
        pass

    @abstractmethod
    def validate(
        self,
        data: dict[str, Any],
        rules: list[str],
        context: dict[str, Any],
    ) -> AIResponse:
        """
        Veri doğrulama ve anomali tespiti.

        Args:
            data: Doğrulanacak veri
            rules: İş kuralları
            context: İş bağlamı

        Returns:
            AIResponse with structured_data as validation result
        """
        pass

    @abstractmethod
    def classify(
        self,
        text: str,
        categories: list[str],
    ) -> AIResponse:
        """
        Basit sınıflandırma.

        Args:
            text: Sınıflandırılacak metin
            categories: Olası kategoriler

        Returns:
            AIResponse with structured_data: {"category": str, "confidence": float}
        """
        pass

    def raw_generate(
        self,
        prompt: str,
        max_tokens: int = 16384,
    ) -> AIResponse:
        """
        Sarmalayıcı olmadan saf prompt gönderme.
        Prompt zaten tüm talimatları içerdiğinde kullanılır
        (örn: algoritma üretimi gibi karmaşık, çok aşamalı görevler).

        Varsayılan implementasyon generate_code'a yönlendirir.
        Adaptörler override etmeli.
        """
        return self.generate_code(prompt=prompt, context={})

    def get_task_suitability(self, task_type: TaskType) -> float:
        """
        Bu modelin belirli bir görev için uygunluk skoru (0.0-1.0).
        Router tarafından kullanılır.

        Returns:
            0.0 = hiç uygun değil
            1.0 = çok uygun
        """
        return 0.5  # Default orta seviye

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Tahmini maliyet hesaplama (USD).

        Returns:
            Tahmini maliyet
        """
        return 0.0  # Subclass override etmeli

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider adı (gemini, claude, openai)."""
        pass

    @property
    def is_available(self) -> bool:
        """Model kullanılabilir durumda mı?"""
        return bool(self.api_key)
