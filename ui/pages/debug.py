"""AI Debug Log Goruntuleyici — tum AI iletisimlerini seffaf gosterir."""
import streamlit as st
import json
from core.debug_logger import get_recent_logs, get_session_logs, clear_session_logs


def show_debug_page():
    """AI debug loglarini gosteren sayfa."""
    st.markdown("### AI Debug Loglari")
    st.markdown("Tum AI cagrilarinin prompt, yanit, parsing ve hata detaylari.")

    # Kontroller
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        source = st.radio("Kaynak", ["Bu Oturum", "Dosya Loglari"], horizontal=True)
    with col2:
        if st.button("Oturum Loglarini Temizle"):
            clear_session_logs()
            st.rerun()
    with col3:
        filter_status = st.selectbox("Filtre", ["Tumu", "Sadece Hatalar", "Sadece Basarili"])

    st.divider()

    # Loglari al
    if source == "Bu Oturum":
        logs = get_session_logs()
    else:
        log_count = st.slider("Son kac log", 10, 200, 50)
        logs = get_recent_logs(log_count)

    # Filtrele
    if filter_status == "Sadece Hatalar":
        logs = [l for l in logs if not l.get("success", True)]
    elif filter_status == "Sadece Basarili":
        logs = [l for l in logs if l.get("success", False)]

    if not logs:
        st.info("Henuz log yok. Bir AI araci kullandiginizda loglar burada gorunecek.")
        return

    # Ozet istatistikler
    total = len(logs)
    failed = sum(1 for l in logs if not l.get("success", True))
    success = total - failed

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam Cagri", total)
    with col2:
        st.metric("Basarili", success)
    with col3:
        st.metric("Basarisiz", failed)

    st.divider()

    # Her log icin kart
    for idx, log in enumerate(logs):
        is_error = not log.get("success", True)
        status_icon = "X" if is_error else "OK"
        status_color = "red" if is_error else "green"

        # Baslik
        provider = log.get("provider", "?")
        operation = log.get("operation", "?")
        model = log.get("model", "?")
        duration = log.get("duration_ms", 0)
        timestamp = log.get("timestamp", "?")

        header = f"[{status_icon}] {provider}/{operation} | {model} | {duration}ms | {timestamp}"

        with st.expander(header, expanded=is_error):
            # Hata bilgisi (varsa, en uste)
            error_info = log.get("error")
            if error_info:
                st.error(f"**Hata Tipi:** {error_info.get('type', '?')}")
                st.error(f"**Mesaj:** {error_info.get('message', '?')}")
                st.error(f"**Baglam:** {error_info.get('context', '?')}")
                if error_info.get("traceback"):
                    with st.expander("Traceback (tam hata izleme)"):
                        st.code(error_info["traceback"], language="python")

            # Asamalar (stages)
            stages = log.get("stages", [])
            if stages:
                st.markdown("#### Asamalar")
                for stage in stages:
                    stage_name = stage.get("stage", "?")
                    stage_status = stage.get("status", "ok")
                    elapsed = stage.get("elapsed_ms", 0)

                    if stage_status == "error":
                        stage_icon = "[HATA]"
                    elif stage_status == "warning":
                        stage_icon = "[UYARI]"
                    else:
                        stage_icon = "[OK]"

                    st.markdown(f"**{stage_icon} {stage_name}** ({elapsed}ms)")

                    data = stage.get("data")
                    if data:
                        _show_stage_data(stage_name, data)

            # Sonuc
            final_result = log.get("final_result")
            if final_result:
                st.markdown("#### Sonuc")
                st.json(final_result)


def _show_stage_data(stage_name, data):
    """Asama verisini uygun formatta goster."""
    if not data:
        return

    # Prompt gonderimi
    if stage_name == "prompt_sent":
        prompt_text = data.get("prompt_text", "")
        if prompt_text:
            with st.expander(f"Gonderilen Prompt ({data.get('prompt_length', '?')} karakter)"):
                st.code(prompt_text, language="markdown")

        schema = data.get("schema")
        if schema:
            with st.expander("Kullanilan Sema"):
                st.json(schema)

        extra = data.get("extra")
        if extra:
            with st.expander("Ek Bilgiler"):
                st.json(extra)
        return

    # API yaniti
    if stage_name == "api_response":
        tokens = data.get("tokens", {})
        if tokens:
            st.caption(f"Tokenlar: input={tokens.get('input', '?')}, output={tokens.get('output', '?')}")

        raw = data.get("raw_response_text", "")
        if raw:
            with st.expander(f"Ham API Yaniti ({data.get('raw_response_length', '?')} karakter)"):
                try:
                    parsed = json.loads(raw)
                    st.json(parsed)
                except (json.JSONDecodeError, TypeError):
                    st.code(raw[:5000], language="json")
        return

    # Tool use yaniti
    if stage_name == "tool_use_response":
        st.caption(f"Tool: {data.get('tool_name', '?')}")
        tool_input = data.get("tool_input")
        if tool_input:
            with st.expander("Tool Use Input (AI'nin urettigi yapilandirilmis veri)"):
                st.json(tool_input)
        return

    # Schema dogrulama
    if "schema_validation" in stage_name:
        schema_class = data.get("schema_class", "?")
        error = data.get("validation_error")
        if error:
            st.error(f"Sema dogrulama HATASI ({schema_class}): {error}")
            input_data = data.get("input_data", "")
            if input_data:
                with st.expander("Dogrulanamayan Veri"):
                    if isinstance(input_data, str):
                        st.code(input_data[:3000], language="json")
                    else:
                        st.json(input_data)
        else:
            result = data.get("validation_result")
            if result:
                with st.expander(f"Dogrulanan Veri ({schema_class})"):
                    st.json(result)
        return

    # Parsing asamalari
    if stage_name.startswith("parsing_"):
        error = data.get("error")
        if error:
            st.error(f"Parsing hatasi: {error}")

        input_d = data.get("input")
        if input_d:
            with st.expander("Parsing Girdisi"):
                st.json(input_d) if isinstance(input_d, (dict, list)) else st.code(str(input_d)[:3000])

        output_d = data.get("output")
        if output_d:
            with st.expander("Parsing Ciktisi"):
                st.json(output_d) if isinstance(output_d, (dict, list)) else st.code(str(output_d)[:3000])
        return

    # Kod calistirma
    if stage_name == "code_execution":
        code = data.get("generated_code", "")
        if code:
            with st.expander(f"Uretilen Kod ({data.get('code_length', '?')} karakter)"):
                st.code(code[:5000], language="python")

        error = data.get("error")
        if error:
            st.error(f"Kod calistirma hatasi: {error}")
            tb = data.get("traceback")
            if tb:
                st.code(tb, language="python")
        return

    # Genel veri gosterimi
    with st.expander(f"Detay: {stage_name}"):
        if isinstance(data, (dict, list)):
            st.json(data)
        else:
            st.code(str(data)[:3000])
