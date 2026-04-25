# Pydantic + Python 3.9 Uyumsuzluk Hatasi

## Hata

```
AttributeError: '_SpecialForm' object has no attribute 'replace'
```

Tam traceback:
```
File "pydantic/json_schema.py", line 333, in build_schema_type_to_method
    method_name = f'{key.replace("-", "_")}_schema'
File "typing.py", line 647, in __getattr__
    return getattr(self.__origin__, attr)
AttributeError: '_SpecialForm' object has no attribute 'replace'
```

## Kök Neden

**Pydantic 2.12+ ile Python 3.9 arasinda uyumsuzluk.**

Pydantic 2.12 surumunden itibaren `pydantic-core` ve `typing_extensions`
bagimlilikları guncellendi. Bu guncellemeler Python 3.9'un `typing` modulundeki
`_SpecialForm` sinifiyla catisma olusturuyor.

### Teknik detay:

1. Pydantic'in `model_json_schema()` metodu cagrildiginda `build_schema_type_to_method()` cagirilir
2. Bu metot dahili schema tiplerini (`str`, `int`, `union`, vb.) bir sozlukte toplar
3. Her `key` bir string olmali ve uzerinde `.replace("-", "_")` yapilir
4. **Python 3.9 + Pydantic 2.12+ + typing_extensions 4.12+** kombinasyonunda
   sozluk anahtarlari arasina `typing.Union` gibi `_SpecialForm` nesneleri karisiyor
5. `_SpecialForm` nesneleri `str` degil, dolayisiyla `.replace()` metodu yok
6. Sonuc: `AttributeError: '_SpecialForm' object has no attribute 'replace'`

### Etkilenen ortam:

| Bilesen | Sorunlu versiyon | Calisan versiyon |
|---------|-----------------|------------------|
| Python | 3.9.x | 3.9.x |
| Pydantic | >= 2.12.0 | 2.10.x veya 2.11.x |
| pydantic-core | >= 2.33.0 | 2.27.x |
| typing_extensions | >= 4.12.0 | herhangi |

## Cozum

### Secenek 1: Pydantic'i downgrade et (ONERILEN)

```bash
pip install "pydantic>=2.5.0,<2.12.0"
```

Bu komut Pydantic 2.10.x veya 2.11.x yukleyecektir. Bu surumler
Python 3.9 ile tam uyumludur.

### Secenek 2: Python'u yukselt

```bash
# Python 3.10+ yukleyin
# Pydantic 2.12+ sorunsuz calisir
```

### Secenek 3: requirements.txt ayarlari

`requirements.txt` dosyasinda Pydantic versiyonu sabitlenmistir:

```
pydantic>=2.5.0,<2.12.0
```

Bu ayar Python 3.9 ile uyumlu en son Pydantic surumunu yukler.

## Kontrol

Duzeltme sonrasi asagidaki komutu calistirarak test edin:

```bash
python -c "
from pydantic import BaseModel, Field
from typing import List, Any

class Test(BaseModel):
    items: List[str] = Field(description='test')

print(Test.model_json_schema())
print('BASARILI!')
"
```

## Onemli notlar

- Bu hata SADECE `model_json_schema()` cagrildiginda ortaya cikar
- Model olusturma, validasyon gibi islemler etkilenmez
- Projede `model_json_schema()` su yerlerde kullanilir:
  - `ai/adapters/gemini_adapter.py` — Gemini response_schema icin
  - `ai/adapters/claude_adapter.py` — tool input_schema icin
  - `ai/adapters/openai_adapter.py` — JSON schema strict mode icin
  - `ai/pipeline.py` — extraction prompt schema icin
  - Tum tool dosyalari — prompt icinde schema gostermek icin
- Yani bu hata AI ile herhangi bir islem yapilamadigini gosterir
