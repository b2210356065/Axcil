"""Model-spesifik prompt sarmalayıcıları."""
from core.models import ModelProvider


class ModelSpecificWrapper:
    """
    Model-spesifik prompt formatlaması.

    Her AI modeli farklı prompt stilinden daha iyi sonuç alır:
    - Gemini: Minimal talimat, direkt şema
    - Claude: XML etiketli yapı
    - GPT: System message + detaylı talimat
    """

    @staticmethod
    def wrap_for_model(
        core_prompt: str,
        provider: ModelProvider,
        task_type: str = "extraction"
    ) -> str:
        """
        Çekirdek promptu model için optimize et.

        Args:
            core_prompt: Model-agnostik çekirdek prompt
            provider: Hedef AI provider
            task_type: Görev tipi

        Returns:
            Model için optimize edilmiş prompt
        """
        if provider == ModelProvider.GEMINI:
            return ModelSpecificWrapper._wrap_gemini(core_prompt, task_type)
        elif provider == ModelProvider.CLAUDE:
            return ModelSpecificWrapper._wrap_claude(core_prompt, task_type)
        elif provider == ModelProvider.OPENAI:
            return ModelSpecificWrapper._wrap_openai(core_prompt, task_type)
        else:
            return core_prompt  # Fallback: çekirdek prompt

    @staticmethod
    def _wrap_gemini(core_prompt: str, task_type: str) -> str:
        """
        Gemini için minimal sarmalama.

        Gemini minimal talimatlardan en iyi sonucu alır.
        Direkt şema + kısa talimat yeterli.
        """
        task_intros = {
            "extraction": "Veriyi çıkar ve şemaya uygun JSON döndür.",
            "generation": "İstenilen kodu üret.",
            "validation": "Veriyi doğrula ve sonucu JSON'da döndür.",
        }

        intro = task_intros.get(task_type, "Görevi tamamla.")

        wrapped = f"""{intro}

{core_prompt}

JSON çıktısını döndür:
"""
        return wrapped

    @staticmethod
    def _wrap_claude(core_prompt: str, task_type: str) -> str:
        """
        Claude için XML etiketli sarmalama.

        Claude XML yapısını tercih eder ve daha iyi parse eder.
        """
        task_roles = {
            "extraction": "Sen bir veri çıkarma uzmanısın.",
            "generation": "Sen bir yazılım mühendisisin.",
            "validation": "Sen bir veri kalite kontrol uzmanısın.",
        }

        role = task_roles.get(task_type, "Sen bir AI asistanısın.")

        # XML formatında yeniden yapılandır
        wrapped = f"""{role}

<task>
{task_type.capitalize()} görevi
</task>

<instructions>
{core_prompt}
</instructions>

<output_requirements>
- Yapılandırılmış format kullan
- Açık ve kesin ol
- Belirsizlik varsa belirt
</output_requirements>

Görevi tamamla:
"""
        return wrapped

    @staticmethod
    def _wrap_openai(core_prompt: str, task_type: str) -> str:
        """
        GPT için system-first sarmalama.

        GPT system message'da rol tanımı + detaylı talimatları tercih eder.
        """
        system_roles = {
            "extraction": "Sen profesyonel bir veri çıkarma uzmanısın. Metinden, görsellerden ve belgelerden yapılandırılmış veri çıkarırsın.",
            "generation": "Sen uzman bir Python geliştiricisisin. Özellikle openpyxl ile Excel otomasyon kodları yazarsın.",
            "validation": "Sen bir veri kalite kontrol uzmanısın. Verilerdeki hataları, tutarsızlıkları ve anomalileri tespit edersin.",
        }

        system_role = system_roles.get(task_type, "Sen yardımsever bir AI asistanısın.")

        # Not: Bu format daha sonra API çağrısında system message olarak kullanılacak
        wrapped = f"""SYSTEM: {system_role}

USER: {core_prompt}

Lütfen istenilen formatda yanıt ver.
"""
        return wrapped

    @staticmethod
    def extract_system_message(wrapped_prompt: str) -> tuple[str, str]:
        """
        GPT formatından system ve user message'ı ayır.

        Returns:
            (system_message, user_message)
        """
        if wrapped_prompt.startswith("SYSTEM:"):
            parts = wrapped_prompt.split("USER:", 1)
            if len(parts) == 2:
                system = parts[0].replace("SYSTEM:", "").strip()
                user = parts[1].strip()
                return system, user

        # System message yoksa
        return "", wrapped_prompt


# Kullanım örnekleri

def wrap_extraction_prompt(
    core_prompt: str,
    provider: ModelProvider
) -> str:
    """Çıkarma promptunu sarma."""
    return ModelSpecificWrapper.wrap_for_model(
        core_prompt=core_prompt,
        provider=provider,
        task_type="extraction"
    )


def wrap_code_prompt(
    core_prompt: str,
    provider: ModelProvider
) -> str:
    """Kod üretme promptunu sarma."""
    return ModelSpecificWrapper.wrap_for_model(
        core_prompt=core_prompt,
        provider=provider,
        task_type="generation"
    )


def wrap_validation_prompt(
    core_prompt: str,
    provider: ModelProvider
) -> str:
    """Doğrulama promptunu sarma."""
    return ModelSpecificWrapper.wrap_for_model(
        core_prompt=core_prompt,
        provider=provider,
        task_type="validation"
    )
