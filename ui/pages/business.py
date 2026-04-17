"""İş Yeri yönetimi sayfası - Çoklu iş yeri tanımlama ve seçim."""
import streamlit as st
from core.database import (
    get_all_businesses,
    get_business_by_id,
    get_active_business,
    create_business,
    update_business,
    delete_business,
    set_active_business,
    count_businesses
)


def show_business_page():
    """İş yeri yönetimi sayfası."""
    st.markdown('<div class="main-header">🏢 İş Yerleri</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">İş yerlerinizi tanımlayın ve yönetin</div>',
                unsafe_allow_html=True)

    # Mevcut iş yerleri
    businesses = get_all_businesses()
    active_business = get_active_business()

    # İstatistikler
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Toplam İş Yeri", len(businesses))

    with col2:
        active_name = active_business["business_name"] if active_business else "Seçilmemiş"
        st.metric("Aktif İş Yeri", active_name[:20] + "..." if len(active_name) > 20 else active_name)

    with col3:
        if active_business:
            st.metric("Sektör", active_business["sector"])

    st.divider()

    # Tab'lar
    tab1, tab2 = st.tabs(["📋 İş Yerlerim", "➕ Yeni İş Yeri"])

    with tab1:
        show_business_list(businesses, active_business)

    with tab2:
        show_add_business_form()


def show_business_list(businesses, active_business):
    """İş yeri listesi."""
    if not businesses:
        st.info("""
        👋 Henüz iş yeri tanımlı değil!

        **Başlamak için:**
        1. Sağdaki "Yeni İş Yeri" sekmesine gidin
        2. İş yeri bilgilerinizi girin
        3. Kaydedin
        """)
        return

    st.markdown("### İş Yerleriniz")

    for idx, business in enumerate(businesses, 1):
        is_active = active_business and active_business["id"] == business["id"]

        # Kart
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                # İsim ve badge
                badge = "🟢 AKTİF" if is_active else "⚪ Pasif"
                st.markdown(f"#### {idx}. {business['business_name']} {badge}")
                st.caption(f"Sektör: {business['sector']}")
                st.text(business['business_description'][:100] + "...")

            with col2:
                st.text(f"Oluşturma: {business['created_at'][:10]}")
                if business['updated_at'] != business['created_at']:
                    st.text(f"Güncelleme: {business['updated_at'][:10]}")

            with col3:
                # Aksiyon butonları
                if not is_active:
                    if st.button(f"✅ Aktif Yap", key=f"activate_{business['id']}",
                                type="primary", use_container_width=True):
                        set_active_business(business['id'])
                        st.session_state.active_business = get_business_by_id(business['id'])
                        st.success(f"✅ '{business['business_name']}' aktif edildi!")
                        st.rerun()

                # Düzenle
                if st.button(f"✏️ Düzenle", key=f"edit_{business['id']}",
                            use_container_width=True):
                    st.session_state.editing_business = business['id']
                    st.rerun()

                # Sil (aktif değilse)
                if not is_active:
                    if st.button(f"🗑️ Sil", key=f"delete_{business['id']}",
                                type="secondary", use_container_width=True):
                        st.session_state.deleting_business = business['id']

            # Silme onayı
            if hasattr(st.session_state, 'deleting_business') and \
               st.session_state.deleting_business == business['id']:
                with st.expander("⚠️ Silme Onayı", expanded=True):
                    st.warning(f"""
                    **DİKKAT:** '{business['business_name']}' silinecek!

                    Bu işlem:
                    - İş yerini siler
                    - İlişkili tüm işlevsellikler silinir
                    - İlişkili geçmiş kayıtları silinir
                    - **GERİ ALINAMAZ!**
                    """)

                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("❌ İptal", key=f"cancel_delete_{business['id']}"):
                            del st.session_state.deleting_business
                            st.rerun()

                    with col_b:
                        if st.button("✅ Evet, Sil", key=f"confirm_delete_{business['id']}",
                                    type="primary"):
                            delete_business(business['id'])
                            del st.session_state.deleting_business
                            st.success("✅ İş yeri silindi")
                            st.rerun()

            # Düzenleme formu
            if hasattr(st.session_state, 'editing_business') and \
               st.session_state.editing_business == business['id']:
                with st.expander("✏️ Düzenle", expanded=True):
                    show_edit_business_form(business)

            st.divider()


def show_add_business_form():
    """Yeni iş yeri ekleme formu."""
    st.markdown("### ➕ Yeni İş Yeri Ekle")

    with st.form("add_business_form"):
        business_name = st.text_input(
            "İş Yeri Adı *",
            placeholder="Örn: ABC Muhasebe Ofisi",
            help="İş yerinizin adı"
        )

        sector = st.selectbox(
            "Sektör *",
            [
                "Muhasebe / Finans",
                "Stok / Depo",
                "İK / Bordro",
                "İnşaat",
                "Perakende / Ticaret",
                "Üretim / İmalat",
                "Lojistik",
                "Teknoloji",
                "Sağlık",
                "Eğitim",
                "Hukuk",
                "Diğer"
            ]
        )

        business_description = st.text_area(
            "İş Yeri Açıklaması *",
            height=120,
            placeholder="İş yerinizin ne yaptığını, hangi tür Excel dosyaları oluşturmanız gerektiğini açıklayın...",
            help="Bu bilgi AI'ya iş bağlamı sağlar ve daha iyi sonuçlar almasını sağlar"
        )

        st.divider()

        auto_activate = st.checkbox(
            "Oluşturduktan sonra otomatik aktif yap",
            value=True,
            help="Yeni iş yeri otomatik olarak aktif iş yeri olarak ayarlanır"
        )

        submitted = st.form_submit_button(
            "💾 İş Yeri Oluştur",
            type="primary",
            use_container_width=True
        )

        if submitted:
            if not business_name or not business_description:
                st.error("❌ İş yeri adı ve açıklaması zorunludur")
            else:
                # Oluştur
                business_id = create_business(business_name, business_description, sector)

                # Aktif yap (istenirse)
                if auto_activate:
                    set_active_business(business_id)
                    st.session_state.active_business = get_business_by_id(business_id)

                st.success(f"✅ '{business_name}' başarıyla oluşturuldu!")
                st.balloons()
                st.rerun()


def show_edit_business_form(business):
    """İş yeri düzenleme formu."""
    with st.form(f"edit_business_form_{business['id']}"):
        business_name = st.text_input(
            "İş Yeri Adı *",
            value=business['business_name']
        )

        sector = st.selectbox(
            "Sektör *",
            [
                "Muhasebe / Finans",
                "Stok / Depo",
                "İK / Bordro",
                "İnşaat",
                "Perakende / Ticaret",
                "Üretim / İmalat",
                "Lojistik",
                "Teknoloji",
                "Sağlık",
                "Eğitim",
                "Hukuk",
                "Diğer"
            ],
            index=[
                "Muhasebe / Finans",
                "Stok / Depo",
                "İK / Bordro",
                "İnşaat",
                "Perakende / Ticaret",
                "Üretim / İmalat",
                "Lojistik",
                "Teknoloji",
                "Sağlık",
                "Eğitim",
                "Hukuk",
                "Diğer"
            ].index(business['sector']) if business['sector'] in [
                "Muhasebe / Finans",
                "Stok / Depo",
                "İK / Bordro",
                "İnşaat",
                "Perakende / Ticaret",
                "Üretim / İmalat",
                "Lojistik",
                "Teknoloji",
                "Sağlık",
                "Eğitim",
                "Hukuk",
                "Diğer"
            ] else 11
        )

        business_description = st.text_area(
            "İş Yeri Açıklaması *",
            value=business['business_description'],
            height=120
        )

        col1, col2 = st.columns(2)

        with col1:
            cancel = st.form_submit_button("❌ İptal", use_container_width=True)

        with col2:
            save = st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True)

        if cancel:
            del st.session_state.editing_business
            st.rerun()

        if save:
            if not business_name or not business_description:
                st.error("❌ Tüm alanlar zorunludur")
            else:
                update_business(
                    business['id'],
                    business_name,
                    business_description,
                    sector
                )
                del st.session_state.editing_business
                st.success("✅ İş yeri güncellendi!")
                st.rerun()
