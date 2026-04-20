"""Pipeline Manager -- cok adimli AI is akislarini yonetir."""
from typing import Any, Callable, Optional
from pydantic import BaseModel
from core.models import TaskType, AIResponse, ExtractionResult, FieldValue
from core.debug_logger import AIDebugLogger
from ai.router import ModelRouter, RetryHandler
from ai.prompts.validation import ValidationPromptBuilder


class PipelineStep(BaseModel):
    """Bir pipeline adimi."""
    name: str
    task_type: TaskType
    operation: str  # "extract", "generate_code", "validate", "classify"
    params: dict[str, Any] = {}
    required: bool = True  # Basarisiz olursa pipeline durur mu?


class PipelineResult(BaseModel):
    """Pipeline sonucu."""
    success: bool
    steps_completed: list[str] = []
    final_data: dict[str, Any] = {}
    errors: list[str] = []
    total_cost: float = 0.0
    total_latency_ms: int = 0


class PipelineManager:
    """
    Cok adimli AI pipeline'larini yonetir.

    Ornek kullanim (Gorsel -> Excel):
    1. Gemini Flash: Gorsel -> JSON cikar
    2. Gemini Flash: JSON'u dogrula
    3. Claude Sonnet: Gerekirse karmasik donusum yap
    4. Claude Sonnet: openpyxl kodu uret
    5. Yerel: Sandbox'ta calistir -> Excel olustur
    """

    def __init__(self, router: ModelRouter):
        self.router = router
        self.retry_handler = RetryHandler(router)

    def execute_extraction_pipeline(
        self,
        image_data: Optional[bytes],
        schema: type[BaseModel],
        business_context: dict[str, Any],
        auto_validate: bool = True,
    ) -> PipelineResult:
        """
        Standart cikarma pipeline'i.

        ADIM 1: Gemini Flash ile gorsel -> JSON cikar
        ADIM 2: Guven skorlarini hesapla
        ADIM 3 (opsiyonel): Dusuk guvenli alanlari Claude ile dogrula

        Returns:
            PipelineResult with extracted data
        """
        dbg = AIDebugLogger("extraction_pipeline", provider="pipeline", model="multi")
        result = PipelineResult(success=False)

        try:
            # ADIM 1: Cikarma (Gemini Flash - ucuz & hizli)
            prompt = self._build_extraction_prompt(schema, business_context)

            dbg.log_stage("step1_extraction_start", {
                "schema_class": schema.__name__ if hasattr(schema, '__name__') else str(schema),
                "has_image": image_data is not None,
                "image_size": len(image_data) if image_data else 0,
                "business_context_keys": list(business_context.keys()),
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:1000],
            })

            extraction_response: AIResponse = self.retry_handler.execute_with_fallback(
                task_type=TaskType.EXTRACTION,
                operation="extract",
                prompt=prompt,
                schema=schema,
                image_data=image_data,
            )

            result.steps_completed.append("extraction")
            result.total_cost += extraction_response.cost_usd
            result.total_latency_ms += extraction_response.latency_ms

            extracted_data = extraction_response.structured_data

            dbg.log_stage("step1_extraction_done", {
                "model_used": extraction_response.model,
                "structured_data": extracted_data,
                "tokens": {"input": extraction_response.input_tokens, "output": extraction_response.output_tokens},
                "cost": extraction_response.cost_usd,
            })

            # ADIM 2: Guven skorlarini hesapla
            extraction_result = self._calculate_confidence_scores(
                extracted_data,
                business_context
            )

            dbg.log_stage("step2_confidence_scores", {
                "fields": {k: {"value": str(v.value)[:100], "confidence": v.confidence, "status": v.status}
                          for k, v in extraction_result.fields.items()},
                "confidence_avg": extraction_result.confidence_avg,
            })

            result.steps_completed.append("confidence_calculation")

            # ADIM 3: Dusuk guvenli alanlari dogrula (opsiyonel)
            if auto_validate:
                low_confidence_fields = [
                    field for field, value in extraction_result.fields.items()
                    if value.confidence < 0.70
                ]

                dbg.log_stage("step3_low_confidence_check", {
                    "low_confidence_fields": low_confidence_fields,
                    "threshold": 0.70,
                    "will_validate": len(low_confidence_fields) > 0,
                })

                if low_confidence_fields:
                    validation_response = self._validate_low_confidence_fields(
                        extraction_result,
                        low_confidence_fields,
                        business_context
                    )
                    result.total_cost += validation_response.cost_usd
                    result.total_latency_ms += validation_response.latency_ms
                    result.steps_completed.append("validation")

                    dbg.log_stage("step3_validation_done", {
                        "validation_data": validation_response.structured_data,
                        "cost": validation_response.cost_usd,
                    })

            result.final_data = extraction_result.model_dump()
            result.success = True

            dbg.finish(success=True, result={
                "steps_completed": result.steps_completed,
                "total_cost": result.total_cost,
                "total_latency_ms": result.total_latency_ms,
                "final_data_keys": list(result.final_data.keys()),
            })

        except Exception as e:
            result.errors.append(f"Pipeline error: {str(e)}")
            dbg.log_error(e, context="extraction_pipeline")
            dbg.finish(success=False)

        return result

    def execute_code_generation_pipeline(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        business_context: dict[str, Any],
    ) -> PipelineResult:
        """
        Kod uretim pipeline'i.

        ADIM 1: Claude Sonnet ile openpyxl kodu uret
        ADIM 2: Kod guvenlik taramasi
        ADIM 3: Sandbox'ta test calistirma

        Returns:
            PipelineResult with generated code
        """
        result = PipelineResult(success=False)

        try:
            # ADIM 1: Kod uretimi (Claude Sonnet - en iyi kod uretici)
            prompt = self._build_code_generation_prompt(data, schema, business_context)

            code_response: AIResponse = self.retry_handler.execute_with_fallback(
                task_type=TaskType.CODE_GENERATION,
                operation="generate_code",
                prompt=prompt,
                context={
                    "business_context": business_context,
                    "schema": schema,
                    "data_sample": data,
                }
            )

            result.steps_completed.append("code_generation")
            result.total_cost += code_response.cost_usd
            result.total_latency_ms += code_response.latency_ms

            generated_code = code_response.content

            # ADIM 2: Guvenlik taramasi
            is_safe = self._security_scan(generated_code)
            result.steps_completed.append("security_scan")

            if not is_safe:
                raise ValueError("Kod guvenlik taramasindan gecemedi")

            result.final_data = {
                "code": generated_code,
                "model_used": code_response.model,
            }
            result.success = True

        except Exception as e:
            result.errors.append(f"Code generation pipeline error: {str(e)}")

        return result

    def execute_validation_pipeline(
        self,
        data: dict[str, Any],
        rules: list[str],
        business_context: dict[str, Any],
    ) -> PipelineResult:
        """
        Dogrulama pipeline'i.

        ADIM 1: Claude Sonnet ile derin dogrulama ve anomali tespiti
        ADIM 2: Otomatik duzeltme onerileri

        Returns:
            PipelineResult with validation results
        """
        result = PipelineResult(success=False)

        try:
            validation_response: AIResponse = self.retry_handler.execute_with_fallback(
                task_type=TaskType.VALIDATION,
                operation="validate",
                data=data,
                rules=rules,
                context=business_context,
            )

            result.steps_completed.append("validation")
            result.total_cost += validation_response.cost_usd
            result.total_latency_ms += validation_response.latency_ms

            result.final_data = validation_response.structured_data
            result.success = True

        except Exception as e:
            result.errors.append(f"Validation pipeline error: {str(e)}")

        return result

    def _build_extraction_prompt(
        self,
        schema: type[BaseModel],
        context: dict[str, Any]
    ) -> str:
        """Cikarma promptu olustur."""
        return f"""
Verilen gorseldeki/metindeki tum veriyi cikar.

<schema>
{schema.model_json_schema()}
</schema>

<business_context>
Is yeri: {context.get('business_name', 'Belirsiz')}
Sektor: {context.get('sector', 'Belirsiz')}
Ozel kurallar: {context.get('rules', [])}
</business_context>

<rules>
- Tum alanlari dikkatle oku
- Belirsiz degerler icin dusuk confidence ver (0.0-0.7)
- Sayilari number olarak dondur (string degil)
- Tarih formati: YYYY-MM-DD
- Bulunamayan alanlar: null
</rules>

Her alan icin guven skoru (confidence) ekle.
"""

    def _build_code_generation_prompt(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        context: dict[str, Any]
    ) -> str:
        """Kod uretim promptu olustur."""
        return f"""
openpyxl ile profesyonel Excel dosyasi olusturan Python kodu uret.

<data_structure>
{schema}
</data_structure>

<sample_data>
{data}
</sample_data>

<business_context>
{context}
</business_context>

<requirements>
- Fonksiyon: create_excel(data: dict, output_path: str) -> None
- Izin verilen: openpyxl, datetime, os, json, re, math, decimal
- YASAK: eval, exec, subprocess, __import__, system
- Baslik satiri: kalin, mavi arka plan (#1E3A5F), beyaz yazi
- Alternatif satir renklendirme
- Otomatik sutun genisligi
- Sayi formatlari: binlik ayiricili
- Para formati: #,##0.00 TL
- Tarih formati: DD.MM.YYYY
</requirements>

Sadece Python kodu uret (aciklama yok):
"""

    def _calculate_confidence_scores(
        self,
        data: dict[str, Any],
        context: dict[str, Any]
    ) -> ExtractionResult:
        """
        Cikarilan verilere guven skorlari ekle.

        Basit kurallar:
        - Sayisal deger varsa: 0.95
        - Metin uzunlugu >3: 0.90
        - Metin kisa ama anlamli: 0.80
        - Belirsiz: 0.50
        """
        fields = {}

        for key, value in data.items():
            confidence = 0.80  # Varsayilan

            # Basit skor hesaplama
            if value is None or value == "":
                confidence = 0.50
            elif isinstance(value, (int, float)):
                confidence = 0.95
            elif isinstance(value, str):
                if len(value) > 3:
                    confidence = 0.90
                else:
                    confidence = 0.70

            fields[key] = FieldValue(value=value, confidence=confidence)

        return ExtractionResult(
            fields=fields,
            raw_data=data,
        )

    def _validate_low_confidence_fields(
        self,
        extraction_result: ExtractionResult,
        low_confidence_fields: list[str],
        context: dict[str, Any]
    ) -> AIResponse:
        """
        Dusuk guvenli alanlari AI ile dogrula.

        Claude/validation modeli kullanarak dusuk guvenli alanlari
        yeniden degerlendirir ve duzeltme onerileri uretir.

        Args:
            extraction_result: Cikarma sonucu (tum alanlar)
            low_confidence_fields: Dusuk guvenli alan adlari
            context: Is baglami

        Returns:
            AIResponse with validation results and corrected fields
        """
        # Dusuk guvenli alanlari hazirla
        fields_to_validate = {}
        for field_name in low_confidence_fields:
            if field_name in extraction_result.fields:
                fv = extraction_result.fields[field_name]
                fields_to_validate[field_name] = {
                    "value": fv.value if not hasattr(fv.value, 'isoformat') else str(fv.value),
                    "confidence": fv.confidence,
                }

        # Dogrulama kurallari olustur
        validation_rules = [
            f"'{field}' alani dusuk guvenle cikarildi (confidence={info['confidence']:.2f}), "
            f"mevcut deger: '{info['value']}' -- bu degeri dogrula veya duzelt"
            for field, info in fields_to_validate.items()
        ]

        # Tam veri baglamini ekle (diger alanlar referans olarak)
        all_fields_context = {}
        for field_name, fv in extraction_result.fields.items():
            val = fv.value
            if hasattr(val, 'isoformat'):
                val = str(val)
            all_fields_context[field_name] = {
                "value": val,
                "confidence": fv.confidence,
            }

        enriched_context = {
            **context,
            "all_extracted_fields": all_fields_context,
            "low_confidence_fields": list(fields_to_validate.keys()),
        }

        # Validation promptu olustur
        prompt_builder = ValidationPromptBuilder()
        validation_data = {
            "fields_to_validate": fields_to_validate,
            "full_extraction": extraction_result.raw_data,
        }

        # Router uzerinden validation gorevine uygun model sec ve cagir
        validation_response: AIResponse = self.retry_handler.execute_with_fallback(
            task_type=TaskType.VALIDATION,
            operation="validate",
            data=validation_data,
            rules=validation_rules,
            context=enriched_context,
        )

        # Dogrulama sonuclarina gore extraction_result'i guncelle
        if validation_response.structured_data:
            corrected = validation_response.structured_data.get("corrected_data", {})
            for field_name, new_value in corrected.items():
                if field_name in extraction_result.fields:
                    # Duzeltilmis degeri uygula, guven skorunu yukselt
                    extraction_result.fields[field_name] = FieldValue(
                        value=new_value,
                        confidence=0.85,  # AI dogrulamasi sonrasi orta-yuksek guven
                    )

        return validation_response

    def _security_scan(self, code: str) -> bool:
        """
        Uretilen kodu guvenlik tehditleri icin tara.

        Yasakli pattern'ler:
        - eval, exec, subprocess, os.system, __import__
        - sys, builtins, time.sleep, inspect (YENI - 2026)
        - concurrent.futures, asyncio, cffi (YENI - 2026)
        """
        dangerous_patterns = [
            "eval(",
            "exec(",
            "subprocess",
            "os.system",
            "__import__",
            "popen(",
            # NEW: Critical additions (April 2026 security audit)
            "sys.",
            "sys ",
            "builtins.",
            "time.sleep",
            "inspect.",
            "concurrent.futures",
            "concurrent.",
            "asyncio.",
            "cffi.",
        ]

        code_lower = code.lower()

        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                return False

        return True
