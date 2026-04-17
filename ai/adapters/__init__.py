"""AI model adaptörleri — her provider için birleşik arayüz."""
from ai.adapters.base import BaseModelAdapter
from ai.adapters.gemini_adapter import GeminiAdapter
from ai.adapters.claude_adapter import ClaudeAdapter
from ai.adapters.openai_adapter import OpenAIAdapter

__all__ = [
    "BaseModelAdapter",
    "GeminiAdapter",
    "ClaudeAdapter",
    "OpenAIAdapter",
]
