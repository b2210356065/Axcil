"""Code Sandbox — AI ürettiği kodu güvenli şekilde çalıştırır."""
import ast
import re
from typing import Any, Optional


class SecurityViolation(Exception):
    """Güvenlik ihlali hatası."""
    pass


class CodeSandbox:
    """
    Güvenli kod çalıştırma ortamı.

    AI'ın ürettiği Python kodunu güvenlik kontrollerinden geçirir
    ve kısıtlı bir ortamda çalıştırır.

    Güvenlik katmanları:
    1. Statik analiz (AST parse)
    2. Yasaklı pattern taraması
    3. İzin verilen import kontrolü
    4. Restricted builtins
    """

    # Yasaklı modüller (sadece gerçekten tehlikeli olanlar)
    BLOCKED_IMPORTS = {
        "subprocess",
        "shutil",
        "importlib",
        "ctypes",
        "socket",
        "http",
        "urllib",
        "requests",
        "pickle",
        "shelve",
        "marshal",
        "code",
        "codeop",
        "compileall",
        "py_compile",
        "multiprocessing",
        "threading",
        "signal",
        "webbrowser",
        "smtplib",
        "ftplib",
        "telnetlib",
        # Üçüncü parti kütüphaneler (sandbox'ta yok, AI bazen kullanmaya çalışıyor)
        "pandas",
        "numpy",
        "xlsxwriter",
        "xlrd",
        "xlwt",

        # ============================================
        # NEWLY ADDED (April 2026 Security Audit)
        # ============================================

        # Interpreter control and sandbox escape
        "sys",          # Can exit interpreter (sys.exit()), modify sys.modules,
                        # manipulate sys.path to load malicious code, access stdin/stdout

        "builtins",     # Can override core functions like open(), __import__(), eval(),
                        # enabling complete sandbox escape. Critical threat.

        # C interoperability (similar to ctypes)
        "cffi",         # C Foreign Function Interface - can call arbitrary C functions,
                        # load shared libraries, bypass Python security. Same risk as ctypes.

        # Parallelism and resource exhaustion
        "concurrent",   # concurrent.futures can create thread/process pools for fork bombs
                        # and resource exhaustion attacks

        "asyncio",      # Async event loops can be abused for resource exhaustion,
                        # difficult to timeout, can block sandbox indefinitely

        # Timing attacks and DoS
        "time",         # time.sleep() enables DoS attacks (infinite sleep, tie up workers).
                        # NOTE: datetime module provides date/time functionality safely.
                        # time.time() is NOT needed in AI-generated code (adapters measure
                        # latency outside sandbox)

        # Runtime introspection
        "inspect",      # Can inspect runtime internals, read source code, access frame
                        # objects, potentially find secrets in memory or bypass security
    }

    # Yasaklı pattern'ler (tehlikeli kod kalıpları)
    FORBIDDEN_PATTERNS = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"compile\s*\(",
        # __import__ artık kontrollü safe_import ile izin veriliyor — pattern'den çıkarıldı
        r"subprocess",
        r"os\.system",
        r"os\.popen",
        r"os\.spawn",
        r"os\.exec",
        r"importlib",
        r"__builtins__",
        r"(?<!\w)open\s*\(",  # Dosya açma yasak (wb.save kullanılmalı) — method adı içindeki 'open'i atla
        r"file\s*\(",
        r"input\s*\(",  # Kullanıcı girdisi yasak
        r"raw_input\s*\(",

        # Newly added patterns (April 2026 Security Audit)
        r"\bsys\.",           # Match sys. with word boundary
        r"time\.sleep",       # Block sleep even if time somehow gets imported
        r"inspect\.",         # Block any inspect usage
        r"\bbuiltins\.",      # Block builtins access with word boundary
        r"concurrent\.futures",  # Block futures
        r"asyncio\.",         # Block asyncio usage
    ]

    # Yasaklı AST node tipleri
    FORBIDDEN_NODES = {
        ast.Global,      # Global değişken tanımlama
    }

    @staticmethod
    def validate_code(code: str) -> tuple[bool, Optional[str]]:
        """
        Kodu güvenlik açısından doğrula.

        Args:
            code: Python kodu

        Returns:
            (is_safe: bool, error_message: Optional[str])
        """
        # 1. Pattern taraması
        for pattern in CodeSandbox.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Yasaklı pattern bulundu: {pattern}"

        # 2. AST analizi
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Sözdizimi hatası: {e}"

        # 3. AST node kontrolü
        for node in ast.walk(tree):
            # Yasaklı node tipleri
            if type(node) in CodeSandbox.FORBIDDEN_NODES:
                return False, f"Yasaklı AST node: {type(node).__name__}"

            # Import kontrolü — tehlikeli modülleri engelle
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if CodeSandbox._is_blocked_import(alias.name):
                        return False, f"Yasaklı import: {alias.name}"

            if isinstance(node, ast.ImportFrom):
                if node.module and CodeSandbox._is_blocked_import(node.module):
                    return False, f"Yasaklı import: {node.module}"

            # Attribute access kontrolü (tehlikeli attribute'lar)
            if isinstance(node, ast.Attribute):
                attr_name = node.attr
                dangerous_attrs = ["__dict__", "__class__", "__bases__", "__globals__"]
                if attr_name in dangerous_attrs:
                    return False, f"Tehlikeli attribute erişimi: {attr_name}"

        return True, None

    @staticmethod
    def _is_blocked_import(module_name: str) -> bool:
        """Import'un yasaklı listede olup olmadığını kontrol et."""
        root_module = module_name.split(".")[0]
        return root_module in CodeSandbox.BLOCKED_IMPORTS

    @staticmethod
    def execute_safe(
        code: str,
        function_name: str,
        args: tuple = (),
        kwargs: dict = None,
    ) -> Any:
        """
        Kodu güvenli ortamda çalıştır.

        Args:
            code: Python kodu (fonksiyon tanımı içermeli)
            function_name: Çağrılacak fonksiyon adı
            args: Pozisyonel argümanlar
            kwargs: Keyword argümanlar

        Returns:
            Fonksiyon çıktısı

        Raises:
            SecurityViolation: Güvenlik ihlali durumunda
            RuntimeError: Kod çalıştırma hatası
        """
        if kwargs is None:
            kwargs = {}

        # Güvenlik kontrolü
        is_safe, error = CodeSandbox.validate_code(code)
        if not is_safe:
            raise SecurityViolation(f"Güvenlik ihlali: {error}")

        # Kısıtlı builtins
        safe_builtins = CodeSandbox._create_safe_builtins()

        # Kısıtlı globals (sadece izin verilen modüller)
        safe_globals = {
            "__builtins__": safe_builtins,
        }

        # İzin verilen modülleri import et
        import openpyxl
        from openpyxl import styles, utils
        import datetime
        from datetime import date, timedelta
        import os.path
        import json
        import re
        import math
        from decimal import Decimal

        safe_globals.update({
            "openpyxl": openpyxl,
            "styles": styles,
            "utils": utils,
            "datetime": datetime,
            "date": date,
            "timedelta": timedelta,
            "os": type("os", (), {"path": os.path})(),  # Sadece os.path
            "json": json,
            "re": re,
            "math": math,
            "Decimal": Decimal,
        })

        # Kodu çalıştır
        try:
            exec(code, safe_globals)
        except Exception as e:
            raise RuntimeError(f"Kod çalıştırma hatası: {e}") from e

        # Fonksiyonu çağır
        if function_name not in safe_globals:
            raise RuntimeError(f"Fonksiyon bulunamadı: {function_name}")

        func = safe_globals[function_name]

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            raise RuntimeError(f"Fonksiyon çalıştırma hatası: {e}") from e

    @staticmethod
    def _create_safe_builtins() -> dict:
        """
        Kısıtlı builtins sözlüğü oluştur.

        Tehlikeli fonksiyonlar kaldırılmış, güvenli olanlar korunmuş.
        """
        safe_builtins = {
            # Temel tipler
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "set": set,
            "frozenset": frozenset,

            # Yardımcı fonksiyonlar
            "abs": abs,
            "all": all,
            "any": any,
            "enumerate": enumerate,
            "filter": filter,
            "len": len,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "round": round,
            "sorted": sorted,
            "sum": sum,
            "zip": zip,

            # Tip kontrolü
            "isinstance": isinstance,
            "issubclass": issubclass,
            "type": type,

            # String işlemleri
            "chr": chr,
            "ord": ord,

            # Container işlemleri
            "slice": slice,

            # Diğer
            "True": True,
            "False": False,
            "None": None,

            # YASAK: eval, exec, compile, open, file, input

            # Kontrollü __import__: sadece izin verilen modülleri import edebilir
            # AI kodu fonksiyon içinde "from openpyxl import X" yazabilir
            "__import__": CodeSandbox._make_safe_import(),
        }

        return safe_builtins

    @staticmethod
    def _make_safe_import():
        """Sadece izin verilen modülleri import edebilen kısıtlı __import__ fonksiyonu."""
        ALLOWED_MODULES = {
            "openpyxl", "openpyxl.styles", "openpyxl.utils", "openpyxl.worksheet",
            "openpyxl.chart", "openpyxl.formatting", "openpyxl.comments",
            "datetime", "json", "re", "math", "decimal", "os", "os.path",
            "typing", "collections",
        }

        _real_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            root = name.split(".")[0]
            # İzin verilen modül mü?
            if name in ALLOWED_MODULES or root in {m.split(".")[0] for m in ALLOWED_MODULES}:
                # Blocked imports listesini de kontrol et
                if root not in CodeSandbox.BLOCKED_IMPORTS:
                    return _real_import(name, globals, locals, fromlist, level)
            raise ImportError(f"Güvenlik: '{name}' modülü import edilemez. "
                              f"İzin verilen modüller: openpyxl, datetime, json, re, math, decimal, os.path")

        return safe_import


# Yardımcı fonksiyonlar

def quick_validate(code: str) -> bool:
    """
    Hızlı güvenlik kontrolü.

    Returns:
        True ise güvenli
    """
    is_safe, _ = CodeSandbox.validate_code(code)
    return is_safe


def safe_create_excel(code: str, data: dict, output_path: str) -> str:
    """
    AI kodunu güvenli çalıştırıp Excel oluştur.

    Args:
        code: AI'ın ürettiği create_excel fonksiyon kodu
        data: Excel verisi
        output_path: Çıktı yolu

    Returns:
        Oluşturulan dosya yolu

    Raises:
        SecurityViolation veya RuntimeError
    """
    sandbox = CodeSandbox()

    # Güvenlik kontrolü
    is_safe, error = sandbox.validate_code(code)
    if not is_safe:
        raise SecurityViolation(f"Kod güvensiz: {error}")

    # create_excel fonksiyonunu çalıştır
    sandbox.execute_safe(
        code=code,
        function_name="create_excel",
        kwargs={"data": data, "output_path": output_path}
    )

    return output_path
