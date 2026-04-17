"""Uygulama konfigürasyonu — API anahtarları ve ayarlar."""
from __future__ import annotations
import json
import os
from core.models import APIConfig

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", ".api_keys.json")


def load_config() -> APIConfig:
    """
    API config'i yükle.

    Öncelik sırası:
    1. Environment variables (GEMINI_API_KEY, CLAUDE_API_KEY, OPENAI_API_KEY)
    2. .api_keys.json dosyası
    3. Varsayılan (boş)
    """
    # Environment variables'dan oku
    config = APIConfig(
        gemini_key=os.getenv("GEMINI_API_KEY", ""),
        claude_key=os.getenv("CLAUDE_API_KEY", ""),
        openai_key=os.getenv("OPENAI_API_KEY", ""),
    )

    # Eğer env'de yoksa dosyadan oku
    if not config.gemini_key and not config.claude_key and not config.openai_key:
        if os.path.exists(_CONFIG_FILE):
            try:
                with open(_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                config = APIConfig(**data)
            except Exception:
                pass

    return config


def save_config(config: APIConfig) -> None:
    """API config'i JSON olarak kaydet."""
    data = config.model_dump()
    with open(_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def mask_key(key: str) -> str:
    """API anahtarını maskele."""
    if not key or len(key) < 12:
        return "Ayarlanmamış"
    return f"{key[:8]}...{key[-4:]}"
