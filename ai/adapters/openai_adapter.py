"""OpenAI GPT adaptörü — çok yönlü yedek model."""
import time
from typing import Any, Optional
from pydantic import BaseModel
from ai.adapters.base import BaseModelAdapter
from core.models import AIResponse, TaskType

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class OpenAIAdapter(BaseModelAdapter):
    """
    GPT-4/GPT-5 — Çok Yönlü Yedek.

    Güçlü yönler:
    - Güçlü talimat takibi
    - Mükemmel multimodal (metin, görsel, ses)
    - Strict JSON schema ile decode-time garanti
    - OpenAI ekosistem entegrasyonu

    Kullanım alanları:
    - Fallback model (Gemini veya Claude başarısız olursa)
    - Genel amaçlı görevler
    - Ses transkripsiyonu (Whisper)
    """

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        if OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    def _validate_config(self) -> None:
        """API key kontrolü."""
        if not OPENAI_AVAILABLE:
            raise ValueError("openai paketi yüklü değil. 'pip install openai' çalıştırın.")
        if not self.api_key:
            raise ValueError("OpenAI API key gerekli")

    def extract(
        self,
        prompt: str,
        schema: type[BaseModel],
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
    ) -> AIResponse:
        """Veri çıkarma — GPT görsel analiz yapabilir."""
        start = time.time()

        try:
            # Mesaj içeriği hazırlama
            content = [{"type": "text", "text": prompt}]

            if image_data:
                import base64
                base64_image = base64.b64encode(image_data).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                })

            # API çağrısı (Structured Outputs)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{
                    "role": "system",
                    "content": "Sen bir veri çıkarma uzmanısın. Verilen içeriği analiz et ve yapılandırılmış formatta döndür."
                }, {
                    "role": "user",
                    "content": content
                }],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extraction_result",
                        "strict": True,  # JSON garantisi
                        "schema": schema.model_json_schema()
                    }
                }
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            message_content = response.choices[0].message.content

            return AIResponse(
                content=message_content,
                structured_data=schema.model_validate_json(message_content).model_dump(),
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI extraction error: {e}") from e

    def generate_code(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> AIResponse:
        """Kod üretimi — GPT iyi yapar ama Claude'dan zayıf."""
        start = time.time()

        try:
            system_prompt = """Sen bir Excel otomasyon uzmanısın. openpyxl ile profesyonel Excel dosyaları oluşturan Python kodu üretirsin.

KURALLAR:
- Sadece Python kodu üret
- İzin verilen: openpyxl, datetime, os, json, re, math, decimal
- YASAK: eval, exec, subprocess, __import__, system, popen
- Fonksiyon: create_excel(data: dict, output_path: str) -> None
- Profesyonel stil (başlık formatı, kenarlık, sayı formatları)
"""

            user_prompt = f"""
{prompt}

Context:
{context}

Python kodu üret:
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096,
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            # Code block çıkar
            code_text = response.choices[0].message.content
            if "```python" in code_text:
                code_text = code_text.split("```python")[1].split("```")[0].strip()

            return AIResponse(
                content=code_text,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI code generation error: {e}") from e

    def raw_generate(
        self,
        prompt: str,
        max_tokens: int = 16384,
    ) -> AIResponse:
        """Sarmalayıcı olmadan saf prompt gönderme."""
        start = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            return AIResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI raw generation error: {e}") from e

    def validate(
        self,
        data: dict[str, Any],
        rules: list[str],
        context: dict[str, Any],
    ) -> AIResponse:
        """Veri doğrulama — GPT yeterli ama Claude'dan zayıf."""
        start = time.time()

        try:
            from core.models import ValidationResult

            prompt = f"""
Aşağıdaki veriyi doğrula:

VERİ:
{data}

DOĞRULAMA KURALLARI:
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(rules))}

BAĞLAM:
{context}

Kontroller:
1. Matematiksel tutarlılık
2. Format uyumu
3. Mantıksal tutarlılık
4. Anomali tespiti
5. İş kurallarına uygunluk

ValidationResult formatında döndür.
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Sen bir veri doğrulama uzmanısın."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "validation_result",
                        "strict": True,
                        "schema": ValidationResult.model_json_schema()
                    }
                }
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            message_content = response.choices[0].message.content

            return AIResponse(
                content=message_content,
                structured_data=ValidationResult.model_validate_json(message_content).model_dump(),
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI validation error: {e}") from e

    def classify(
        self,
        text: str,
        categories: list[str],
    ) -> AIResponse:
        """Sınıflandırma — GPT yeterli ama Gemini'den pahalı."""
        start = time.time()

        try:
            from pydantic import Field

            class ClassificationResult(BaseModel):
                category: str = Field(description="Seçilen kategori")
                confidence: float = Field(description="Güven skoru", ge=0.0, le=1.0)
                reasoning: str = Field(description="Karar gerekçesi")

            prompt = f"""
Bu metni kategorize et:

"{text}"

Kategoriler:
{chr(10).join(f"- {cat}" for cat in categories)}

En uygun kategoriyi seç, güven skorunu ve gerekçeni belirt.
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Sen bir metin sınıflandırma uzmanısın."},
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "classification_result",
                        "strict": True,
                        "schema": ClassificationResult.model_json_schema()
                    }
                }
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            message_content = response.choices[0].message.content

            return AIResponse(
                content=message_content,
                structured_data=ClassificationResult.model_validate_json(message_content).model_dump(),
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI classification error: {e}") from e

    def get_task_suitability(self, task_type: TaskType) -> float:
        """OpenAI için görev uygunluk skorları — genel amaçlı yedek."""
        suitability = {
            TaskType.EXTRACTION: 0.8,           # İyi
            TaskType.CLASSIFICATION: 0.8,       # İyi
            TaskType.SIMPLE_TRANSFORM: 0.7,     # İyi
            TaskType.COMPLEX_TRANSFORM: 0.7,    # İyi
            TaskType.CODE_GENERATION: 0.8,      # İyi
            TaskType.VALIDATION: 0.7,           # İyi
            TaskType.ANOMALY_DETECTION: 0.6,    # Yeterli
        }
        return suitability.get(task_type, 0.7)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        OpenAI maliyet hesaplama.

        Fiyatlandırma (model bazlı, ortalama GPT-4 Turbo):
        - Input: ~$10.00 / 1M tokens
        - Output: ~$30.00 / 1M tokens

        Not: GPT-5 daha pahalı olabilir, model bazlı güncelleme gerekebilir.
        """
        # Basitleştirilmiş hesaplama — gerçek fiyatlar model bazında değişir
        input_cost = (input_tokens / 1_000_000) * 10.00
        output_cost = (output_tokens / 1_000_000) * 30.00
        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        return "openai"
