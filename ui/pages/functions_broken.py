"""İşlevsellik yönetimi sayfası - Farklı Excel türlerini tanımlama."""
import streamlit as st
from core.database import (
    get_functionalities,
    save_functionality,
    delete_functionality,
    update_functionality,
    get_business_by_id,
    get_active_business,
    create_business,
    get_all_data_types,
    get_data_type_by_id,
    create_data_type,
)
import json
import sys
import traceback

# Debug logging
def debug_log(message):
    """Debug mesajlarını hem konsola hem Streamlit'e yazdır."""
    print(f"[DEBUG] {message}", file=sys.stderr)
    sys.stderr.flush()


def show_functions_page():
    """İşlevsellik yönetimi sayfası."""
    try:
        debug_log("=== Functions page started ===")

        st.markdown('<div class="main-header">📋 İş Tanımları</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Excel oluşturma süreçlerinizi tanımlayın ve yönetin</div>',
                    unsafe_allow_html=True)

        debug_log("Headers rendered")

        # İş yeri kontrolü - yoksa varsayılan oluştur
        active_business = st.session_state.get("active_business")
        debug_log(f"Active business: {active_business}")

        if not active_business:
            debug_log("No active business, creating default...")
            st.info("İlk kullanım için varsayılan iş profili oluşturuluyor...")
            business_id = create_business(
                "Varsayılan İş",
                "Genel amaçlı Excel işlemleri",
                "Genel"
            )
            from core.database import set_active_business
            set_active_business(business_id)
            st.session_state.active_business = get_business_by_id(business_id)
            debug_log(f"Default business created: {business_id}")
            st.rerun()

        business_id = active_business["id"]
        debug_log(f"Business ID: {business_id}")

        # Mevcut işlevsellikler
        debug_log("Fetching functionalities...")
        functionalities = get_functionalities(business_id)
        debug_log(f"Functionalities count: {len(functionalities)}")

        # İstatistikler
        debug_log("Rendering statistics...")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📊 Toplam İş Tanımı", len(functionalities))

        with col2:
            st.metric("🏢 İş Profili", active_business["business_name"])

        with col3:
            debug_log("Fetching data types...")
            data_types = get_all_data_types()
            debug_log(f"Data types count: {len(data_types)}")
            st.metric("📦 Veri Tipi", len(data_types))

        st.divider()

        # Yeni iş tanımı ekleme butonu
        if "show_add_form" not in st.session_state:
            st.session_state.show_add_form = False

        debug_log(f"Show add form: {st.session_state.show_add_form}")

        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.markdown("### 📋 Mevcut İş Tanımları")

        with col_b:
            if st.button(
                "➕ Yeni İş Tanımı" if not st.session_state.show_add_form else "❌ İptal",
                use_container_width=True,
                type="primary" if not st.session_state.show_add_form else "secondary"
            ):
                st.session_state.show_add_form = not st.session_state.show_add_form
                debug_log(f"Button clicked, toggled to: {st.session_state.show_add_form}")
                st.rerun()

        # Yeni iş tanımı ekleme formu (inline)
        if st.session_state.show_add_form:
            debug_log("Showing add form...")
            st.markdown("---")
            show_add_function_form_inline(business_id)
            st.markdown("---")

        # İş tanımları listesi
        debug_log("Rendering functions list...")
        if not functionalities:
            st.info("""
            🎯 **Henüz iş tanımı oluşturmadınız!**

            İş tanımı, Excel oluşturma sürecinizi tanımlar. Örneğin:
            - Fatura Girişi
            - Stok Takibi
            - Otel Oda Yerleştirme
            - Masraf Takibi

            **Başlamak için yukarıdaki "➕ Yeni İş Tanımı" butonuna tıklayın.**
            """)
        else:
            show_functions_list(functionalities, business_id)

        debug_log("=== Functions page completed successfully ===")

    except Exception as e:
        debug_log(f"ERROR in show_functions_page: {str(e)}")
        debug_log(f"Traceback: {traceback.format_exc()}")
        st.error(f"""
        ❌ **Hata Oluştu!**

        {str(e)}

        **Detaylar:**
        ```
        {traceback.format_exc()}
        ```
        """)
        st.stop()


def show_add_function_form_inline(business_id):
    """Yeni işlevsellik ekleme formu (inline)."""
    try:
        debug_log(f"show_add_function_form_inline called with business_id={business_id}")
        st.markdown("#### ➕ Yeni İş Tanımı Oluştur")

        # Veri tipleri
        debug_log("Fetching data types for form...")
        data_types = get_all_data_types()
        debug_log(f"Data types fetched: {len(data_types)}")

        with st.form("add_function_form_inline", clear_on_submit=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                name = st.text_input(
                    "📌 İş Tanımı Adı *",
                    placeholder="Örn: Otel Oda Yerleştirme, Fatura Girişi, Stok Sayımı",
                    help="Bu işin kısa ve açıklayıcı adı"
                )

            with col2:
            # Veri tipi seçimi
            dtype_options = {dt["id"]: f"{dt['icon']} {dt['name']}" for dt in data_types}
            dtype_options[0] = "➕ Yeni Veri Tipi Ekle..."

            selected_dtype_id = st.selectbox(
                "📊 Veri Tipi *",
                options=list(dtype_options.keys()),
                format_func=lambda x: dtype_options[x],
                help="Bu iş hangi veri tipiyle çalışacak?"
            )

        # Yeni veri tipi ekleme (inline)
        if selected_dtype_id == 0:
            st.markdown("##### ➕ Yeni Veri Tipi Ekle")

            col_a, col_b, col_c = st.columns([2, 2, 1])

            with col_a:
                new_dtype_name = st.text_input(
                    "Veri Tipi Adı",
                    placeholder="Örn: Video, QR Kod, Çizim"
                )

            with col_b:
                new_dtype_desc = st.text_input(
                    "Açıklama",
                    placeholder="Kısa açıklama"
                )

            with col_c:
                new_dtype_icon = st.text_input(
                    "İkon",
                    value="📦",
                    max_chars=2
                )

            # Yeni veri tipi oluşturma
            if new_dtype_name and st.form_submit_button("💾 Veri Tipini Kaydet"):
                new_dtype_id = create_data_type(
                    new_dtype_name,
                    new_dtype_desc,
                    new_dtype_icon
                )

                if new_dtype_id:
                    st.success(f"✅ '{new_dtype_name}' veri tipi oluşturuldu!")
                    st.rerun()
                else:
                    st.error("❌ Bu veri tipi zaten mevcut!")

            st.stop()  # Form gönderimini bekle

        description = st.text_area(
            "📝 Açıklama *",
            height=120,
            placeholder="Bu iş ne yapar? Hangi süreçte kullanılır? Hangi kurallar geçerlidir?\n\nÖrnek:\n- Otel rezervasyonlarında müşterileri odalara yerleştir\n- Cinsiyet kurallarına uygun şekilde yerleştir\n- Grup tercihlerini dikkate al",
            help="İşin detaylı açıklaması - AI bu bilgiyi kullanarak Excel oluşturacak"
        )

        # Basitleştirilmiş şablon seçimi
        template_type = st.selectbox(
            "📋 Excel Şablon Tipi",
            [
                "Özel / Karmaşık Yapı",
                "Fatura / Fiş",
                "Stok Hareketi",
                "Puantaj / Çalışma Saatleri",
                "Masraf Kaydı",
                "Genel Tablo"
            ],
            help="En yakın şablon tipini seçin - AI otomatik format uygulayacak"
        )

        # Gelişmiş seçenekler (opsiyonel)
        with st.expander("⚙️ Gelişmiş Ayarlar (Opsiyonel)"):
            st.markdown("**Sistem Prompt Özelleştirme**")

            custom_prompt = st.text_area(
                "Özel Prompt (AI'a ek talimatlar)",
                height=150,
                placeholder="AI'ın davranışını özelleştirin...\n\nÖrnek:\n- Yabancı kadın-erkek aynı odada kalamaz\n- Grup tercihleri korunmalı\n- Oda kapasiteleri optimize edilmeli",
                help="Bu alan doldurulursa, varsayılan prompt'a eklenecek"
            )

        st.markdown("---")

        col_submit_1, col_submit_2 = st.columns([1, 3])

        with col_submit_1:
            cancel = st.form_submit_button(
                "❌ İptal",
                use_container_width=True
            )

        with col_submit_2:
            submitted = st.form_submit_button(
                "✅ İş Tanımını Kaydet",
                type="primary",
                use_container_width=True
            )

        if cancel:
            st.session_state.show_add_form = False
            st.rerun()

        if submitted:
            if not name or not description:
                st.error("❌ İş adı ve açıklama zorunludur!")
            elif selected_dtype_id == 0:
                st.error("❌ Lütfen veri tipi seçin veya yeni veri tipi oluşturun!")
            else:
                # Basitleştirilmiş input fields ve template
                input_fields = [
                    {"name": "data", "type": "any", "required": True}
                ]

                excel_template = {
                    "type": template_type,
                    "auto_format": True
                }

                # Sistem prompt oluştur
                base_prompt = f"""
Bu bir {template_type} işlevi.

İŞ TANIMI:
{description}

VERİ TİPİ:
{dtype_options[selected_dtype_id]}

GÖREV:
Verilen veriyi analiz et ve {template_type} formatında profesyonel bir Excel dosyası oluştur.
"""

                if custom_prompt:
                    system_prompt = base_prompt + f"\n\nEK TALİMATLAR:\n{custom_prompt}"
                else:
                    system_prompt = base_prompt

                # Kaydet
                result = save_functionality(
                    business_id,
                    name,
                    description,
                    input_fields,
                    excel_template,
                    system_prompt,
                    data_type_id=selected_dtype_id
                )

                if result is None:
                    st.error(f"❌ '{name}' isimli bir iş tanımı zaten mevcut! Farklı bir isim deneyin.")
                else:
                    st.success(f"✅ '{name}' başarıyla oluşturuldu!")
                    st.balloons()
                    st.session_state.show_add_form = False
                    st.rerun()

    except Exception as e:
        debug_log(f"ERROR in show_add_function_form_inline: {str(e)}")
        debug_log(f"Traceback: {traceback.format_exc()}")
        st.error(f"""
        ❌ **Form Hatası!**

        {str(e)}

        **Detaylar:**
        ```
        {traceback.format_exc()}
        ```
        """)


def show_functions_list(functionalities, business_id):
    """İşlevsellik listesi."""
    # Veri tipleri
    data_types = get_all_data_types()
    dtype_map = {dt["id"]: dt for dt in data_types}

    for idx, func in enumerate(functionalities, 1):
        # Veri tipi bilgisi
        dtype_id = func.get("data_type_id", 3)  # Varsayılan: Metin
        dtype = dtype_map.get(dtype_id, {"name": "Bilinmiyor", "icon": "❓"})

        with st.container():
            # Ana bilgiler
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

            with col1:
                st.markdown(f"**{idx}. {func['name']}**")
                st.caption(f"{dtype['icon']} {dtype['name']} · {func['description'][:80]}...")

            with col2:
                st.text(f"📅 {func['created_at'][:10]}")

            with col3:
                # Düzenle
                if st.button("✏️ Düzenle", key=f"edit_{func['id']}", use_container_width=True):
                    st.session_state.editing_function = func['id']
                    st.rerun()

            with col4:
                # Sil
                if st.button("🗑️ Sil", key=f"delete_{func['id']}",
                            type="secondary", use_container_width=True):
                    st.session_state.deleting_function = func['id']

            # Silme onayı
            if hasattr(st.session_state, 'deleting_function') and \
               st.session_state.deleting_function == func['id']:
                with st.expander("⚠️ Silme Onayı", expanded=True):
                    st.warning(f"""
                    **DİKKAT:** '{func['name']}' silinecek!

                    Bu işlem geri alınamaz.
                    """)

                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("❌ İptal", key=f"cancel_delete_{func['id']}", use_container_width=True):
                            del st.session_state.deleting_function
                            st.rerun()

                    with col_b:
                        if st.button("✅ Evet, Sil", key=f"confirm_delete_{func['id']}",
                                    type="primary", use_container_width=True):
                            delete_functionality(func['id'])
                            del st.session_state.deleting_function
                            st.success("✅ İş tanımı silindi")
                            st.rerun()

            # Düzenleme formu
            if hasattr(st.session_state, 'editing_function') and \
               st.session_state.editing_function == func['id']:
                with st.expander("✏️ Düzenleme", expanded=True):
                    show_edit_function_form(func, dtype_map)

            st.divider()


def show_edit_function_form(func, dtype_map):
    """İşlevsellik düzenleme formu."""
    # Veri tipleri
    data_types = get_all_data_types()

    with st.form(f"edit_function_form_{func['id']}"):
        col1, col2 = st.columns([2, 1])

        with col1:
            name = st.text_input(
                "İş Adı",
                value=func['name']
            )

        with col2:
            # Veri tipi seçimi
            dtype_options = {dt["id"]: f"{dt['icon']} {dt['name']}" for dt in data_types}

            current_dtype_id = func.get("data_type_id", 3)

            selected_dtype_id = st.selectbox(
                "Veri Tipi",
                options=list(dtype_options.keys()),
                index=list(dtype_options.keys()).index(current_dtype_id) if current_dtype_id in dtype_options else 0,
                format_func=lambda x: dtype_options[x]
            )

        description = st.text_area(
            "Açıklama",
            value=func['description'],
            height=100
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            cancel = st.form_submit_button("İptal", use_container_width=True)

        with col_btn2:
            save = st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True)

        if cancel:
            del st.session_state.editing_function
            st.rerun()

        if save:
            if not name or not description:
                st.error("Tüm alanlar zorunludur")
            else:
                # Mevcut verileri koru
                input_fields = json.loads(func['input_fields'])
                excel_template = json.loads(func['excel_template'])
                system_prompt = func['system_prompt']

                update_functionality(
                    func['id'],
                    name,
                    description,
                    input_fields,
                    excel_template,
                    system_prompt,
                    data_type_id=selected_dtype_id
                )
                del st.session_state.editing_function
                st.success("✅ İş tanımı güncellendi!")
                st.rerun()
