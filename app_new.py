"""
ExcelAI - AI Destekli Otomatik Excel Oluşturucu
v0.2 - Çoklu Model & Araç Sistemi

Streamlit Web Uygulaması
"""
import streamlit as st
import os
from pathlib import Path

# Core modüller
from core.config import load_config, save_config
from core.models import APIConfig

# AI modüller
from ai.router import ModelRouter

# Sayfa importları (lazy load için fonksiyon olarak)
def load_page_setup():
    from ui.pages.setup import show_setup_page
    return show_setup_page

def load_page_dashboard():
    from ui.pages.dashboard import show_dashboard
    return show_dashboard

def load_page_tools():
    from ui.pages.tools import show_tools_page
    return show_tools_page

def load_page_settings():
    from ui.pages.settings import show_settings_page
    return show_settings_page

def load_page_history():
    from ui.pages.history import show_history_page
    return show_history_page

def load_page_business():
    from ui.pages.business import show_business_page
    return show_business_page


# Sayfa konfigürasyonu
st.set_page_config(
    page_title="ExcelAI - AI Excel Oluşturucu",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS
st.markdown("""
<style>
    /* Ana header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }

    /* Alt başlık */
    .sub-header {
        font-size: 1.2rem;
        color: #4A6FA5;
        margin-bottom: 2rem;
    }

    /* Kartlar */
    .tool-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #E0E0E0;
        background: white;
        transition: all 0.3s;
        cursor: pointer;
    }

    .tool-card:hover {
        border-color: #1E3A5F;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Başarı kutusu */
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        color: #155724;
        margin: 1rem 0;
    }

    /* Bilgi kutusu */
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D1ECF1;
        border: 1px solid #BEE5EB;
        color: #0C5460;
        margin: 1rem 0;
    }

    /* Uyarı kutusu */
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FFF3CD;
        border: 1px solid #FFEAA7;
        color: #856404;
        margin: 1rem 0;
    }

    /* Tab'lar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px 5px 0 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }

    /* Metric kartları */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #1E3A5F;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Session state başlangıç değerleri."""
    # Database başlat
    from core.database import init_db, get_active_business
    init_db()

    if "config" not in st.session_state:
        st.session_state.config = load_config()

    if "router" not in st.session_state:
        if st.session_state.config.available_providers():
            st.session_state.router = ModelRouter(st.session_state.config)
        else:
            st.session_state.router = None

    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"

    if "selected_tool" not in st.session_state:
        st.session_state.selected_tool = None

    if "active_business" not in st.session_state:
        st.session_state.active_business = get_active_business()


def show_sidebar():
    """Sidebar navigasyon."""
    with st.sidebar:
        st.markdown("### 📊 ExcelAI")
        st.markdown("**v0.2** - Çoklu Model Sistemi")
        st.divider()

        # Navigasyon
        st.markdown("#### 📍 Navigasyon")

        pages = {
            "dashboard": "🏠 Ana Sayfa",
            "business": "🏢 İş Yerleri",
            "tools": "🔧 Araçlar",
            "settings": "⚙️ Ayarlar",
            "history": "📜 Geçmiş",
        }

        for page_key, page_name in pages.items():
            if st.button(page_name, use_container_width=True,
                        type="primary" if st.session_state.current_page == page_key else "secondary"):
                st.session_state.current_page = page_key
                st.rerun()

        st.divider()

        # Hızlı bilgiler
        config = st.session_state.config

        st.markdown("#### 🤖 AI Modelleri")
        providers = config.available_providers()

        if providers:
            for provider in providers:
                st.success(f"✓ {provider.value.upper()}")
        else:
            st.warning("⚠ API key ayarlanmadı")
            if st.button("Ayarlara Git", key="quick_setup"):
                st.session_state.current_page = "settings"
                st.rerun()

        st.divider()

        # Aktif iş yeri
        st.markdown("#### 🏢 Aktif İş Yeri")
        active_business = st.session_state.get("active_business")

        if active_business:
            st.success(f"✓ {active_business['business_name'][:20]}")
            st.caption(f"{active_business['sector']}")
        else:
            st.warning("⚠ İş yeri seçilmedi")
            if st.button("İş Yeri Ekle", key="quick_business"):
                st.session_state.current_page = "business"
                st.rerun()

        st.divider()

        # Hızlı istatistikler (örnek)
        st.markdown("#### 📊 İstatistikler")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Araç", "6")
        with col2:
            from core.database import count_businesses
            st.metric("İş Yeri", count_businesses())

        st.divider()
        st.caption("© 2025 ExcelAI")


def main():
    """Ana uygulama akışı."""
    # Session state başlat
    init_session_state()

    # Sidebar göster
    show_sidebar()

    # Kurulum kontrolü
    config = st.session_state.config
    has_any_key = bool(config.gemini_key or config.claude_key or config.openai_key)

    # Eğer hiç API key yoksa, kurulum sayfasına yönlendir
    if not has_any_key and st.session_state.current_page != "settings":
        st.warning("⚠ Lütfen önce API anahtarlarınızı ayarlayın.")
        if st.button("Ayarlara Git →", type="primary"):
            st.session_state.current_page = "settings"
            st.rerun()
        st.stop()

    # Sayfa yönlendirme
    current_page = st.session_state.current_page

    try:
        if current_page == "dashboard":
            show_dashboard = load_page_dashboard()
            show_dashboard()

        elif current_page == "business":
            show_business_page = load_page_business()
            show_business_page()

        elif current_page == "tools":
            show_tools_page = load_page_tools()
            show_tools_page()

        elif current_page == "settings":
            show_settings_page = load_page_settings()
            show_settings_page()

        elif current_page == "history":
            show_history_page = load_page_history()
            show_history_page()

        else:
            st.error(f"Bilinmeyen sayfa: {current_page}")

    except Exception as e:
        st.error(f"Sayfa yükleme hatası: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()
