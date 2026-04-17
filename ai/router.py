"""Model Router — görevleri en uygun AI modeline yönlendirir."""
from typing import Optional
from core.models import TaskType, ModelProvider, APIConfig
from core.debug_logger import AIDebugLogger
from ai.adapters import BaseModelAdapter, GeminiAdapter, ClaudeAdapter, OpenAIAdapter


class ModelRouter:
    """
    Akıllı model yönlendirme sistemi.

    Görev analizi → Karmaşıklık skoru → Model seçimi

    Strateji:
    - %70-80 Gemini Flash (ucuz, hızlı)
    - %20-30 Claude Sonnet (kaliteli, karmaşık)
    - GPT sadece fallback
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self._adapters: dict[ModelProvider, BaseModelAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        """Mevcut API keylerle adaptörleri başlat."""
        # Gemini
        if self.config.gemini_key:
            try:
                self._adapters[ModelProvider.GEMINI] = GeminiAdapter(
                    api_key=self.config.gemini_key,
                    model_name=self.config.gemini_model
                )
            except ValueError as e:
                # Paket yüklü değil, sessizce atla
                pass

        # Claude
        if self.config.claude_key:
            try:
                self._adapters[ModelProvider.CLAUDE] = ClaudeAdapter(
                    api_key=self.config.claude_key,
                    model_name=self.config.claude_model
                )
            except ValueError as e:
                pass

        # OpenAI
        if self.config.openai_key:
            try:
                self._adapters[ModelProvider.OPENAI] = OpenAIAdapter(
                    api_key=self.config.openai_key,
                    model_name=self.config.openai_model
                )
            except ValueError as e:
                pass

    def select_model(
        self,
        task_type: TaskType,
        prefer_cost_optimization: bool = True,
        required_provider: Optional[ModelProvider] = None,
    ) -> BaseModelAdapter:
        """
        Görev için en uygun modeli seç.

        Args:
            task_type: Görev tipi
            prefer_cost_optimization: Maliyet optimizasyonu tercih et (varsayılan True)
            required_provider: Belirli bir provider zorunlu mu?

        Returns:
            Seçilen model adaptörü

        Raises:
            ValueError: Uygun model bulunamazsa
        """
        # Belirli provider istendiyse direkt döndür
        if required_provider:
            adapter = self._adapters.get(required_provider)
            if not adapter:
                raise ValueError(f"{required_provider.value} provider mevcut değil")
            return adapter

        # Uygunluk skorlarını hesapla
        candidates = []
        for provider, adapter in self._adapters.items():
            suitability = adapter.get_task_suitability(task_type)
            candidates.append((provider, adapter, suitability))

        if not candidates:
            raise ValueError("Hiçbir AI provider konfigüre edilmemiş")

        # Sırala: suitability'ye göre
        candidates.sort(key=lambda x: x[2], reverse=True)

        # Maliyet optimizasyonu aktifse ve Gemini uygunsa, Gemini'yi tercih et
        if prefer_cost_optimization:
            gemini = next(
                (c for c in candidates if c[0] == ModelProvider.GEMINI and c[2] >= 0.8),
                None
            )
            if gemini:
                return gemini[1]

        # En yüksek uygunluk skoruna sahip modeli döndür
        return candidates[0][1]

    def get_fallback_chain(self, task_type: TaskType) -> list[BaseModelAdapter]:
        """
        Görev için fallback zinciri oluştur.

        Birincil model başarısız olursa sırayla dene.

        Returns:
            Model listesi (öncelik sırasına göre)
        """
        # Tüm adaptörleri suitability'ye göre sırala
        chain = []
        for adapter in self._adapters.values():
            suitability = adapter.get_task_suitability(task_type)
            chain.append((adapter, suitability))

        # Sırala ve sadece adaptörleri döndür
        chain.sort(key=lambda x: x[1], reverse=True)
        return [adapter for adapter, _ in chain]

    def estimate_task_cost(
        self,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[ModelProvider] = None,
    ) -> float:
        """
        Görev için tahmini maliyet hesapla.

        Args:
            task_type: Görev tipi
            input_tokens: Tahmin edilen input token sayısı
            output_tokens: Tahmin edilen output token sayısı
            provider: Belirli bir provider (None ise otomatik seç)

        Returns:
            Tahmini maliyet (USD)
        """
        if provider:
            adapter = self._adapters.get(provider)
        else:
            adapter = self.select_model(task_type)

        if not adapter:
            return 0.0

        return adapter.estimate_cost(input_tokens, output_tokens)

    def get_routing_decision(self, task_type: TaskType) -> dict:
        """
        Yönlendirme kararı detaylarını döndür (debug/analiz için).

        Returns:
            {
                "primary_model": str,
                "fallback_chain": list[str],
                "suitability_scores": dict[str, float],
                "estimated_cost": float
            }
        """
        primary = self.select_model(task_type)
        fallback = self.get_fallback_chain(task_type)

        scores = {}
        for provider, adapter in self._adapters.items():
            scores[provider.value] = adapter.get_task_suitability(task_type)

        return {
            "primary_model": f"{primary.provider_name} - {primary.model_name}",
            "fallback_chain": [f"{a.provider_name} - {a.model_name}" for a in fallback[1:]],
            "suitability_scores": scores,
            "estimated_cost": primary.estimate_cost(1000, 500),  # Örnek hesaplama
        }

    @property
    def available_providers(self) -> list[ModelProvider]:
        """Aktif provider listesi."""
        return list(self._adapters.keys())

    def get_adapter(self, provider: ModelProvider) -> Optional[BaseModelAdapter]:
        """Belirli bir provider'ın adaptörünü döndür."""
        return self._adapters.get(provider)


class RetryHandler:
    """
    Hata yönetimi ve fallback chain yürütücü.

    Birincil model başarısız olursa yedek modelleri dener.
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def execute_with_fallback(
        self,
        task_type: TaskType,
        operation: str,  # "extract", "generate_code", "validate", "classify"
        **kwargs
    ):
        """
        Fallback chain ile operasyon yürüt.

        Args:
            task_type: Görev tipi
            operation: Yapılacak operasyon adı
            **kwargs: Operasyona özel parametreler

        Returns:
            AIResponse

        Raises:
            RuntimeError: Tüm modeller başarısız olursa
        """
        dbg = AIDebugLogger("retry_handler", provider="router", model="fallback_chain")
        fallback_chain = self.router.get_fallback_chain(task_type)
        errors = []

        dbg.log_stage("fallback_chain_start", {
            "task_type": task_type.value,
            "operation": operation,
            "chain": [f"{a.provider_name}/{a.model_name}" for a in fallback_chain],
            "kwargs_keys": [k for k in kwargs.keys() if k != "image_data"],
        })

        for i, adapter in enumerate(fallback_chain):
            try:
                dbg.log_stage(f"trying_model_{i}", {
                    "provider": adapter.provider_name,
                    "model": adapter.model_name,
                    "operation": operation,
                })

                # Operasyonu çağır
                method = getattr(adapter, operation)
                result = method(**kwargs)

                dbg.log_stage(f"model_{i}_success", {
                    "provider": adapter.provider_name,
                    "model": adapter.model_name,
                })
                dbg.finish(success=True, result={
                    "winning_provider": adapter.provider_name,
                    "winning_model": adapter.model_name,
                    "attempt": i + 1,
                })
                return result

            except Exception as e:
                error_info = f"{adapter.provider_name}: {str(e)}"
                errors.append(error_info)
                dbg.log_stage(f"model_{i}_failed", {
                    "provider": adapter.provider_name,
                    "model": adapter.model_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }, status="error")
                continue

        # Tüm modeller başarısız
        error_msg = "\n".join(errors)
        dbg.log_error(RuntimeError(error_msg), context="all_models_failed")
        dbg.finish(success=False)
        raise RuntimeError(f"Tüm modeller başarısız oldu:\n{error_msg}")
