"""Algoritma (iş akışı) üretimi iş mantığı."""
import json
import tempfile
import os
from typing import Optional

from core.database import (
    get_functionality_by_id,
    get_failed_algorithm_attempts,
    save_algorithm_attempt,
    save_algorithm_success,
)
from core.algorithm_runner import save_algorithm_file, test_algorithm
from core.models import TaskType
from ai.prompts.generation import AlgorithmPromptBuilder
from core.enrichment import _parse_json_response


def generate_algorithm(func_id: int, router, user_feedback: str = None) -> dict:
    """
    İş tanımı için create_excel algoritması üret.

    Args:
        func_id: İş tanımı ID
        router: ModelRouter instance
        user_feedback: Kullanıcının eksikler/önerileri (varsa)

    Returns:
        {
            "success": bool,
            "code": str or None,
            "version": int or None,
            "error": str or None,
            "failure_report": dict or None,
        }
    """
    func = get_functionality_by_id(func_id)
    if not func:
        return _fail("İş tanımı bulunamadı")

    # Zenginleştirilmiş tanım zorunlu
    enriched_raw = func.get("enriched_definition")
    if not enriched_raw:
        return _fail("İş tanımı henüz zenginleştirilmemiş. Lütfen önce zenginleştirin.")

    try:
        enriched = json.loads(enriched_raw) if isinstance(enriched_raw, str) else enriched_raw
    except (json.JSONDecodeError, TypeError):
        return _fail("Zenginleştirilmiş tanım JSON olarak okunamadı")

    # Geçmiş başarısız denemeleri al
    failed_attempts = get_failed_algorithm_attempts(func_id)

    # Kullanıcı geri bildirimi varsa son denemeye ekle
    if user_feedback and failed_attempts:
        # Son denemeye feedback ekle (prompt'ta görünecek)
        failed_attempts[-1]["user_feedback"] = user_feedback

    # Prompt oluştur
    if failed_attempts:
        prompt = AlgorithmPromptBuilder.build_algorithm_iteration(
            enriched_definition=enriched,
            failed_attempts=failed_attempts,
        )
    else:
        prompt = AlgorithmPromptBuilder.build_algorithm_generation(
            enriched_definition=enriched,
        )

    # AI çağrısı — Claude Sonnet (kod üretimi)
    try:
        model = router.select_model(
            TaskType.CODE_GENERATION,
            prefer_cost_optimization=False,
        )
        response = model.raw_generate(prompt=prompt, max_tokens=16384)
        raw_content = response.content

        # JSON parse
        result = _parse_json_response(raw_content)
        if not result:
            # JSON parse edilemedi — ham yanıttan kod çıkarmayı dene
            code = _extract_code_from_response(raw_content)
            if code:
                result = {"status": "success", "code": code,
                          "test_summary": {}, "notlar": "JSON parse edilemedi, kod çıkarıldı"}
            else:
                save_algorithm_attempt(
                    func_id, raw_content, status="failed",
                    ai_failure_report=json.dumps({"error": "JSON parse hatası"}),
                    user_feedback=user_feedback,
                )
                return _fail("AI yanıtı JSON olarak parse edilemedi")

        status = result.get("status", "failure")

        if status == "success":
            code = result.get("code", "")
            if not code:
                return _fail("AI başarılı dedi ama kod boş")

            # İmza kontrolü — AI bazen data parametresini atlar
            code = _ensure_correct_signature(code)

            # Güvenlik taraması + test
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                test_ok, test_error = test_algorithm(code, tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            if not test_ok:
                # Test başarısız — kaydet ve hata dön
                save_algorithm_attempt(
                    func_id, code, status="failed",
                    test_results=test_error,
                    user_feedback=user_feedback,
                )
                return {
                    "success": False,
                    "code": code,
                    "version": None,
                    "error": f"Kod testlerden geçemedi: {test_error}",
                    "failure_report": result,
                }

            # Başarılı — dosyaya kaydet
            algorithm_path = save_algorithm_file(func_id, code)
            test_summary = json.dumps(result.get("test_summary", {}), ensure_ascii=False)
            version = save_algorithm_success(func_id, algorithm_path, code, test_summary)

            return {
                "success": True,
                "code": code,
                "version": version,
                "error": None,
                "failure_report": None,
            }

        else:
            # AI başarısız olduğunu bildirdi
            son_kod = result.get("son_kod", "")
            save_algorithm_attempt(
                func_id, son_kod, status="failed",
                test_results=json.dumps(result.get("basarisiz_testler", []), ensure_ascii=False),
                ai_failure_report=json.dumps(result, ensure_ascii=False),
                user_feedback=user_feedback,
            )
            return {
                "success": False,
                "code": son_kod,
                "version": None,
                "error": result.get("oneri", "AI algoritma üretemedi"),
                "failure_report": result,
            }

    except Exception as e:
        return _fail(str(e))


def _ensure_correct_signature(code: str) -> str:
    """
    create_excel fonksiyon imzasını zorunlu formata düzelt.
    AI bazen data parametresini atlayıp sadece output_path üretebiliyor.
    Beklenen imza: create_excel(data: dict, output_path: str) -> None
    """
    import re

    # İmza zaten doğruysa dokunma
    if re.search(r'def create_excel\s*\(\s*data\s*[,:]', code):
        return code

    # Yanlış imzayı düzelt (data parametresi eksik)
    fixed = re.sub(
        r'def create_excel\s*\([^)]*\)(\s*->.*?)?:',
        'def create_excel(data: dict, output_path: str) -> None:',
        code,
        count=1,
    )
    return fixed


def _fail(error: str) -> dict:
    return {
        "success": False,
        "code": None,
        "version": None,
        "error": error,
        "failure_report": None,
    }


def _extract_code_from_response(text: str) -> Optional[str]:
    """AI yanıtından Python kodunu çıkar."""
    import re

    # ```python ... ``` bloğu ara
    match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if "def create_excel" in code:
            return code

    # def create_excel ile başlayan kısmı bul
    idx = text.find("def create_excel")
    if idx >= 0:
        # Öncesindeki import satırlarını da al
        lines = text[:idx].split("\n")
        import_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith(("from ", "import ")) or stripped == "":
                import_lines.insert(0, line)
            else:
                break

        # create_excel fonksiyonunun sonunu bul
        remaining = text[idx:]
        # Fonksiyon sonu: bir sonraki top-level tanım veya dosya sonu
        end_match = re.search(r'\n(?=\S)', remaining[1:])
        if end_match:
            func_code = remaining[:end_match.start() + 1]
        else:
            func_code = remaining

        return "\n".join(import_lines) + "\n" + func_code

    return None
