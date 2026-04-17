"""Prompt mühendisliği - İş tanımına göre sistem promptu oluşturma."""

import json


def build_system_prompt(business_profile, functionality):
    """İş yeri profili ve işlevsellik tanımına göre sistem promptu oluşturur."""

    input_fields = json.loads(functionality["input_fields"]) if isinstance(functionality["input_fields"], str) else functionality["input_fields"]
    excel_template = json.loads(functionality["excel_template"]) if isinstance(functionality["excel_template"], str) else functionality["excel_template"]

    prompt = f"""Sen bir Excel dosyası oluşturma uzmanısın. Aşağıdaki iş yeri ve işlevsellik tanımına göre, kullanıcının verdiği girdileri işleyerek openpyxl kütüphanesi ile Excel dosyası oluşturacak Python kodu üretmelisin.

## İş Yeri Bilgileri
- **İş Yeri Adı:** {business_profile['business_name']}
- **Sektör:** {business_profile.get('sector', 'Belirtilmemiş')}
- **İş Yeri Açıklaması:** {business_profile['business_description']}

## İşlevsellik Tanımı
- **İşlev Adı:** {functionality['name']}
- **İşlev Açıklaması:** {functionality['description']}

## Beklenen Girdi Alanları
{_format_input_fields(input_fields)}

## Excel Çıktı Formatı
{_format_excel_template(excel_template)}

## Kurallar
1. openpyxl kütüphanesini kullanarak Excel dosyası oluşturacak Python kodu üret.
2. Kod, `create_excel(data: dict, output_path: str)` adlı tek bir fonksiyon içermelidir.
3. `data` parametresi kullanıcının girdi alanlarını içeren bir sözlüktür.
4. Kodda hata yönetimi olmalıdır.
5. Excel dosyası profesyonel görünümlü olmalıdır (başlık stilleri, sütun genişlikleri, kenarlıklar).
6. Tarih, sayı ve para birimi formatları Türkçe standartlara uygun olmalıdır.
7. Sadece Python kodu üret, açıklama ekleme. Kod ```python ... ``` blokları içinde olmalıdır.
8. Eğer girdi verileri bir tablo/liste içeriyorsa, her satırı ayrı bir Excel satırına yaz.
9. Başlık satırını kalın, renkli arka planlı ve ortalanmış yap.
10. Sayfanın adını işlevsellik adına uygun şekilde belirle.

## Önemli
- Kod doğrudan çalıştırılabilir olmalıdır.
- Tüm Türkçe karakterler doğru şekilde desteklenmelidir.
- Sayısal veriler varsa toplam/özet satırları ekle.
- output_path parametresine dosyayı kaydet.
"""
    return prompt


def build_user_prompt(user_inputs, image_descriptions=None):
    """Kullanıcı girdilerinden kullanıcı promptu oluşturur."""

    prompt = "Aşağıdaki verileri kullanarak Excel dosyası oluşturacak Python kodunu üret:\n\n"
    prompt += "## Kullanıcı Verileri\n"

    for key, value in user_inputs.items():
        if value:
            prompt += f"- **{key}:** {value}\n"

    if image_descriptions:
        prompt += "\n## Görsellerden Elde Edilen Bilgiler\n"
        for i, desc in enumerate(image_descriptions, 1):
            prompt += f"- **Görsel {i}:** {desc}\n"

    prompt += "\n\nYukarıdaki verilere göre `create_excel(data, output_path)` fonksiyonunu içeren Python kodu üret."
    return prompt


def build_image_analysis_prompt():
    """Görsel analiz için sistem promptu."""
    return """Sen bir görsel analiz uzmanısın. Verilen görseli analiz et ve içindeki bilgileri yapılandırılmış metin olarak çıkar.

Özellikle şunlara dikkat et:
- Tablolar ve listeler
- Sayısal veriler
- Tarihler
- İsimler ve başlıklar
- Metin içerikleri

Çıktını düz metin olarak, anlaşılır ve yapılandırılmış şekilde ver."""


def generate_auto_system_prompt(business_name, business_desc, func_name, func_desc, input_fields, excel_config):
    """Kullanıcının tanımlarına göre otomatik sistem promptu oluşturur.
    Bu, kullanıcıya öneri olarak sunulur."""

    input_list = "\n".join([f"  - {f['name']}: {f['type']} - {f.get('description', '')}" for f in input_fields])

    sheets_desc = ""
    for sheet in excel_config.get("sheets", []):
        cols = ", ".join([c["name"] for c in sheet.get("columns", [])])
        sheets_desc += f"  - Sayfa: {sheet['name']} | Sütunlar: {cols}\n"

    prompt = f"""Sen "{business_name}" iş yeri için "{func_name}" işlevini yerine getiren bir Excel oluşturma asistanısın.

İş Yeri: {business_desc}

İşlev: {func_desc}

Kullanıcıdan alınacak girdiler:
{input_list}

Oluşturulacak Excel yapısı:
{sheets_desc}

Bu girdileri alarak, iş mantığına uygun şekilde openpyxl ile Excel dosyası oluşturacak Python kodu üretmelisin.
Kod `create_excel(data: dict, output_path: str)` fonksiyonunu içermelidir.
Profesyonel formatlama, Türkçe karakter desteği ve hata yönetimi zorunludur."""

    return prompt


def _format_input_fields(fields):
    if not fields:
        return "Belirtilmemiş"
    lines = []
    for f in fields:
        line = f"- **{f['name']}** ({f['type']})"
        if f.get("description"):
            line += f": {f['description']}"
        if f.get("required"):
            line += " *(zorunlu)*"
        lines.append(line)
    return "\n".join(lines)


def _format_excel_template(template):
    if not template:
        return "Belirtilmemiş"
    lines = []
    for sheet in template.get("sheets", []):
        lines.append(f"### Sayfa: {sheet['name']}")
        if sheet.get("columns"):
            lines.append("| Sütun Adı | Veri Tipi | Açıklama |")
            lines.append("|-----------|-----------|----------|")
            for col in sheet["columns"]:
                lines.append(f"| {col['name']} | {col.get('type', 'text')} | {col.get('description', '')} |")
        lines.append("")
    return "\n".join(lines)
