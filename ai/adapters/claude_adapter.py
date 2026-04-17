"""Claude 4.5 Sonnet adaptörü — uzman kod üretimi ve karmaşık muhakeme."""
import time
from typing import Any, Optional
from pydantic import BaseModel
from ai.adapters.base import BaseModelAdapter
from core.models import AIResponse, TaskType
from core.debug_logger import AIDebugLogger

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    anthropic = None


class ClaudeAdapter(BaseModelAdapter):
    """
    Claude 4.5 Sonnet — Uzman Mühendis.

    Güçlü yönler:
    - Sınıfının en iyi kod üretimi
    - Derin analitik ve muhakeme
    - Karmaşık iş mantığı anlama
    - Tool use ile yapılandırılmış çıktı

    Kullanım alanları:
    - Excel kodu üretme (openpyxl)
    - Karmaşık veri dönüştürme
    - Anomali tespiti
    - Formül/VBA üretimi
    """

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name)
        if CLAUDE_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

    def _validate_config(self) -> None:
        """API key kontrolü."""
        if not CLAUDE_AVAILABLE:
            raise ValueError("anthropic paketi yüklü değil. 'pip install anthropic' çalıştırın.")
        if not self.api_key:
            raise ValueError("Claude API key gerekli")

    def extract(
        self,
        prompt: str,
        schema: type[BaseModel],
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
    ) -> AIResponse:
        """
        Veri çıkarma — Claude görsel analiz yapabilir ama Gemini'den yavaş.
        Genelde karmaşık çıkarma senaryolarında kullanılır.
        """
        dbg = AIDebugLogger("extract", provider="claude", model=self.model_name)
        start = time.time()

        try:
            # Tool definition
            tool_schema = schema.model_json_schema()
            tool = {
                "name": "extract_data",
                "description": "Veriyi yapılandırılmış formatta çıkar",
                "input_schema": tool_schema
            }

            dbg.log_prompt(prompt, schema=schema, extra={
                "has_image": image_data is not None,
                "image_size": len(image_data) if image_data else 0,
                "mime_type": mime_type,
                "tool_definition": tool,
            })

            # İçerik hazırlama
            content = []
            if image_data:
                import base64
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64.b64encode(image_data).decode()
                    }
                })
            content.append({
                "type": "text",
                "text": prompt
            })

            # API çağrısı detaylarını logla
            api_params = {
                "model": self.model_name,
                "max_tokens": 4096,
                "tools": [tool],
                "tool_choice": {"type": "any"},
                "message_content_types": [c["type"] for c in content],
            }
            dbg.log_api_request(request_body=api_params)

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                tools=[tool],
                tool_choice={"type": "any"},
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # Ham yanıtı logla
            raw_content_blocks = []
            for block in response.content:
                if block.type == "tool_use":
                    raw_content_blocks.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                elif block.type == "text":
                    raw_content_blocks.append({
                        "type": "text",
                        "text": block.text,
                    })
                else:
                    raw_content_blocks.append({
                        "type": block.type,
                        "str": str(block),
                    })

            dbg.log_api_response(
                response=raw_content_blocks,
                status_code=200,
                raw_text=str(raw_content_blocks),
                tokens={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                }
            )

            # Tool use yanıtını parse et
            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None
            )

            if not tool_use:
                dbg.log_parsing("tool_use_search", input_data=raw_content_blocks,
                               error="Claude tool use yanıtı bulunamadı — hiçbir content block'u tool_use tipinde değil")
                raise ValueError("Claude tool use yanıtı bulunamadı")

            dbg.log_tool_use_response(
                tool_name=tool_use.name,
                tool_input=tool_use.input,
                raw_content=raw_content_blocks,
            )

            # Structured data olarak kaydet
            dbg.log_parsing("structured_data_extract",
                           input_data={"tool_use.input_type": str(type(tool_use.input)),
                                       "tool_use.input": tool_use.input})

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            result = AIResponse(
                content=str(tool_use.input),
                structured_data=tool_use.input,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={
                "structured_data": tool_use.input,
                "tokens": {"input": input_tokens, "output": output_tokens},
                "cost_usd": cost,
                "latency_ms": latency_ms,
            })

            return result

        except Exception as e:
            dbg.log_error(e, context="claude_extract")
            dbg.finish(success=False)
            raise RuntimeError(f"Claude extraction error: {e}") from e

    def generate_code(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> AIResponse:
        """
        Kod üretimi — Claude'un en güçlü yönü.
        Temiz, idiomatik, güvenli Python/openpyxl kodu üretir.
        """
        dbg = AIDebugLogger("generate_code", provider="claude", model=self.model_name)
        start = time.time()

        try:
            # XML formatında prompt (Claude'un tercihi)
            full_prompt = f"""
<task>
{prompt}
</task>

<context>
İş yeri bağlamı: {context.get('business_context', {})}
Excel şeması: {context.get('schema', {})}
Stil gereksinimleri: {context.get('style_requirements', {})}
</context>

<constraints>
- Sadece Python kodu üret, açıklama ekleme
- İzin verilen: openpyxl, datetime, os, json, re, math, decimal
- YASAK: eval, exec, subprocess, __import__, system, popen
- Fonksiyon imzası: create_excel(data: dict, output_path: str) -> None
- Profesyonel formatlama (başlık stil, kenarlık, sayı formatları)
</constraints>

Python kodunu üret:
"""

            dbg.log_prompt(full_prompt, extra={
                "original_prompt_length": len(prompt),
                "context_keys": list(context.keys()),
            })

            dbg.log_api_request(request_body={
                "model": self.model_name,
                "max_tokens": 8192,
                "message_role": "user",
            })

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=8192,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )

            # Ham yanıtı logla
            raw_text = response.content[0].text if response.content else ""
            dbg.log_api_response(
                status_code=200,
                raw_text=raw_text,
                tokens={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                }
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            # Code block'u çıkar
            code_text = response.content[0].text
            dbg.log_parsing("code_block_extraction",
                           input_data={"raw_length": len(code_text),
                                       "has_python_block": "```python" in code_text,
                                       "has_any_block": "```" in code_text})

            if "```python" in code_text:
                code_text = code_text.split("```python")[1].split("```")[0].strip()
                dbg.log_parsing("code_block_extracted",
                               output_data={"extracted_length": len(code_text),
                                            "first_100_chars": code_text[:100]})
            else:
                dbg.log_parsing("code_block_extraction",
                               input_data={"note": "```python bulunamadı, ham yanıt kullanılacak"},
                               output_data={"code_length": len(code_text)})

            result = AIResponse(
                content=code_text,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={
                "code_length": len(code_text),
                "code_first_200": code_text[:200],
                "tokens": {"input": input_tokens, "output": output_tokens},
                "cost_usd": cost,
            })

            return result

        except Exception as e:
            dbg.log_error(e, context="claude_generate_code")
            dbg.finish(success=False)
            raise RuntimeError(f"Claude code generation error: {e}") from e

    def raw_generate(
        self,
        prompt: str,
        max_tokens: int = 16384,
    ) -> AIResponse:
        """Sarmalayıcı olmadan saf prompt gönderme — algoritma üretimi için."""
        dbg = AIDebugLogger("raw_generate", provider="claude", model=self.model_name)
        start = time.time()

        try:
            dbg.log_prompt(prompt, extra={"max_tokens": max_tokens})

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            raw_text = response.content[0].text if response.content else ""
            dbg.log_api_response(
                status_code=200,
                raw_text=raw_text,
                tokens={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                }
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            result = AIResponse(
                content=response.content[0].text,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={
                "content_length": len(result.content),
                "tokens": {"input": input_tokens, "output": output_tokens},
            })

            return result

        except Exception as e:
            dbg.log_error(e, context="claude_raw_generate")
            dbg.finish(success=False)
            raise RuntimeError(f"Claude raw generation error: {e}") from e

    def validate(
        self,
        data: dict[str, Any],
        rules: list[str],
        context: dict[str, Any],
    ) -> AIResponse:
        """
        Veri doğrulama ve anomali tespiti — Claude'un güçlü yönü.
        Derin muhakeme ile mantıksal tutarsızlıkları tespit eder.
        """
        dbg = AIDebugLogger("validate", provider="claude", model=self.model_name)
        start = time.time()

        try:
            from core.models import ValidationResult

            tool_schema = ValidationResult.model_json_schema()
            tool = {
                "name": "validate_data",
                "description": "Veriyi doğrula ve anomalileri tespit et",
                "input_schema": tool_schema
            }

            prompt = f"""
<data>
{data}
</data>

<validation_rules>
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(rules))}
</validation_rules>

<business_context>
{context}
</business_context>

Derin analiz yap:
1. Matematiksel tutarlılık (toplamlar, oranlar)
2. Format uyumu (tarih, tutar formatları)
3. Mantıksal tutarlılık (gelecek tarih, negatif değer vs.)
4. Anomali tespiti (normal aralık dışı değerler)
5. İş kurallarına uygunluk

Her sorun için ValidationIssue oluştur.
"""

            dbg.log_prompt(prompt, extra={
                "data_keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
                "rules_count": len(rules),
                "tool_definition": tool,
            })

            dbg.log_api_request(request_body={
                "model": self.model_name,
                "max_tokens": 4096,
                "tools": [tool],
                "tool_choice": {"type": "any"},
            })

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                tools=[tool],
                tool_choice={"type": "any"},
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Ham yanıtı logla
            raw_content_blocks = []
            for block in response.content:
                if block.type == "tool_use":
                    raw_content_blocks.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                elif block.type == "text":
                    raw_content_blocks.append({
                        "type": "text",
                        "text": block.text,
                    })
                else:
                    raw_content_blocks.append({"type": block.type, "str": str(block)})

            dbg.log_api_response(
                response=raw_content_blocks,
                status_code=200,
                raw_text=str(raw_content_blocks),
                tokens={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                }
            )

            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None
            )

            if not tool_use:
                dbg.log_parsing("tool_use_search", input_data=raw_content_blocks,
                               error="Claude validation yanıtı bulunamadı")
                raise ValueError("Claude validation yanıtı bulunamadı")

            dbg.log_tool_use_response(
                tool_name=tool_use.name,
                tool_input=tool_use.input,
                raw_content=raw_content_blocks,
            )

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            result = AIResponse(
                content=str(tool_use.input),
                structured_data=tool_use.input,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={
                "structured_data": tool_use.input,
                "tokens": {"input": input_tokens, "output": output_tokens},
            })

            return result

        except Exception as e:
            dbg.log_error(e, context="claude_validate")
            dbg.finish(success=False)
            raise RuntimeError(f"Claude validation error: {e}") from e

    def classify(
        self,
        text: str,
        categories: list[str],
    ) -> AIResponse:
        """Sınıflandırma — Claude bunu da iyi yapar ama Gemini'den pahalı."""
        dbg = AIDebugLogger("classify", provider="claude", model=self.model_name)
        start = time.time()

        try:
            from pydantic import Field

            class ClassificationResult(BaseModel):
                category: str = Field(description="Seçilen kategori")
                confidence: float = Field(description="Güven skoru", ge=0.0, le=1.0)
                reasoning: str = Field(description="Karar gerekçesi")

            tool = {
                "name": "classify_text",
                "description": "Metni kategorize et",
                "input_schema": ClassificationResult.model_json_schema()
            }

            prompt = f"""
Bu metni kategorize et: "{text}"

Kategoriler:
{chr(10).join(f"- {cat}" for cat in categories)}

En uygun kategoriyi seç, güven skorunu ve gerekçeni belirt.
"""

            dbg.log_prompt(prompt, extra={
                "text_length": len(text),
                "categories": categories,
                "tool_definition": tool,
            })

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                tools=[tool],
                tool_choice={"type": "any"},
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            raw_content_blocks = []
            for block in response.content:
                if block.type == "tool_use":
                    raw_content_blocks.append({
                        "type": "tool_use", "name": block.name, "input": block.input,
                    })
                else:
                    raw_content_blocks.append({"type": block.type, "str": str(block)})

            dbg.log_api_response(
                response=raw_content_blocks,
                status_code=200,
                raw_text=str(raw_content_blocks),
                tokens={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                }
            )

            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None
            )

            if not tool_use:
                dbg.log_parsing("tool_use_search", error="Claude classification yanıtı bulunamadı")
                raise ValueError("Claude classification yanıtı bulunamadı")

            dbg.log_tool_use_response(tool_name=tool_use.name, tool_input=tool_use.input)

            latency_ms = int((time.time() - start) * 1000)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)

            result = AIResponse(
                content=str(tool_use.input),
                structured_data=tool_use.input,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result=tool_use.input)
            return result

        except Exception as e:
            dbg.log_error(e, context="claude_classify")
            dbg.finish(success=False)
            raise RuntimeError(f"Claude classification error: {e}") from e

    def get_task_suitability(self, task_type: TaskType) -> float:
        """Claude için görev uygunluk skorları."""
        suitability = {
            TaskType.EXTRACTION: 0.7,           # İyi ama Gemini'den yavaş
            TaskType.CLASSIFICATION: 0.8,       # Çok iyi ama Gemini'den pahalı
            TaskType.SIMPLE_TRANSFORM: 0.6,     # İyi ama overkill
            TaskType.COMPLEX_TRANSFORM: 1.0,    # En iyi
            TaskType.CODE_GENERATION: 1.0,      # En iyi
            TaskType.VALIDATION: 0.9,           # Çok iyi
            TaskType.ANOMALY_DETECTION: 1.0,    # En iyi
        }
        return suitability.get(task_type, 0.5)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Claude Sonnet maliyet hesaplama.

        Fiyatlandırma (Nisan 2025):
        - Input: $3.00 / 1M tokens
        - Output: $15.00 / 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        return "claude"
