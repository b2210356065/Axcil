"""Ayarlar sayfası - API anahtarları ve model konfigürasyonu."""
import streamlit as st
from core.config import save_config
from core.models import APIConfig, ModelProvider
from ai.router import ModelRouter


def show_settings_page():
    """Ayarlar sayfası."""
    st.markdown('<div class="main-header">⚙️ Ayarlar</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI model ayarları ve API anahtarları</div>',
                unsafe_allow_html=True)

    # Mevcut config
    config = st.session_state.config

    st.markdown("### 🔑 API Anahtarları")

    st.info("""
    **3 AI modeli desteklenmektedir:**
    - **Gemini 2.5 Flash** - Hızlı çıkarma (Google AI Studio)
    - **Claude 4.5 Sonnet** - Kaliteli kod (Anthropic)
    - **GPT-4/5** - Yedek model (OpenAI)

    En az bir API anahtarı gereklidir. Tümünü eklerseniz sistem otomatik olarak en uygun modeli seçer.
    """)

    # API Key formları
    with st.form("api_settings"):
        st.markdown("#### Google Gemini")

        col1, col2 = st.columns([3, 1])

        with col1:
            gemini_key = st.text_input(
                "Gemini API Key",
                value=config.gemini_key if config.gemini_key else "",
                type="password",
                placeholder="AIza...",
                help="Google AI Studio'dan alın: https://makersuite.google.com/app/apikey"
            )

        with col2:
            gemini_options = [
                "models/gemini-3.1-flash-live-preview",
                "models/gemini-2.0-flash",
                "models/gemini-1.5-flash",
                "models/gemini-2.5-flash-preview-05-20"
            ]
            gemini_index = gemini_options.index(config.gemini_model) if config.gemini_model in gemini_options else 0
            gemini_model = st.selectbox(
                "Model",
                gemini_options,
                index=gemini_index
            )

        st.divider()
        st.markdown("#### Anthropic Claude")

        col1, col2 = st.columns([3, 1])

        with col1:
            claude_key = st.text_input(
                "Claude API Key",
                value=config.claude_key if config.claude_key else "",
                type="password",
                placeholder="sk-ant-...",
                help="Anthropic Console'dan alın: https://console.anthropic.com/"
            )

        with col2:
            CLAUDE_MODELS = [
                "claude-sonnet-4-5",
                "claude-opus-4-5",
                "claude-3-5-sonnet-20241022",
                "claude-opus-4",
            ]
            claude_model = st.selectbox(
                "Model",
                CLAUDE_MODELS,
                index=CLAUDE_MODELS.index(config.claude_model) if config.claude_model in CLAUDE_MODELS else 0
            )

        st.divider()
        st.markdown("#### OpenAI GPT")

        col1, col2 = st.columns([3, 1])

        with col1:
            openai_key = st.text_input(
                "OpenAI API Key",
                value=config.openai_key if config.openai_key else "",
                type="password",
                placeholder="sk-...",
                help="OpenAI Platform'dan alın: https://platform.openai.com/api-keys"
            )

        with col2:
            openai_model = st.selectbox(
                "Model",
                ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                index=0 if not config.openai_model else
                      (0 if "4o" in config.openai_model else 1)
            )

        st.divider()
        st.markdown("#### Kalite Ayarları")

        col1, col2 = st.columns(2)

        with col1:
            confidence_high = st.slider(
                "Yüksek Güven Eşiği",
                0.0, 1.0, config.confidence_high,
                0.05,
                help="Bu değerin üzerindeki alanlar otomatik kabul edilir"
            )

        with col2:
            confidence_low = st.slider(
                "Düşük Güven Eşiği",
                0.0, 1.0, config.confidence_low,
                0.05,
                help="Bu değerin altındaki alanlar manuel girişe yönlendirilir"
            )

        st.divider()

        # Kaydet butonu
        submitted = st.form_submit_button(
            "💾 Kaydet",
            type="primary",
            use_container_width=True
        )

        if submitted:
            # Yeni config oluştur
            new_config = APIConfig(
                gemini_key=gemini_key,
                claude_key=claude_key,
                openai_key=openai_key,
                gemini_model=gemini_model,
                claude_model=claude_model,
                openai_model=openai_model,
                confidence_high=confidence_high,
                confidence_low=confidence_low,
            )

            # Kaydet
            save_config(new_config)
            st.session_state.config = new_config

            # Router'ı yenile
            router_created = False
            if new_config.available_providers():
                try:
                    st.session_state.router = ModelRouter(new_config)
                    router_created = True
                except Exception as e:
                    st.error(f"Router başlatma hatası: {str(e)}")

            # Başarı mesajı
            if router_created or new_config.available_providers():
                st.success("✅ Ayarlar kaydedildi!")

                # Eksik paketleri kontrol et ve bilgilendir
                missing_packages = []
                if gemini_key and ModelProvider.GEMINI not in (st.session_state.router.available_providers if st.session_state.router else []):
                    missing_packages.append("google-generativeai")
                if claude_key and ModelProvider.CLAUDE not in (st.session_state.router.available_providers if st.session_state.router else []):
                    missing_packages.append("anthropic")
                if openai_key and ModelProvider.OPENAI not in (st.session_state.router.available_providers if st.session_state.router else []):
                    missing_packages.append("openai")

                if missing_packages:
                    st.warning(f"""
                    ⚠️ API key kaydedildi ancak bazı paketler yüklü değil:

                    ```bash
                    pip install {' '.join(missing_packages)}
                    ```

                    Paketleri yükledikten sonra uygulamayı yeniden başlatın.
                    """)
            else:
                st.success("✅ Ayarlar kaydedildi!")

            st.rerun()

    st.divider()

    # Aktif modeller
    st.markdown("### 🤖 Aktif Modeller")

    providers = config.available_providers()

    if providers:
        for provider in providers:
            if provider == ModelProvider.GEMINI:
                st.success(f"✅ **Gemini** - {config.gemini_model}")
            elif provider == ModelProvider.CLAUDE:
                st.success(f"✅ **Claude** - {config.claude_model}")
            elif provider == ModelProvider.OPENAI:
                st.success(f"✅ **OpenAI** - {config.openai_model}")

        # Routing stratejisi
        st.markdown("### 📍 Routing Stratejisi")

        if st.session_state.router:
            from core.models import TaskType

            st.info("Sistem her görev için en uygun modeli otomatik seçer:")

            tasks = {
                TaskType.EXTRACTION: "Veri Çıkarma (görsel, PDF, metin)",
                TaskType.CODE_GENERATION: "Kod Üretme (Excel kodu)",
                TaskType.VALIDATION: "Doğrulama (anomali tespiti)",
            }

            for task_type, task_desc in tasks.items():
                try:
                    decision = st.session_state.router.get_routing_decision(task_type)

                    st.markdown(f"""
                    **{task_desc}:**
                    - Birincil: `{decision['primary_model']}`
                    - Yedekler: {', '.join(f'`{m}`' for m in decision['fallback_chain'][:2]) if decision['fallback_chain'] else 'Yok'}
                    - Maliyet (1K token): `${decision['estimated_cost']:.4f}`
                    """)
                except:
                    pass

    else:
        st.warning("⚠ Hiç API key ayarlanmamış. Lütfen en az bir key ekleyin.")

    st.divider()

    # API Key nasıl alınır
    with st.expander("❓ API Key Nasıl Alınır?"):
        st.markdown("""
        ### Google Gemini API Key

        1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine gidin
        2. Google hesabınızla giriş yapın
        3. "Get API Key" butonuna tıklayın
        4. "Create API key" seçin
        5. Anahtarı kopyalayın ve yukarıdaki alana yapıştırın

        **Fiyatlandırma:** İlk 2 milyon token ücretsiz (aylık)

        ---

        ### Anthropic Claude API Key

        1. [Anthropic Console](https://console.anthropic.com/) adresine gidin
        2. Hesap oluşturun (kredi kartı gerekebilir)
        3. Settings → API Keys bölümüne gidin
        4. "Create Key" butonuna tıklayın
        5. Anahtarı kopyalayın

        **Fiyatlandırma:** $3-15/1M token (model bazlı)

        ---

        ### OpenAI API Key

        1. [OpenAI Platform](https://platform.openai.com/api-keys) adresine gidin
        2. Hesap oluşturun ve kredi yükleyin ($5 minimum)
        3. "Create new secret key" butonuna tıklayın
        4. Anahtarı kopyalayın (**bir kez gösterilir!**)

        **Fiyatlandırma:** $2.50-30/1M token (model bazlı)
        """)

    st.divider()

    # Tehlikeli bölüm
    with st.expander("🗑️ Tehlikeli Bölüm", expanded=False):
        st.warning("**DİKKAT:** Bu işlemler geri alınamaz!")

        if st.button("🔄 Tüm Ayarları Sıfırla", type="secondary"):
            new_config = APIConfig()  # Boş config
            save_config(new_config)
            st.session_state.config = new_config
            st.session_state.router = None
            st.success("✅ Ayarlar sıfırlandı")
            st.rerun()
