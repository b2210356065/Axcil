"""Yapay zeka motoru - OpenAI API entegrasyonu ve kod üretimi."""

import os
import re
import base64
from openai import OpenAI


def get_api_key():
    """API anahtarını ortam değişkeninden veya dosyadan alır."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        key_file = os.path.join(os.path.dirname(__file__), ".api_key")
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                key = f.read().strip()
    return key


def save_api_key(key):
    """API anahtarını dosyaya kaydeder."""
    key_file = os.path.join(os.path.dirname(__file__), ".api_key")
    with open(key_file, "w") as f:
        f.write(key)
    os.environ["OPENAI_API_KEY"] = key


def _get_client(api_key=None):
    """OpenAI istemcisi oluşturur."""
    key = api_key or get_api_key()
    if not key:
        raise ValueError("API anahtarı bulunamadı. Lütfen ayarlardan API anahtarınızı girin.")
    return OpenAI(api_key=key)


def call_ai(system_prompt, user_prompt, api_key=None, model="gpt-4o-mini"):
    """OpenAI API'ye istek gönderir ve yanıtı döndürür."""
    client = _get_client(api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    return response.choices[0].message.content


def analyze_image(image_bytes, prompt, api_key=None, model="gpt-4o-mini"):
    """Görseli analiz eder ve metin açıklaması döndürür."""
    client = _get_client(api_key)

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                ],
            }
        ],
        max_tokens=2000,
    )

    return response.choices[0].message.content


def extract_python_code(ai_response):
    """AI yanıtından Python kodunu çıkarır."""
    pattern = r"```python\s*(.*?)```"
    matches = re.findall(pattern, ai_response, re.DOTALL)
    if matches:
        return matches[0].strip()

    pattern = r"```\s*(.*?)```"
    matches = re.findall(pattern, ai_response, re.DOTALL)
    if matches:
        return matches[0].strip()

    return ai_response.strip()


def execute_excel_code(code, data, output_path):
    """Üretilen Python kodunu güvenli bir şekilde çalıştırır."""
    # Tehlikeli modül kullanımını kontrol et
    import_pattern = r'(?:import|from)\s+([\w.]+)'
    imports = re.findall(import_pattern, code)
    for imp in imports:
        base_module = imp.split(".")[0]
        if base_module not in {"openpyxl", "datetime", "os", "json", "re", "math"}:
            raise SecurityError(f"Güvenlik: '{imp}' modülü kullanılamaz.")

    # Tehlikeli fonksiyon çağrılarını kontrol et
    dangerous_patterns = [
        r'\bexec\s*\(', r'\beval\s*\(', r'\b__import__\s*\(',
        r'\bsubprocess\b', r'\bsystem\s*\(', r'\bpopen\s*\(',
        r'\brmtree\b', r'\bunlink\s*\(', r'\bremove\s*\(',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            raise SecurityError("Güvenlik: Tehlikeli kod kalıbı tespit edildi.")

    # Kodu çalıştır
    namespace = {"data": data, "output_path": output_path}
    exec(code, namespace)

    if "create_excel" in namespace:
        namespace["create_excel"](data, output_path)
    else:
        raise RuntimeError("Üretilen kodda 'create_excel' fonksiyonu bulunamadı.")

    return output_path


class SecurityError(Exception):
    pass
