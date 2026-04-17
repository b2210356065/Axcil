"""Gemini Flash adaptörü — hızlı çıkarma ve sınıflandırma."""
import time
import json
import base64
import requests
from typing import Any, Optional
from pydantic import BaseModel
from ai.adapters.base import BaseModelAdapter
import sys
import pydantic
from core.models import AIResponse, TaskType
from core.debug_logger import AIDebugLogger

# REST API kullanarak direkt Gemini'ye bağlanıyoruz (paket bağımlılığı yok)
GEMINI_AVAILABLE = True


class GeminiAdapter(BaseModelAdapter):
    # Sınıf seviyesinde son istek zamanını tut (tüm API çağrılarını yavaşlatmak için)
    _last_request_time = 0.0

    """
    Gemini Flash — Hızlı İşçi.

    Güçlü yönler:
    - En hızlı model (~2-5x diğerlerinden)
    - En ucuz ($0.15/1M input, $0.60/1M output)
    - 1M token bağlam penceresi
    - Mükemmel multimodal (görsel, PDF, video, ses)
    - responseSchema ile JSON garantisi

    Kullanım alanları:
    - Görsel/PDF'den veri çıkarma
    - Basit sınıflandırma
    - Büyük belge işleme
    """

    def _validate_config(self) -> None:
        """API key kontrolü."""
        if not self.api_key:
            raise ValueError("Gemini API key gerekli")
        # REST API kullanıyoruz, ek konfigürasyon gerekmez
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        # Model adı 'models/' ile başlamıyorsa REST API hata verir, bunu otomatik düzeltelim
        if self.model_name and not self.model_name.startswith("models/"):
            self.model_name = f"models/{self.model_name}"

        # OTOMATİK REDIRECT KALDIRILDI - Kullanıcı ne seçerse o kullanılır
        # Model adı aynen kullanılacak, redirect yok
        print(f"[GEMINI ADAPTER] Kullanılan model: {self.model_name}")

    def _clean_schema_for_gemini(self, schema: Any) -> Any:
        """Gemini API'nin kabul etmediği Pydantic alanlarını temizler ve type'ları düzeltir."""
        if isinstance(schema, dict):
            # Gemini'nin 400 hatası vermesine sebep olan Pydantic anahtarlarını temizle
            schema.pop("title", None)
            schema.pop("default", None)

            # Veri tiplerini BÜYÜK HARF yap (örn: 'string' -> 'STRING')
            if "type" in schema and isinstance(schema["type"], str):
                schema["type"] = schema["type"].upper()

            return {k: self._clean_schema_for_gemini(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self._clean_schema_for_gemini(item) for item in schema]
        return schema

    def _flatten_pydantic_schema(self, model: type[BaseModel]) -> dict:
        """
        Pydantic schema'yı flatten et - $defs ve $ref'leri kaldır.
        Gemini API inline schema istiyor, referans kabul etmiyor.
        """
        schema = model.model_json_schema()

        # $defs varsa, tüm referansları resolve et
        if "$defs" in schema:
            defs = schema.pop("$defs")
            schema = self._resolve_refs(schema, defs)

        # Şemayı Gemini REST API formatına uygun hale getir
        return self._clean_schema_for_gemini(schema)

    def _resolve_refs(self, obj: Any, defs: dict) -> Any:
        """$ref referanslarını inline olarak resolve et."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                # Referansı çöz: "#/$defs/ExcelSheet" -> ExcelSheet tanımını al
                ref_path = obj["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.replace("#/$defs/", "")
                    # Tanımı al ve içindeki referansları da çöz
                    resolved = defs.get(def_name, {}).copy()
                    return self._resolve_refs(resolved, defs)
                return obj
            else:
                # Dictionary içindeki tüm değerleri recursive olarak işle
                return {k: self._resolve_refs(v, defs) for k, v in obj.items()}
        elif isinstance(obj, list):
            # List içindeki tüm elemanları recursive olarak işle
            return [self._resolve_refs(item, defs) for item in obj]
        else:
            return obj

    def _post_with_retry(self, url: str, json_data: dict, timeout: int = 120,
                         max_retries: int = 3, dbg: AIDebugLogger = None) -> requests.Response:
        """429 (Quota Exceeded) hatalarında otomatik bekleme ve tekrar deneme mantığı."""
        for attempt in range(max_retries):
            # Hem dakika başı istek (RPM) hem de token (TPM) limitini yormamak için bekleme süresini 6 saniyeye çıkarıyoruz.
            elapsed = time.time() - GeminiAdapter._last_request_time
            if elapsed < 6.0:
                wait_time = 6.0 - elapsed
                if dbg:
                    dbg.log_stage("rate_limit_wait", {"wait_seconds": round(wait_time, 2)})
                time.sleep(wait_time)
            GeminiAdapter._last_request_time = time.time()

            response = requests.post(url, json=json_data, timeout=timeout)
            if response.status_code == 429 and attempt < max_retries - 1:
                # API'den gelen orijinal hatayı terminale yazdır
                print(f"\n[GEMINI ADAPTER] API'den dönen ham hata (429):\n{response.text}\n")
                if dbg:
                    dbg.log_stage("rate_limit_429", {
                        "attempt": attempt + 1,
                        "response_text": response.text[:2000],
                    }, status="warning")

                sleep_time = 15 * (attempt + 1)
                is_daily_limit = False
                try:
                    error_data = response.json()
                    if "GenerateRequestsPerDay" in str(error_data):
                        is_daily_limit = True

                    details = error_data.get("error", {}).get("details", [])
                    for detail in details:
                        if "retryDelay" in detail:
                            delay_str = detail["retryDelay"]
                            sleep_time = int(float(delay_str.replace("s", ""))) + 1
                except Exception:
                    pass

                if is_daily_limit:
                    print("[GEMINI ADAPTER] Günlük limit tamamen dolmuş! Tekrar deneme döngüsü iptal ediliyor.")
                    if dbg:
                        dbg.log_stage("daily_limit_reached", {"message": "Günlük limit doldu"}, status="error")
                    break

                print(f"[GEMINI ADAPTER] 429 Kotaya takıldı. İşlem devamı için {sleep_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
                continue
            return response
        return response

    def extract(
        self,
        prompt: str,
        schema: type[BaseModel],
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
    ) -> AIResponse:
        """Veri çıkarma — Gemini'nin en güçlü yönü."""
        dbg = AIDebugLogger("extract", provider="gemini", model=self.model_name)
        start = time.time()

        try:
            # İçerik hazırlama
            parts = [{"text": prompt}]
            if image_data:
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": image_b64
                    }
                })

            # Schema'yı flatten et ve temizle
            json_schema = self._flatten_pydantic_schema(schema)

            dbg.log_prompt(prompt, schema=schema, extra={
                "has_image": image_data is not None,
                "image_size": len(image_data) if image_data else 0,
                "mime_type": mime_type,
                "flattened_schema": json_schema,
                "original_schema": schema.model_json_schema(),
            })

            # Request body
            request_body = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": json_schema,
                }
            }

            url_masked = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key[:8]}...MASKED"
            real_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"

            dbg.log_api_request(request_body={
                "model": self.model_name,
                "generationConfig": request_body["generationConfig"],
                "parts_count": len(parts),
                "parts_types": [list(p.keys()) for p in parts],
            }, url=url_masked)

            response = self._post_with_retry(real_url, json_data=request_body, timeout=180, dbg=dbg)

            # Hata durumunda detaylı mesajı göster
            if not response.ok:
                error_detail = response.text
                dbg.log_api_response(status_code=response.status_code, raw_text=error_detail)
                dbg.log_error(RuntimeError(f"Gemini API Error {response.status_code}"),
                             context=f"HTTP {response.status_code}: {error_detail[:500]}")
                dbg.finish(success=False)

                print(f"[GEMINI ERROR] Status: {response.status_code}", file=sys.stderr)
                print(f"[GEMINI ERROR] Response: {error_detail}", file=sys.stderr)
                sys.stderr.flush()
                raise RuntimeError(f"Gemini API Error {response.status_code}: {error_detail}")

            result = response.json()

            # Ham yanıtı logla
            dbg.log_api_response(
                response=result,
                status_code=response.status_code,
                raw_text=json.dumps(result, ensure_ascii=False)[:20000],
                tokens={
                    "input": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "output": result.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                }
            )

            # Yanıtı parse et
            if "candidates" not in result or not result["candidates"]:
                dbg.log_parsing("candidates_check",
                               input_data={"keys": list(result.keys())},
                               error="Gemini boş yanıt döndürdü — 'candidates' yok veya boş")
                dbg.finish(success=False)
                raise RuntimeError("Gemini boş yanıt döndürdü")

            content_text = result["candidates"][0]["content"]["parts"][0]["text"]

            dbg.log_parsing("json_text_extracted",
                           input_data={"content_text_length": len(content_text),
                                       "content_text_preview": content_text[:2000]})

            # Token kullanımı
            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            latency_ms = int((time.time() - start) * 1000)
            cost = self.estimate_cost(input_tokens, output_tokens)

            # Pydantic validation
            try:
                validated = schema.model_validate_json(content_text)
                structured_data = validated.model_dump()
                dbg.log_schema_validation(
                    schema_class=schema.__name__,
                    data=content_text[:3000],
                    result=structured_data,
                )
            except Exception as val_err:
                dbg.log_schema_validation(
                    schema_class=schema.__name__,
                    data=content_text[:3000],
                    error=f"{type(val_err).__name__}: {val_err}",
                )
                dbg.finish(success=False)
                raise

            ai_response = AIResponse(
                content=content_text,
                structured_data=structured_data,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={
                "structured_data_keys": list(structured_data.keys()) if isinstance(structured_data, dict) else str(type(structured_data)),
                "tokens": {"input": input_tokens, "output": output_tokens},
                "cost_usd": cost,
                "latency_ms": latency_ms,
            })

            return ai_response

        except requests.exceptions.RequestException as e:
            dbg.log_error(e, context="gemini_extract_network_error")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini API error: {e}") from e
        except Exception as e:
            if not any(s.get("status") == "error" for s in dbg.entry.get("stages", [])):
                dbg.log_error(e, context="gemini_extract_unexpected")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini extraction error: {e}") from e

    def generate_code(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> AIResponse:
        """Kod üretimi — Gemini'nin zayıf yönü."""
        dbg = AIDebugLogger("generate_code", provider="gemini", model=self.model_name)
        start = time.time()

        try:
            full_prompt = f"""
{prompt}

<context>
{json.dumps(context, ensure_ascii=False, indent=2)}
</context>

Python kodu üret (sadece kod, açıklama yok):
"""

            dbg.log_prompt(full_prompt, extra={"context_keys": list(context.keys())})

            request_body = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"
            dbg.log_api_request(request_body={"prompt_length": len(full_prompt)})

            response = self._post_with_retry(url, json_data=request_body, timeout=180, dbg=dbg)

            if not response.ok:
                error_detail = response.text
                dbg.log_api_response(status_code=response.status_code, raw_text=error_detail)
                dbg.finish(success=False)
                raise RuntimeError(f"Gemini API Error {response.status_code}: {error_detail}")

            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]

            dbg.log_api_response(
                status_code=200,
                raw_text=content_text[:5000],
                tokens={
                    "input": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "output": result.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                }
            )

            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            latency_ms = int((time.time() - start) * 1000)
            cost = self.estimate_cost(input_tokens, output_tokens)

            ai_response = AIResponse(
                content=content_text,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={"code_length": len(content_text)})
            return ai_response

        except Exception as e:
            dbg.log_error(e, context="gemini_generate_code")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini code generation error: {e}") from e

    def raw_generate(
        self,
        prompt: str,
        max_tokens: int = 16384,
    ) -> AIResponse:
        """Sarmalayıcı olmadan saf prompt gönderme."""
        dbg = AIDebugLogger("raw_generate", provider="gemini", model=self.model_name)
        start = time.time()

        try:
            safe_max_tokens = min(max_tokens, 8192)
            dbg.log_prompt(prompt, extra={"max_tokens": safe_max_tokens})

            request_body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": safe_max_tokens}
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"
            response = self._post_with_retry(url, json_data=request_body, timeout=180, dbg=dbg)

            if not response.ok:
                error_detail = response.text
                dbg.log_api_response(status_code=response.status_code, raw_text=error_detail)
                dbg.finish(success=False)
                raise RuntimeError(f"Gemini API Error {response.status_code}: {error_detail}")

            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]

            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            dbg.log_api_response(
                status_code=200,
                raw_text=content_text[:5000],
                tokens={"input": input_tokens, "output": output_tokens}
            )

            latency_ms = int((time.time() - start) * 1000)
            cost = self.estimate_cost(input_tokens, output_tokens)

            ai_response = AIResponse(
                content=content_text,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result={"content_length": len(content_text)})
            return ai_response

        except Exception as e:
            dbg.log_error(e, context="gemini_raw_generate")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini raw generation error: {e}") from e

    def validate(
        self,
        data: dict[str, Any],
        rules: list[str],
        context: dict[str, Any],
    ) -> AIResponse:
        """Basit doğrulama — karmaşık anomali tespiti için Claude tercih edilmeli."""
        dbg = AIDebugLogger("validate", provider="gemini", model=self.model_name)
        start = time.time()

        try:
            from core.models import ValidationResult

            prompt = f"""
Aşağıdaki veriyi doğrula:

<data>
{json.dumps(data, ensure_ascii=False, indent=2)}
</data>

<rules>
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(rules))}
</rules>

<context>
{json.dumps(context, ensure_ascii=False, indent=2)}
</context>

Her alan için doğrulama yap ve ValidationResult formatında döndür.
"""

            json_schema = self._flatten_pydantic_schema(ValidationResult)

            dbg.log_prompt(prompt, extra={
                "data_keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
                "rules_count": len(rules),
                "flattened_schema": json_schema,
            })

            request_body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": json_schema,
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"

            dbg.log_api_request(request_body={
                "generationConfig": request_body["generationConfig"],
                "prompt_length": len(prompt),
            })

            response = self._post_with_retry(url, json_data=request_body, timeout=180, dbg=dbg)

            if not response.ok:
                error_detail = response.text
                dbg.log_api_response(status_code=response.status_code, raw_text=error_detail)
                dbg.finish(success=False)
                raise RuntimeError(f"Gemini API Error {response.status_code}: {error_detail}")

            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]

            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            dbg.log_api_response(
                status_code=200,
                raw_text=content_text[:5000],
                tokens={"input": input_tokens, "output": output_tokens}
            )

            latency_ms = int((time.time() - start) * 1000)
            cost = self.estimate_cost(input_tokens, output_tokens)

            try:
                validated = ValidationResult.model_validate_json(content_text)
                structured_data = validated.model_dump()
                dbg.log_schema_validation("ValidationResult", content_text[:2000], result=structured_data)
            except Exception as val_err:
                dbg.log_schema_validation("ValidationResult", content_text[:2000], error=str(val_err))
                dbg.finish(success=False)
                raise

            ai_response = AIResponse(
                content=content_text,
                structured_data=structured_data,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result=structured_data)
            return ai_response

        except Exception as e:
            if not any(s.get("status") == "error" for s in dbg.entry.get("stages", [])):
                dbg.log_error(e, context="gemini_validate")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini validation error: {e}") from e

    def classify(
        self,
        text: str,
        categories: list[str],
    ) -> AIResponse:
        """Sınıflandırma — Gemini'nin güçlü yönlerinden."""
        dbg = AIDebugLogger("classify", provider="gemini", model=self.model_name)
        start = time.time()

        try:
            from pydantic import Field

            class ClassificationResult(BaseModel):
                category: str = Field(description="Seçilen kategori")
                confidence: float = Field(description="Güven skoru 0.0-1.0", ge=0.0, le=1.0)
                reasoning: str = Field(description="Kısa açıklama")

            prompt = f"""
Bu metni kategorize et:

"{text}"

Kategoriler:
{chr(10).join(f"- {cat}" for cat in categories)}

En uygun kategoriyi seç ve güven skorunu belirt.
"""

            json_schema = self._flatten_pydantic_schema(ClassificationResult)

            dbg.log_prompt(prompt, extra={
                "text_length": len(text),
                "categories": categories,
                "schema": json_schema,
            })

            request_body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": json_schema,
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_name}:generateContent?key={self.api_key}"
            response = self._post_with_retry(url, json_data=request_body, timeout=180, dbg=dbg)

            if not response.ok:
                error_detail = response.text
                dbg.log_api_response(status_code=response.status_code, raw_text=error_detail)
                dbg.finish(success=False)
                raise RuntimeError(f"Gemini API Error {response.status_code}: {error_detail}")

            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]

            usage = result.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            dbg.log_api_response(
                status_code=200,
                raw_text=content_text[:3000],
                tokens={"input": input_tokens, "output": output_tokens}
            )

            latency_ms = int((time.time() - start) * 1000)
            cost = self.estimate_cost(input_tokens, output_tokens)

            try:
                validated = ClassificationResult.model_validate_json(content_text)
                structured_data = validated.model_dump()
                dbg.log_schema_validation("ClassificationResult", content_text[:2000], result=structured_data)
            except Exception as val_err:
                dbg.log_schema_validation("ClassificationResult", content_text[:2000], error=str(val_err))
                dbg.finish(success=False)
                raise

            ai_response = AIResponse(
                content=content_text,
                structured_data=structured_data,
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
            )

            dbg.finish(success=True, result=structured_data)
            return ai_response

        except Exception as e:
            if not any(s.get("status") == "error" for s in dbg.entry.get("stages", [])):
                dbg.log_error(e, context="gemini_classify")
            dbg.finish(success=False)
            raise RuntimeError(f"Gemini classification error: {e}") from e

    def get_task_suitability(self, task_type: TaskType) -> float:
        """Gemini için görev uygunluk skorları."""
        suitability = {
            TaskType.EXTRACTION: 1.0,
            TaskType.CLASSIFICATION: 1.0,
            TaskType.SIMPLE_TRANSFORM: 0.9,
            TaskType.COMPLEX_TRANSFORM: 0.4,
            TaskType.CODE_GENERATION: 0.3,
            TaskType.VALIDATION: 0.7,
            TaskType.ANOMALY_DETECTION: 0.4,
        }
        return suitability.get(task_type, 0.5)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Gemini Flash maliyet hesaplama."""
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        return "gemini"
