"""
AI Debug Logger — Tüm AI iletişimlerini şeffaf şekilde loglar.

Her AI çağrısında şunları kaydeder:
1. Gönderilen prompt (tam metin)
2. Kullanılan model ve parametreler
3. API'den dönen ham yanıt
4. Parsing/dönüştürme adımları ve sonuçları
5. Hatalar ve stack trace'ler
6. Zamanlama ve maliyet bilgileri

Loglar hem dosyaya hem de Streamlit session_state'e yazılır.
"""
import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Log dizini
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def _get_log_file() -> Path:
    """Günlük log dosyası yolu."""
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"ai_debug_{today}.jsonl"


def _safe_serialize(obj: Any, max_length: int = 50000) -> Any:
    """Objeyi JSON-serializable hale getir, çok büyükse kes."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        if isinstance(obj, str) and len(obj) > max_length:
            return obj[:max_length] + f"... [KESILDI, toplam {len(obj)} karakter]"
        return obj
    if isinstance(obj, bytes):
        return f"<bytes: {len(obj)} bytes>"
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v, max_length) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        serialized = [_safe_serialize(item, max_length) for item in obj[:100]]
        if len(obj) > 100:
            serialized.append(f"... [ve {len(obj) - 100} öğe daha]")
        return serialized
    if hasattr(obj, 'model_dump'):
        return _safe_serialize(obj.model_dump(), max_length)
    if hasattr(obj, '__dict__'):
        return _safe_serialize(obj.__dict__, max_length)
    return str(obj)[:max_length]


def _write_log(entry: dict) -> None:
    """Log girdisini JSONL dosyasına yaz."""
    try:
        log_file = _get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        print(f"[DEBUG LOGGER] Log yazma hatası: {e}")


def _add_to_session(entry: dict) -> None:
    """Log girdisini Streamlit session_state'e ekle (UI'da göstermek için)."""
    try:
        import streamlit as st
        if "ai_debug_logs" not in st.session_state:
            st.session_state.ai_debug_logs = []
        # Son 200 log tut (bellek tasarrufu)
        st.session_state.ai_debug_logs.append(entry)
        if len(st.session_state.ai_debug_logs) > 200:
            st.session_state.ai_debug_logs = st.session_state.ai_debug_logs[-200:]
    except Exception:
        pass  # Streamlit context dışında çalışıyorsa sessizce geç


class AIDebugLogger:
    """Her AI çağrısı için kullanılan debug logger."""

    def __init__(self, operation: str, provider: str = "", model: str = ""):
        self.operation = operation
        self.provider = provider
        self.model = model
        self.call_id = f"{datetime.now().strftime('%H%M%S%f')}_{operation}"
        self.start_time = time.time()
        self.entry = {
            "call_id": self.call_id,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "provider": provider,
            "model": model,
            "stages": [],
            "success": False,
            "error": None,
            "duration_ms": 0,
        }

    def log_stage(self, stage_name: str, data: Any = None, status: str = "ok") -> None:
        """Bir aşamayı logla (prompt oluşturma, API çağrısı, parsing, vs.)."""
        stage = {
            "stage": stage_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "elapsed_ms": int((time.time() - self.start_time) * 1000),
            "data": _safe_serialize(data),
        }
        self.entry["stages"].append(stage)

    def log_prompt(self, prompt: str, schema: Any = None, extra: dict = None) -> None:
        """Gönderilen promptu logla."""
        data = {
            "prompt_text": prompt,
            "prompt_length": len(prompt),
        }
        if schema is not None:
            if hasattr(schema, 'model_json_schema'):
                data["schema"] = _safe_serialize(schema.model_json_schema())
                data["schema_class"] = schema.__name__
            else:
                data["schema"] = _safe_serialize(schema)
        if extra:
            data["extra"] = _safe_serialize(extra)
        self.log_stage("prompt_sent", data)

    def log_api_request(self, request_body: Any = None, url: str = "", headers: dict = None) -> None:
        """API'ye gönderilen isteği logla."""
        data = {
            "url": url,
        }
        if request_body is not None:
            data["request_body"] = _safe_serialize(request_body)
        if headers:
            # API key'leri maskele
            safe_headers = {}
            for k, v in headers.items():
                if "key" in k.lower() or "auth" in k.lower() or "token" in k.lower():
                    safe_headers[k] = "***MASKED***"
                else:
                    safe_headers[k] = v
            data["headers"] = safe_headers
        self.log_stage("api_request", data)

    def log_api_response(self, response: Any = None, status_code: int = 0,
                         raw_text: str = "", tokens: dict = None) -> None:
        """API'den dönen ham yanıtı logla."""
        data = {
            "status_code": status_code,
            "raw_response_text": raw_text[:20000] if raw_text else "",
            "raw_response_length": len(raw_text) if raw_text else 0,
        }
        if tokens:
            data["tokens"] = tokens
        if response is not None and response != raw_text:
            data["parsed_response"] = _safe_serialize(response)
        self.log_stage("api_response", data)

    def log_parsing(self, step: str, input_data: Any = None,
                    output_data: Any = None, error: str = None) -> None:
        """Yanıt parsing/dönüştürme adımını logla."""
        data = {
            "parsing_step": step,
        }
        if input_data is not None:
            data["input"] = _safe_serialize(input_data, max_length=10000)
        if output_data is not None:
            data["output"] = _safe_serialize(output_data, max_length=10000)
        if error:
            data["error"] = error
        status = "error" if error else "ok"
        self.log_stage(f"parsing_{step}", data, status=status)

    def log_schema_validation(self, schema_class: str, data: Any,
                              result: Any = None, error: str = None) -> None:
        """Pydantic şema doğrulamasını logla."""
        log_data = {
            "schema_class": schema_class,
            "input_data": _safe_serialize(data, max_length=10000),
        }
        if result is not None:
            log_data["validation_result"] = _safe_serialize(result, max_length=10000)
        if error:
            log_data["validation_error"] = error
        status = "error" if error else "ok"
        self.log_stage("schema_validation", log_data, status=status)

    def log_code_execution(self, code: str, data: Any = None,
                           result: str = None, error: str = None) -> None:
        """Üretilen kodun çalıştırılmasını logla."""
        log_data = {
            "generated_code": code[:10000],
            "code_length": len(code),
        }
        if data is not None:
            log_data["input_data"] = _safe_serialize(data, max_length=5000)
        if result:
            log_data["result"] = result
        if error:
            log_data["error"] = error
            log_data["traceback"] = traceback.format_exc()
        status = "error" if error else "ok"
        self.log_stage("code_execution", log_data, status=status)

    def log_error(self, error: Exception, context: str = "") -> None:
        """Hata logla."""
        self.entry["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
        }
        self.entry["success"] = False

    def log_tool_use_response(self, tool_name: str, tool_input: Any,
                               raw_content: Any = None) -> None:
        """Claude tool_use yanıtını logla."""
        data = {
            "tool_name": tool_name,
            "tool_input": _safe_serialize(tool_input),
        }
        if raw_content is not None:
            data["raw_content_blocks"] = _safe_serialize(raw_content)
        self.log_stage("tool_use_response", data)

    def finish(self, success: bool = True, result: Any = None) -> dict:
        """Logu tamamla ve kaydet."""
        self.entry["success"] = success
        self.entry["duration_ms"] = int((time.time() - self.start_time) * 1000)
        if result is not None:
            self.entry["final_result"] = _safe_serialize(result, max_length=10000)

        _write_log(self.entry)
        _add_to_session(self.entry)

        return self.entry


def get_recent_logs(count: int = 50) -> list[dict]:
    """Son N log girdisini oku (en yeniden en eskiye)."""
    log_file = _get_log_file()
    if not log_file.exists():
        return []

    logs = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass

    return logs[-count:][::-1]  # En yeni en üstte


def get_session_logs() -> list[dict]:
    """Streamlit session'daki logları döndür."""
    try:
        import streamlit as st
        return list(reversed(st.session_state.get("ai_debug_logs", [])))
    except Exception:
        return []


def clear_session_logs() -> None:
    """Session loglarını temizle."""
    try:
        import streamlit as st
        st.session_state.ai_debug_logs = []
    except Exception:
        pass
