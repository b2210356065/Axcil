"""Kayıtlı algoritmaları güvenli çalıştırır."""
import os

from excel_engine.sandbox import CodeSandbox, SecurityViolation


ALGORITHMS_DIR = os.path.join(os.path.dirname(__file__), "..", "algorithms")


def get_algorithm_path(func_id: int) -> str:
    """Algoritma dosya yolunu döndür."""
    return os.path.join(ALGORITHMS_DIR, f"func_{func_id}.py")


def algorithm_exists(func_id: int) -> bool:
    """Algoritma dosyası var mı?"""
    return os.path.exists(get_algorithm_path(func_id))


def save_algorithm_file(func_id: int, code: str) -> str:
    """Algoritma kodunu dosyaya kaydet. Yolu döndürür."""
    os.makedirs(ALGORITHMS_DIR, exist_ok=True)
    path = get_algorithm_path(func_id)

    # Mevcut dosyayı yedekle
    if os.path.exists(path):
        backup = path.replace(".py", "_backup.py")
        try:
            os.replace(path, backup)
        except OSError:
            pass

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path


def run_algorithm(func_id: int, data: dict, output_path: str) -> str:
    """
    İş tanımı için kayıtlı algoritmayı çalıştır.

    Args:
        func_id: İş tanımı ID'si
        data: {"satirlar": [...]} formatında veri
        output_path: Excel çıktı yolu

    Returns:
        Oluşturulan dosya yolu

    Raises:
        FileNotFoundError: Algoritma dosyası yoksa
        SecurityViolation: Güvenlik ihlali
        RuntimeError: Kod çalıştırma hatası
    """
    path = get_algorithm_path(func_id)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Algoritma dosyası bulunamadı: func_{func_id}.py. "
            f"Lütfen iş akışını oluşturun."
        )

    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # Her çalıştırmada güvenlik kontrolü
    is_safe, error = CodeSandbox.validate_code(code)
    if not is_safe:
        raise SecurityViolation(f"Algoritma güvenlik kontrolünden geçemedi: {error}")

    # Sandbox içinde çalıştır
    CodeSandbox.execute_safe(
        code=code,
        function_name="create_excel",
        kwargs={"data": data, "output_path": output_path},
    )

    return output_path


def test_algorithm(code: str, output_path: str) -> tuple:
    """
    Algoritma kodunu boş veri ile test et.

    Returns:
        (success: bool, error_message: str or None)
    """
    # Güvenlik kontrolü
    is_safe, error = CodeSandbox.validate_code(code)
    if not is_safe:
        return False, f"Güvenlik ihlali: {error}"

    # Boş veri ile test
    try:
        CodeSandbox.execute_safe(
            code=code,
            function_name="create_excel",
            kwargs={"data": {"satirlar": []}, "output_path": output_path},
        )
    except Exception as e:
        return False, f"Boş veri testi başarısız: {e}"

    # Tek satırlık veri ile test
    try:
        CodeSandbox.execute_safe(
            code=code,
            function_name="create_excel",
            kwargs={
                "data": {"satirlar": [{"Test": "değer", "Sayı": 100}]},
                "output_path": output_path,
            },
        )
    except Exception as e:
        return False, f"Tek satır testi başarısız: {e}"

    return True, None
