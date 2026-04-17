"""İş tanımı yönetimi sayfası — zenginleştirme ve iş akışı desteği ile."""
import streamlit as st
import json

from core.database import (
    get_functionalities,
    get_functionality_by_id,
    save_functionality,
    update_functionality,
    delete_functionality,
    get_active_business,
    create_business,
    get_all_data_types,
    create_data_type,
    delete_data_type,
    get_enrichment_attempts,
)
from core.enrichment import (
    enrich_functionality,
    confirm_enrichment,
    reject_enrichment_with_feedback,
)
from core.algorithm_generator import generate_algorithm
from core.algorithm_runner import algorithm_exists, get_algorithm_path


# ---------------------------------------------------------------------------
# Durum yardımcıları
# ---------------------------------------------------------------------------

def _get_data_type_ids(func):
    """İş tanımından veri tipi ID listesini al (geriye uyumlu)."""
    raw = func.get("data_type_ids")
    if raw:
        if isinstance(raw, str):
            try:
                ids = json.loads(raw)
                if isinstance(ids, list):
                    return ids
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(raw, list):
            return raw
    dtype_id = func.get("data_type_id", 3)
    return [dtype_id] if dtype_id else [3]


def _func_status(func) -> tuple:
    """İş tanımının durumunu döndürür: (emoji, label, color)."""
    has_enriched = bool(func.get("enriched_definition"))
    has_algorithm = bool(func.get("algorithm_path")) and algorithm_exists(func["id"])

    if has_algorithm:
        v = func.get("algorithm_version", 1)
        return ("🟢", f"Hazır (v{v})", "green")
    elif has_enriched:
        return ("🟡", "Zenginleştirildi", "orange")
    else:
        return ("⚪", "Tanımsız", "gray")


# ---------------------------------------------------------------------------
# Ana sayfa
# ---------------------------------------------------------------------------

def show_functions_page():
    """İş tanımı yönetimi sayfası."""
    st.markdown("## İş Tanımları")
    st.caption("Excel oluşturma süreçlerinizi tanımlayın, zenginleştirin ve iş akışı oluşturun")

    # İş yeri kontrolü
    active_business = st.session_state.get("active_business")
    if not active_business:
        st.info("İlk kullanım için varsayılan profil oluşturuluyor...")
        business_id = create_business("Varsayılan İş", "Genel Excel işlemleri", "Genel")
        from core.database import set_active_business
        set_active_business(business_id)
        from core.database import get_business_by_id
        st.session_state.active_business = get_business_by_id(business_id)
        st.rerun()

    business_id = active_business["id"]
    functionalities = get_functionalities(business_id)
    data_types = get_all_data_types()

    # İstatistikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam", len(functionalities))
    with col2:
        ready = sum(1 for f in functionalities
                    if f.get("algorithm_path") and algorithm_exists(f["id"]))
        st.metric("Hazır", ready)
    with col3:
        enriched = sum(1 for f in functionalities if f.get("enriched_definition"))
        st.metric("Zenginleştirilmiş", enriched)
    with col4:
        pending = len(functionalities) - ready
        st.metric("Bekleyen", pending)

    st.divider()

    # Yeni iş tanımı ekleme
    if st.button("＋ Yeni İş Tanımı Ekle", use_container_width=True, type="primary"):
        st.session_state.show_add_form = True
        st.session_state.pop("editing_func_id", None)
        st.session_state.pop("enriching_func_id", None)
        st.session_state.pop("algo_func_id", None)

    if st.session_state.get("show_add_form", False):
        _show_add_form(business_id, data_types)

    # Düzenleme formu
    if st.session_state.get("editing_func_id"):
        _show_edit_form(st.session_state.editing_func_id, data_types)

    # Özel veri tipi yönetimi
    with st.expander("Özel Veri Tipi Ekle / Yönet"):
        _show_data_type_manager(data_types)

    st.divider()

    # İş tanımları listesi
    if functionalities:
        st.markdown("### Mevcut İş Tanımları")
        for idx, func in enumerate(functionalities, 1):
            _render_func_card(func, idx, data_types)
    else:
        st.info("Henüz iş tanımı yok. Yukarıdaki butona tıklayarak ekleyin.")


# ---------------------------------------------------------------------------
# İş tanımı kartı
# ---------------------------------------------------------------------------

def _render_func_card(func, idx, data_types):
    """Tek bir iş tanımı kartını çizer."""
    func_id = func["id"]
    emoji, status_label, color = _func_status(func)

    dtype_ids = _get_data_type_ids(func)
    dtype_names = []
    for did in dtype_ids:
        dt = next((d for d in data_types if d["id"] == did), None)
        if dt:
            dtype_names.append(f"{dt['icon']} {dt['name']}")
        else:
            dtype_names.append("Bilinmiyor")

    # Başlık satırı
    header_col, status_col = st.columns([5, 1])
    with header_col:
        st.markdown(f"**{idx}. {func['name']}** {emoji}")
        st.caption(f"{' | '.join(dtype_names)} · {func['description'][:100]}")
    with status_col:
        st.markdown(
            f"<span style='color:{color}; font-size:0.85em;'>{status_label}</span>",
            unsafe_allow_html=True,
        )

    # Aksiyon butonları
    btn_cols = st.columns([1, 1, 1, 1, 1])
    with btn_cols[0]:
        if st.button("Düzenle", key=f"edit_{func_id}", use_container_width=True):
            st.session_state.editing_func_id = func_id
            st.session_state.pop("show_add_form", None)
            st.session_state.pop("enriching_func_id", None)
            st.session_state.pop("algo_func_id", None)
            st.rerun()
    with btn_cols[1]:
        if st.button("Zenginleştir", key=f"enrich_{func_id}", use_container_width=True):
            st.session_state.enriching_func_id = func_id
            st.session_state.pop("editing_func_id", None)
            st.session_state.pop("show_add_form", None)
            st.session_state.pop("algo_func_id", None)
            st.rerun()
    with btn_cols[2]:
        disabled = not bool(func.get("enriched_definition"))
        if st.button("İş Akışı", key=f"algo_{func_id}",
                     use_container_width=True, disabled=disabled):
            st.session_state.algo_func_id = func_id
            st.session_state.pop("editing_func_id", None)
            st.session_state.pop("show_add_form", None)
            st.session_state.pop("enriching_func_id", None)
            st.rerun()
    with btn_cols[3]:
        if func.get("algorithm_path") and algorithm_exists(func_id):
            if st.button("Kodu Gör", key=f"view_{func_id}", use_container_width=True):
                st.session_state[f"show_code_{func_id}"] = not st.session_state.get(
                    f"show_code_{func_id}", False
                )
                st.rerun()
        else:
            st.button("Kodu Gör", key=f"view_{func_id}",
                      use_container_width=True, disabled=True)
    with btn_cols[4]:
        if st.button("Sil", key=f"del_{func_id}", use_container_width=True):
            delete_functionality(func_id)
            st.success("Silindi!")
            st.rerun()

    # Algoritma kodu görüntüleme
    if st.session_state.get(f"show_code_{func_id}", False):
        _show_algorithm_code(func_id)

    # Zenginleştirme paneli
    if st.session_state.get("enriching_func_id") == func_id:
        _show_enrichment_panel(func_id)

    # İş akışı paneli
    if st.session_state.get("algo_func_id") == func_id:
        _show_algorithm_panel(func_id)

    st.divider()


# ---------------------------------------------------------------------------
# Zenginleştirme paneli
# ---------------------------------------------------------------------------

def _show_enrichment_panel(func_id):
    """Zenginleştirme panelini gösterir."""
    func = get_functionality_by_id(func_id)
    if not func:
        return

    st.markdown("---")
    st.markdown("#### Tanımı Zenginleştir")

    # Mevcut zenginleştirilmiş tanım varsa göster
    enriched_raw = func.get("enriched_definition")
    if enriched_raw:
        try:
            enriched = json.loads(enriched_raw) if isinstance(enriched_raw, str) else enriched_raw
            st.success("Bu iş tanımı daha önce zenginleştirilmiş.")
            with st.expander("Mevcut Zenginleştirilmiş Tanımı Gör", expanded=False):
                st.json(enriched)
        except (json.JSONDecodeError, TypeError):
            enriched = None

    # Bekleyen sonuç varsa göster
    pending_key = f"enrichment_result_{func_id}"
    if pending_key in st.session_state:
        result = st.session_state[pending_key]
        if result["success"]:
            st.markdown("##### Yeni Zenginleştirilmiş Tanım")
            st.json(result["enriched"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Onayla", key=f"enr_approve_{func_id}",
                             type="primary", use_container_width=True):
                    confirm_enrichment(func_id, result["enriched"], result.get("attempt_id"))
                    st.session_state.pop(pending_key, None)
                    st.session_state.pop("enriching_func_id", None)
                    st.success("Zenginleştirilmiş tanım onaylandı!")
                    st.rerun()

            with col2:
                if st.button("Reddet", key=f"enr_reject_{func_id}",
                             use_container_width=True):
                    st.session_state[f"enr_show_feedback_{func_id}"] = True
                    st.rerun()

            # Reddetme geri bildirimi
            if st.session_state.get(f"enr_show_feedback_{func_id}"):
                feedback = st.text_area(
                    "Eksikler ve Öneriler",
                    placeholder="Nelerin düzeltilmesini veya eklenmesini istiyorsunuz?",
                    key=f"enr_feedback_{func_id}",
                )
                if st.button("Geri Bildirim Gönder ve Yeniden Üret",
                             key=f"enr_send_fb_{func_id}",
                             use_container_width=True):
                    if result.get("attempt_id"):
                        reject_enrichment_with_feedback(
                            result["attempt_id"],
                            feedback or "Kullanıcı reddetti",
                        )
                    st.session_state.pop(pending_key, None)
                    st.session_state.pop(f"enr_show_feedback_{func_id}", None)
                    # Yeniden üret
                    _run_enrichment(func_id)
                    st.rerun()
        else:
            st.error(f"Zenginleştirme başarısız: {result.get('error', 'Bilinmeyen hata')}")
            st.session_state.pop(pending_key, None)

    # Zenginleştirme başlat butonu
    col_run, col_cancel = st.columns(2)
    with col_run:
        label = "Yeniden Zenginleştir" if enriched_raw else "Zenginleştir"
        if st.button(label, key=f"run_enrich_{func_id}",
                     type="primary", use_container_width=True):
            _run_enrichment(func_id)
            st.rerun()
    with col_cancel:
        if st.button("Kapat", key=f"close_enrich_{func_id}",
                     use_container_width=True):
            st.session_state.pop("enriching_func_id", None)
            st.session_state.pop(f"enrichment_result_{func_id}", None)
            st.session_state.pop(f"enr_show_feedback_{func_id}", None)
            st.rerun()

    st.markdown("---")


def _run_enrichment(func_id):
    """Zenginleştirme AI çağrısını çalıştırır."""
    router = st.session_state.get("router")
    if not router:
        st.error("AI modelleri yapılandırılmamış. Ayarlar sayfasından API anahtarlarını girin.")
        return

    with st.spinner("AI tanımı zenginleştiriyor..."):
        result = enrich_functionality(func_id, router)
    st.session_state[f"enrichment_result_{func_id}"] = result


# ---------------------------------------------------------------------------
# İş akışı (algoritma) paneli
# ---------------------------------------------------------------------------

def _show_algorithm_panel(func_id):
    """İş akışı oluşturma panelini gösterir."""
    func = get_functionality_by_id(func_id)
    if not func:
        return

    st.markdown("---")
    st.markdown("#### İş Akışı Geliştir")

    # Zenginleştirilmiş tanım yoksa uyarı
    if not func.get("enriched_definition"):
        st.warning("İş akışı oluşturmak için önce tanımı zenginleştirmeniz gerekiyor.")
        if st.button("Kapat", key=f"close_algo_warn_{func_id}"):
            st.session_state.pop("algo_func_id", None)
            st.rerun()
        st.markdown("---")
        return

    # Mevcut algoritma bilgisi
    if func.get("algorithm_path") and algorithm_exists(func_id):
        v = func.get("algorithm_version", 1)
        st.success(f"İş akışı mevcut (versiyon {v})")

    # Bekleyen sonuç
    pending_key = f"algorithm_result_{func_id}"
    if pending_key in st.session_state:
        result = st.session_state[pending_key]
        if result["success"]:
            st.success(f"İş akışı başarıyla oluşturuldu! (v{result.get('version', 1)})")
            with st.expander("Üretilen Kodu Gör"):
                st.code(result["code"], language="python")
            st.session_state.pop(pending_key, None)
        else:
            st.error(f"İş akışı oluşturulamadı: {result.get('error', 'Bilinmeyen hata')}")
            if result.get("code"):
                with st.expander("Başarısız Kod"):
                    st.code(result["code"], language="python")

            # Kullanıcı geri bildirimi
            st.markdown("##### Geri Bildirim ile Yeniden Dene")
            feedback = st.text_area(
                "Eksikler ve Öneriler",
                placeholder="Kodda nelerin düzeltilmesini istiyorsunuz? (Boş bırakabilirsiniz)",
                key=f"algo_feedback_{func_id}",
            )
            if st.button("Geri Bildirimle Yeniden Üret",
                         key=f"algo_retry_{func_id}",
                         type="primary", use_container_width=True):
                st.session_state.pop(pending_key, None)
                _run_algorithm(func_id, user_feedback=feedback or None)
                st.rerun()

            if st.button("Kapat", key=f"algo_close_err_{func_id}",
                         use_container_width=True):
                st.session_state.pop(pending_key, None)
                st.session_state.pop("algo_func_id", None)
                st.rerun()
            st.markdown("---")
            return

    # Aksiyon butonları
    col_run, col_cancel = st.columns(2)
    with col_run:
        label = "Yeniden Oluştur" if (func.get("algorithm_path")
                                       and algorithm_exists(func_id)) else "İş Akışı Oluştur"
        if st.button(label, key=f"run_algo_{func_id}",
                     type="primary", use_container_width=True):
            _run_algorithm(func_id)
            st.rerun()
    with col_cancel:
        if st.button("Kapat", key=f"close_algo_{func_id}",
                     use_container_width=True):
            st.session_state.pop("algo_func_id", None)
            st.session_state.pop(f"algorithm_result_{func_id}", None)
            st.rerun()

    st.markdown("---")


def _run_algorithm(func_id, user_feedback=None):
    """Algoritma üretme AI çağrısını çalıştırır."""
    router = st.session_state.get("router")
    if not router:
        st.error("AI modelleri yapılandırılmamış. Ayarlar sayfasından API anahtarlarını girin.")
        return

    with st.spinner("AI iş akışı oluşturuyor (bu biraz zaman alabilir)..."):
        result = generate_algorithm(func_id, router, user_feedback=user_feedback)
    st.session_state[f"algorithm_result_{func_id}"] = result


# ---------------------------------------------------------------------------
# Algoritma kodu görüntüleme
# ---------------------------------------------------------------------------

def _show_algorithm_code(func_id):
    """Kaydedilmiş algoritma kodunu gösterir."""
    path = get_algorithm_path(func_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        st.code(code, language="python")
    except FileNotFoundError:
        st.warning("Algoritma dosyası bulunamadı.")


# ---------------------------------------------------------------------------
# Ekleme formu
# ---------------------------------------------------------------------------

def _show_add_form(business_id, data_types):
    """Yeni iş tanımı ekleme formu."""
    st.markdown("---")
    st.markdown("### Yeni İş Tanımı")

    name = st.text_input("İş Adı *", placeholder="Örn: Fatura İşleme", key="add_name")
    description = st.text_area("Açıklama *", height=100, key="add_desc")

    dtype_dict = {dt["id"]: f"{dt['icon']} {dt['name']}" for dt in data_types}
    selected_dtypes = st.multiselect(
        "Veri Tipleri * (birden fazla seçilebilir)",
        options=list(dtype_dict.keys()),
        format_func=lambda x: dtype_dict[x],
        default=[3],
        key="add_dtypes",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("İptal", use_container_width=True, key="add_cancel"):
            st.session_state.show_add_form = False
            st.rerun()
    with col2:
        if st.button("Kaydet", type="primary", use_container_width=True, key="add_save"):
            if not name or not description:
                st.error("Tüm alanları doldurun!")
            elif not selected_dtypes:
                st.error("En az bir veri tipi seçin!")
            else:
                result = save_functionality(
                    business_id,
                    name.strip(),
                    description.strip(),
                    [{"name": "data", "type": "any"}],
                    {"type": "general"},
                    f"İş: {name}\n{description}",
                    data_type_ids=selected_dtypes,
                )
                if result:
                    st.success(f"'{name}' eklendi!")
                    st.session_state.show_add_form = False
                    st.rerun()
                else:
                    st.error("Bu isimde iş tanımı zaten var!")

    st.markdown("---")


# ---------------------------------------------------------------------------
# Düzenleme formu
# ---------------------------------------------------------------------------

def _show_edit_form(func_id, data_types):
    """İş tanımı düzenleme formu."""
    func = get_functionality_by_id(func_id)
    if not func:
        st.error("İş tanımı bulunamadı!")
        st.session_state.pop("editing_func_id", None)
        return

    st.markdown("---")
    st.markdown(f"### Düzenle: {func['name']}")

    name = st.text_input("İş Adı *", value=func["name"], key="edit_name")
    description = st.text_area("Açıklama *", value=func["description"],
                               height=100, key="edit_desc")

    current_dtype_ids = _get_data_type_ids(func)
    dtype_dict = {dt["id"]: f"{dt['icon']} {dt['name']}" for dt in data_types}
    selected_dtypes = st.multiselect(
        "Veri Tipleri * (birden fazla seçilebilir)",
        options=list(dtype_dict.keys()),
        format_func=lambda x: dtype_dict[x],
        default=[did for did in current_dtype_ids if did in dtype_dict],
        key="edit_dtypes",
    )

    with st.expander("Sistem Promptu (İleri Seviye)"):
        system_prompt = st.text_area(
            "AI için özel talimatlar",
            value=func.get("system_prompt", ""),
            height=150,
            key="edit_system_prompt",
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("İptal", use_container_width=True, key="edit_cancel"):
            st.session_state.pop("editing_func_id", None)
            st.rerun()
    with col2:
        if st.button("Güncelle", type="primary", use_container_width=True, key="edit_save"):
            if not name or not description:
                st.error("Tüm alanları doldurun!")
            elif not selected_dtypes:
                st.error("En az bir veri tipi seçin!")
            else:
                raw_fields = func.get("input_fields", "[]")
                if isinstance(raw_fields, str):
                    try:
                        input_fields = json.loads(raw_fields)
                    except (json.JSONDecodeError, TypeError):
                        input_fields = [{"name": "data", "type": "any"}]
                else:
                    input_fields = raw_fields

                raw_template = func.get("excel_template", "{}")
                if isinstance(raw_template, str):
                    try:
                        excel_template = json.loads(raw_template)
                    except (json.JSONDecodeError, TypeError):
                        excel_template = {"type": "general"}
                else:
                    excel_template = raw_template

                result = update_functionality(
                    func_id,
                    name.strip(),
                    description.strip(),
                    input_fields,
                    excel_template,
                    system_prompt,
                    data_type_ids=selected_dtypes,
                )
                if result:
                    st.success(f"'{name}' güncellendi!")
                    st.session_state.pop("editing_func_id", None)
                    st.rerun()
                else:
                    st.error("Bu isimde başka bir iş tanımı zaten var!")

    st.markdown("---")


# ---------------------------------------------------------------------------
# Özel veri tipi yönetimi
# ---------------------------------------------------------------------------

def _show_data_type_manager(data_types):
    """Özel veri tipi ekleme ve yönetme."""
    st.markdown("#### Yeni Veri Tipi Oluştur")

    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        new_name = st.text_input("Ad", placeholder="Örn: Barkod", key="new_dtype_name")
    with col2:
        new_desc = st.text_input("Açıklama", placeholder="Barkod veya QR kod verisi",
                                 key="new_dtype_desc")
    with col3:
        new_icon = st.text_input("İkon", value="📊", max_chars=2, key="new_dtype_icon")

    if st.button("Veri Tipi Ekle", key="add_dtype_btn"):
        if not new_name:
            st.error("Veri tipi adı boş olamaz!")
        else:
            result = create_data_type(new_name.strip(), new_desc.strip(),
                                      new_icon.strip() or "📊")
            if result:
                st.success(f"'{new_name}' veri tipi eklendi!")
                st.rerun()
            else:
                st.error("Bu isimde veri tipi zaten var!")

    user_types = [dt for dt in data_types if not dt.get("is_default", 0)]
    if user_types:
        st.markdown("#### Özel Veri Tipleri")
        for dt in user_types:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{dt['icon']} **{dt['name']}** — {dt.get('description', '')}")
            with col2:
                if st.button("Sil", key=f"del_dtype_{dt['id']}"):
                    delete_data_type(dt["id"])
                    st.success(f"'{dt['name']}' silindi!")
                    st.rerun()

    st.markdown("#### Varsayılan Veri Tipleri")
    default_types = [dt for dt in data_types if dt.get("is_default", 0)]
    for dt in default_types:
        st.caption(f"{dt['icon']} {dt['name']} — {dt.get('description', '')}")
