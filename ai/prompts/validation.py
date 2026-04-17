"""Doğrulama ve anomali tespiti prompt şablonları."""
from typing import Any, Optional


class ValidationPromptBuilder:
    """
    Veri doğrulama promptları.

    Claude Sonnet için optimize edilmiş - en iyi muhakeme.
    """

    @staticmethod
    def build_basic_validation(
        data: dict[str, Any],
        validation_rules: list[str],
        business_context: dict[str, Any]
    ) -> str:
        """
        Temel doğrulama promptu.

        Args:
            data: Doğrulanacak veri
            validation_rules: İş kuralları
            business_context: İş bağlamı

        Returns:
            Doğrulama promptu
        """
        prompt = f"""
Sen bir veri kalite kontrol uzmanısın. Verilen veriyi iş kurallarına göre doğrula.

<data_to_validate>
{data}
</data_to_validate>

<validation_rules>
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(validation_rules))}
</validation_rules>

<business_context>
İş yeri: {business_context.get('business_name', 'Belirsiz')}
Sektör: {business_context.get('sector', 'Belirsiz')}
Normal değer aralıkları: {business_context.get('normal_ranges', 'Belirlenmemiş')}
</business_context>

<validation_types>
Şu kontrolleri yap:

1. MATEMATIKSEL TUTARLILIK:
   - Toplamlar doğru hesaplanmış mı?
   - Yüzdeler mantıklı mı (0-100 arası)?
   - Ara toplam + KDV = Genel Toplam?

2. FORMAT UYUMU:
   - Tarihler geçerli mi? (1900-2100 arası, gelecek tarih kontrolü)
   - Sayılar pozitif mi? (negatif değer anormal)
   - Para birimleri tutarlı mı?

3. MANTIKSAL TUTARLILIK:
   - Gelecek tarihli kayıt var mı?
   - Anormal büyük/küçük değerler var mı?
   - Zorunlu alanlar dolu mu?

4. ANOMALİ TESPİTİ:
   - Normal aralığın dışında değer var mı?
   - Tekrar eden kayıtlar var mı?
   - Şüpheli pattern'ler var mı?

5. İŞ KURALLARINA UYGUNLUK:
   - Sektörel kurallar ihlal edilmiş mi?
   - Yasal gereklilikler karşılanıyor mu?
</validation_types>

<output_format>
Her alan için ValidationIssue formatında yanıt ver:

{{
  "is_valid": true/false,
  "issues": [
    {{
      "field": "alan_adı",
      "status": "error" / "warning",
      "message": "Sorun açıklaması",
      "suggestion": "Düzeltme önerisi (varsa)"
    }}
  ],
  "corrected_data": {{}} // Otomatik düzeltilmiş veri (varsa)
}}

"error" = Kritik hata, düzeltilmeli
"warning" = Uyarı, kontrol edilmeli ama kabul edilebilir
</output_format>

Derin analiz yap ve ValidationResult döndür:
"""
        return prompt

    @staticmethod
    def build_anomaly_detection(
        data: dict[str, Any],
        historical_data: Optional[list[dict]] = None,
        business_context: dict[str, Any] = None
    ) -> str:
        """
        Anomali tespiti promptu.

        Geçmiş veriyle karşılaştırarak anormal pattern'leri tespit eder.
        """
        historical_section = ""
        if historical_data:
            historical_section = f"""
<historical_data>
Geçmiş kayıtlar (referans için):
{historical_data[:10]}  # İlk 10 kayıt
</historical_data>
"""

        prompt = f"""
Sen bir veri anomali tespit uzmanısın. Statistical ve pattern-based analiz yapıyorsun.

<current_data>
{data}
</current_data>

{historical_section}

<anomaly_detection_methods>
1. STATISTICAL OUTLIERS:
   - Z-score analizi (±3 standart sapma dışı)
   - IQR method (Q1-1.5*IQR, Q3+1.5*IQR)
   - Değer aralığı kontrolü (min-max beklenen)

2. PATTERN ANOMALIES:
   - Tekrar eden kayıtlar (duplicate detection)
   - Sıra dışı zaman serileri (zaman atlamaları)
   - Tutarsız kategoriler (beklenmeyen değerler)

3. BUSINESS LOGIC ANOMALIES:
   - Normal operasyon saatleri dışı işlemler
   - Olağandışı büyük işlemler
   - Sektörel standartların dışında değerler

4. RELATIONSHIP ANOMALIES:
   - İlişkili alanlar arasında tutarsızlık
   - Matematiksel ilişkilerde sapma
   - Beklenen oranların dışında değerler
</anomaly_detection_methods>

<context>
{business_context or {}}
</context>

Her tespit edilen anomali için:
- Anomali tipi
- Şiddet seviyesi (düşük/orta/yüksek)
- Açıklama
- Olası sebep
- Öneri

ValidationResult formatında döndür:
"""
        return prompt

    @staticmethod
    def build_consistency_check(
        data_list: list[dict],
        consistency_rules: list[str]
    ) -> str:
        """Birden fazla kaydın tutarlılık kontrolü."""
        prompt = f"""
Birden fazla veri kaydının tutarlılığını kontrol et.

<data_records>
{data_list}
</data_records>

<consistency_rules>
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(consistency_rules))}
</consistency_rules>

<checks>
1. FORMAT CONSISTENCY:
   - Aynı alan tüm kayıtlarda aynı formatta mı?
   - Tarih formatı tutarlı mı?
   - Sayı formatı tutarlı mı?

2. VALUE CONSISTENCY:
   - Kategoriler tutarlı mı? (yazım farklılıkları)
   - Birimler tutarlı mı? (adet, kg, lt)
   - Para birimleri tutarlı mı?

3. RELATIONAL CONSISTENCY:
   - İlişkili kayıtlar mantıklı mı?
   - Zaman sırası tutarlı mı?
   - Toplam değerler uyumlu mu?
</checks>

Tutarsızlıkları tespit et ve rapor ver:
"""
        return prompt

    @staticmethod
    def build_cove_verification(
        extracted_data: dict[str, Any],
        verification_questions: list[str]
    ) -> str:
        """
        Chain-of-Verification doğrulama promptu.

        Her soru için bağımsız doğrulama.
        """
        questions_section = "\n".join(
            f"{i+1}. {q}" for i, q in enumerate(verification_questions)
        )

        prompt = f"""
Çıkarılan veriyi doğrulamak için her soruyu BAĞIMSIZ olarak yanıtla.

<extracted_data>
{extracted_data}
</extracted_data>

<verification_questions>
{questions_section}
</verification_questions>

<instructions>
1. Her soruyu orijinal kaynağa göre kontrol et
2. Sadece kaynakta olan bilgiyi kullan
3. Çıkarılan veriye körü körüne güvenme
4. Tutarsızlık tespit edersen rapor et
5. Her soru için: "Evet/Hayır" + açıklama
</instructions>

Her soru için yanıt ver:
{{
  "question": "...",
  "answer": "Evet" / "Hayır",
  "explanation": "...",
  "issues_found": []  // Tutarsızlık varsa
}}
"""
        return prompt


# Yardımcı fonksiyonlar

def quick_validation_prompt(
    data: dict,
    rules: list[str],
    context: dict = None
) -> str:
    """Hızlı doğrulama promptu."""
    builder = ValidationPromptBuilder()
    return builder.build_basic_validation(
        data=data,
        validation_rules=rules,
        business_context=context or {}
    )


def quick_anomaly_prompt(
    data: dict,
    historical: list[dict] = None,
    context: dict = None
) -> str:
    """Hızlı anomali tespiti promptu."""
    builder = ValidationPromptBuilder()
    return builder.build_anomaly_detection(
        data=data,
        historical_data=historical,
        business_context=context or {}
    )
