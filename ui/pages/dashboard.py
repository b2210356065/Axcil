"""Ana sayfa - Dashboard."""
import streamlit as st
from datetime import datetime


def show_dashboard():
    """Ana sayfa gösterimi."""
    # Header
    st.markdown('<div class="main-header">ExcelAI Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI destekli otomatik Excel oluşturma sistemi</div>',
                unsafe_allow_html=True)

    # Hoş geldin mesajı
    st.markdown(f"""
    <div class="info-box">
        <strong>Hoş geldiniz!</strong><br>
        ExcelAI ile fotoğraf, PDF, ses, metin ve Excel dosyalarınızı profesyonel Excel tablolarına dönüştürün.
        <br><br>
        Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # İş kontrolü
    from core.database import get_functionalities, get_active_business

    active_business = st.session_state.get("active_business")

    if active_business:
        functionalities = get_functionalities(active_business["id"])
        if functionalities:
            st.success(f"**Tanımlı İş Sayısı:** {len(functionalities)}")
            st.divider()
        else:
            st.info("""
            **İlk Kullanım**

            Excel türlerinizi tanımlayarak başlayın. Örneğin:
            - Fatura Girişi
            - Stok Takibi
            - Puantaj Kaydı
            """)
            if st.button("İş Tanımla", type="primary"):
                st.session_state.current_page = "functions"
                st.rerun()
            st.divider()

    # Özellikler bölümü
    st.markdown("### Özellikler")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 3 AI Modeli
        - **Gemini 2.5 Flash** - Hızlı & Ucuz
        - **Claude 4.5 Sonnet** - Kaliteli Kod
        - **GPT-5** - Yedek Model

        Akıllı routing ile en uygun model otomatik seçilir.
        """)

    with col2:
        st.markdown("""
        #### 6 Araç
        - **Görsel → Excel** - Fotoğraflardan veri
        - **Metin → Excel** - Serbest metin
        - **PDF → Excel** - PDF belgeler
        - **Ses → Excel** - Sesli notlar
        - **Excel Dönüştürme** - Format değişimi
        - **Doğrulama** - Hata tespiti
        """)

    with col3:
        st.markdown("""
        #### Profesyonel Çıktı
        - Otomatik stil formatlaması
        - Zebra şerit
        - Güven skoru gösterimi
        - Çoklu sayfa desteği
        - Sektör şablonları

        Hazır Excel dosyaları.
        """)

    st.divider()

    # Hızlı başlangıç
    st.markdown("### Hızlı Başlangıç")

    st.markdown("""
    **3 adımda Excel oluşturun:**

    1. Araç Seçin
    2. Veri Yükleyin
    3. Excel İndirin

    Tüm işlem dakikalar içinde tamamlanır.
    """)

    if st.button("Araçlara Git", type="primary", use_container_width=True):
        st.session_state.current_page = "tools"
        st.rerun()

    st.divider()

    # Sektörel çözümler
    st.markdown("### 🏢 Sektörel Çözümler")

    sectors = [
        {
            "name": "Muhasebe / Finans",
            "icon": "💰",
            "use_cases": ["Fatura girişi", "Fiş kaydı", "Banka ekstresi"],
            "time_saved": "8-12 saat/ay"
        },
        {
            "name": "Stok / Depo",
            "icon": "📦",
            "use_cases": ["Envanter sayımı", "İrsaliye girişi", "Stok hareketi"],
            "time_saved": "45-90 dk/gün"
        },
        {
            "name": "İK / Bordro",
            "icon": "👥",
            "use_cases": ["Puantaj girişi", "İzin takibi", "Bordro hazırlama"],
            "time_saved": "6-10 saat/dönem"
        },
        {
            "name": "İnşaat",
            "icon": "🏗️",
            "use_cases": ["Saha raporu", "Metraj çıkarma", "İşçilik kaydı"],
            "time_saved": "5-8 saat/hafta"
        },
    ]

    cols = st.columns(4)

    for i, sector in enumerate(sectors):
        with cols[i]:
            st.markdown(f"""
            <div class="tool-card">
                <h3>{sector['icon']} {sector['name']}</h3>
                <p><strong>Kullanım alanları:</strong></p>
                <ul>
                    {"".join(f"<li>{uc}</li>" for uc in sector['use_cases'])}
                </ul>
                <p style="color: #28a745; font-weight: bold;">
                    ⏱ {sector['time_saved']} tasarruf
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Son bilgiler
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📚 Dokümantasyon

        - **CLAUDE.md** - Proje detayları
        - **GELISTIRME_PLANI.md** - Yol haritası
        - **test_demo.py** - Test senaryoları

        Tüm dosyalar proje dizininde bulunmaktadır.
        """)

    with col2:
        st.markdown("""
        ### 🆘 Destek

        Sorun mu yaşıyorsunuz?

        1. API anahtarlarını kontrol edin (Ayarlar)
        2. Gerekli paketlerin yüklü olduğundan emin olun
        3. Test senaryolarını çalıştırın

        ```bash
        python test_demo.py
        ```
        """)

    st.divider()
    st.success("✅ Sistem hazır! Araçlar sayfasından başlayabilirsiniz.")
