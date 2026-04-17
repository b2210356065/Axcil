"""İş tanımı zenginleştirme iş mantığı."""
import json
from typing import Optional

from core.database import (
    get_functionality_by_id,
    get_rejected_enrichments,
    save_enrichment_attempt,
    accept_enrichment as db_accept_enrichment,
    reject_enrichment as db_reject_enrichment,
    get_all_data_types,
)
from core.models import TaskType
from ai.prompts.generation import EnrichmentPromptBuilder


def _get_data_type_names(func: dict) -> list[str]:
    """İş tanımından veri tipi isimlerini al."""
    raw = func.get("data_type_ids")
    ids = []
    if raw:
        if isinstance(raw, str):
            try:
                ids = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(raw, list):
            ids = raw

    if not ids:
        dtype_id = func.get("data_type_id", 3)
        ids = [dtype_id] if dtype_id else [3]

    all_types = get_all_data_types()
    type_map = {dt["id"]: dt["name"] for dt in all_types}
    return [type_map.get(did, "Bilinmiyor") for did in ids]


def enrich_functionality(func_id: int, router) -> dict:
    """
    İş tanımını AI ile zenginleştir.

    Returns:
        {"success": bool, "enriched": dict or None, "attempt_id": int, "error": str or None}
    """
    func = get_functionality_by_id(func_id)
    if not func:
        return {"success": False, "enriched": None, "attempt_id": None,
                "error": "İş tanımı bulunamadı"}

    # Geçmiş başarısız denemeleri al
    rejected = get_rejected_enrichments(func_id)
    data_type_names = _get_data_type_names(func)

    # Sektör bilgisi (iş yeri profilinden)
    from core.database import get_business_by_id
    business = get_business_by_id(func.get("business_id", 0))
    sector = business.get("sector", "Genel") if business else "Genel"

    # Prompt oluştur
    if rejected:
        prompt = EnrichmentPromptBuilder.build_iterative_enrichment(
            name=func["name"],
            description=func["description"],
            sector=sector,
            data_types=data_type_names,
            failed_attempts=rejected,
        )
    else:
        prompt = EnrichmentPromptBuilder.build_enrichment(
            name=func["name"],
            description=func["description"],
            sector=sector,
            data_types=data_type_names,
        )

    # AI çağrısı — Claude Sonnet tercih (yaratıcı görev)
    try:
        model = router.select_model(
            TaskType.COMPLEX_TRANSFORM,
            prefer_cost_optimization=False,
        )
        response = model.raw_generate(prompt=prompt, max_tokens=16384)
        raw_content = response.content

        # JSON parse
        enriched = _parse_json_response(raw_content)
        if not enriched:
            return {"success": False, "enriched": None, "attempt_id": None,
                    "error": "AI yanıtı JSON olarak parse edilemedi"}

        # DB'ye kaydet (henüz onaylanmadı)
        enriched_json = json.dumps(enriched, ensure_ascii=False)
        attempt_number = save_enrichment_attempt(func_id, enriched_json, status="pending")

        return {"success": True, "enriched": enriched,
                "attempt_id": attempt_number, "error": None}

    except Exception as e:
        return {"success": False, "enriched": None, "attempt_id": None,
                "error": str(e)}


def confirm_enrichment(func_id: int, enriched_definition: dict,
                       attempt_id: Optional[int] = None):
    """Kullanıcı zenginleştirilmiş tanımı onayladı."""
    enriched_json = json.dumps(enriched_definition, ensure_ascii=False)
    db_accept_enrichment(func_id, enriched_json, attempt_id)


def reject_enrichment_with_feedback(attempt_id: int, feedback: str):
    """Kullanıcı zenginleştirilmiş tanımı reddetti."""
    db_reject_enrichment(attempt_id, feedback)


def _parse_json_response(text: str) -> Optional[dict]:
    """AI yanıtından JSON çıkar.

    Strateji sırası:
    1. Doğrudan json.loads
    2. ```json ... ``` kod bloğu (greedy — en büyük bloğu yakala)
    3. En dıştaki { ... } eşleştirmesi (brace-depth)
    """
    if not text or not text.strip():
        return None

    # 1. Direkt JSON dene
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    import re

    # 2. ```json ... ``` bloğu ara — GREEDY (.*) kullan, büyük yanıtlarda lazy (.*?) erken durur
    #    Birden fazla blok varsa en uzununu al
    blocks = re.findall(r'```(?:json)?\s*\n(.*?)\n\s*```', text, re.DOTALL)
    if blocks:
        # En uzun bloğu dene (AI bazen birden fazla kod bloğu döner)
        for block in sorted(blocks, key=len, reverse=True):
            block = block.strip()
            if block:
                try:
                    return json.loads(block)
                except (json.JSONDecodeError, TypeError):
                    continue

    # 3. En dıştaki { ... } eşleştirmesi — string literal içindeki parantezleri atla
    start = text.find("{")
    if start >= 0:
        depth = 0
        in_string = False
        escape_next = False
        last_valid_end = -1

        for i in range(start, len(text)):
            ch = text[i]

            if escape_next:
                escape_next = False
                continue

            if ch == '\\' and in_string:
                escape_next = True
                continue

            if ch == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    last_valid_end = i
                    break

        if last_valid_end > start:
            try:
                return json.loads(text[start:last_valid_end + 1])
            except (json.JSONDecodeError, TypeError):
                pass

    return None
