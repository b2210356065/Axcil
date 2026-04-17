"""Geçmiş sayfası - İşlem geçmişi ve metrikler."""
import streamlit as st
from datetime import datetime, timedelta
import os
from pathlib import Path


def show_history_page():
    """Geçmiş sayfası."""
    st.markdown('<div class="main-header">📜 Geçmiş</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">İşlem geçmişi ve istatistikler</div>',
                unsafe_allow_html=True)

    # Metrikler
    st.markdown("### 📊 Özet İstatistikler")

    col1, col2, col3, col4 = st.columns(4)

    # Outputs dizinindeki dosyaları say
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        excel_files = list(outputs_dir.glob("*.xlsx"))
        file_count = len(excel_files)

        # Toplam boyut
        total_size = sum(f.stat().st_size for f in excel_files if f.exists())
        total_size_mb = total_size / (1024 * 1024)

        # Son 24 saat
        now = datetime.now()
        recent_files = [
            f for f in excel_files
            if datetime.fromtimestamp(f.stat().st_mtime) > now - timedelta(days=1)
        ]

    else:
        file_count = 0
        total_size_mb = 0
        recent_files = []

    with col1:
        st.metric("Toplam Excel", file_count)

    with col2:
        st.metric("Son 24 Saat", len(recent_files))

    with col3:
        st.metric("Toplam Boyut", f"{total_size_mb:.1f} MB")

    with col4:
        # Aktif modeller
        providers = st.session_state.config.available_providers()
        st.metric("Aktif Model", len(providers))

    st.divider()

    # Dosya listesi
    st.markdown("### 📁 Oluşturulan Dosyalar")

    if file_count == 0:
        st.info("Henüz Excel dosyası oluşturulmamış. Araçlar sayfasından başlayın!")
        if st.button("🔧 Araçlara Git"):
            st.session_state.current_page = "tools"
            st.rerun()
        st.stop()

    # Sıralama
    sort_by = st.selectbox(
        "Sıralama",
        ["En Yeni", "En Eski", "En Büyük", "En Küçük", "İsim (A-Z)"],
        key="sort_history"
    )

    # Sıralama uygula
    if sort_by == "En Yeni":
        sorted_files = sorted(excel_files, key=lambda f: f.stat().st_mtime, reverse=True)
    elif sort_by == "En Eski":
        sorted_files = sorted(excel_files, key=lambda f: f.stat().st_mtime)
    elif sort_by == "En Büyük":
        sorted_files = sorted(excel_files, key=lambda f: f.stat().st_size, reverse=True)
    elif sort_by == "En Küçük":
        sorted_files = sorted(excel_files, key=lambda f: f.stat().st_size)
    else:  # İsim
        sorted_files = sorted(excel_files, key=lambda f: f.name)

    # Dosyaları göster
    for idx, file in enumerate(sorted_files[:50], 1):  # İlk 50 dosya
        stat = file.stat()
        size_kb = stat.st_size / 1024
        modified = datetime.fromtimestamp(stat.st_mtime)

        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            st.markdown(f"**{idx}. {file.name}**")

        with col2:
            st.text(f"{size_kb:.1f} KB")

        with col3:
            st.text(modified.strftime("%d.%m.%Y %H:%M"))

        with col4:
            # İndirme butonu
            with open(file, "rb") as f:
                st.download_button(
                    "📥 İndir",
                    f,
                    file_name=file.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{idx}"
                )

    if len(excel_files) > 50:
        st.info(f"ℹ️ Toplam {len(excel_files)} dosya var. İlk 50 tanesi gösteriliyor.")

    st.divider()

    # Temizlik
    st.markdown("### 🗑️ Temizlik")

    st.warning("**DİKKAT:** Bu işlemler geri alınamaz!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ 30 Günden Eski Dosyaları Sil"):
            now = datetime.now()
            old_threshold = now - timedelta(days=30)
            deleted = 0

            for file in excel_files:
                if datetime.fromtimestamp(file.stat().st_mtime) < old_threshold:
                    file.unlink()
                    deleted += 1

            if deleted > 0:
                st.success(f"✅ {deleted} dosya silindi")
                st.rerun()
            else:
                st.info("30 günden eski dosya bulunamadı")

    with col2:
        if st.button("🗑️ TÜM Dosyaları Sil"):
            # Onay
            confirm = st.checkbox("Tüm dosyaları silmek istediğimden eminim")

            if confirm:
                for file in excel_files:
                    file.unlink()

                st.success(f"✅ {len(excel_files)} dosya silindi")
                st.rerun()
            else:
                st.warning("⚠ Onaylamadan silinemez")

    st.divider()

    # İstatistikler (demo)
    st.markdown("### 📈 İstatistikler")

    st.info("🚧 Detaylı istatistikler yakında eklenecek!")

    st.markdown("""
    **Gelecek özellikler:**
    - Günlük/haftalık/aylık kullanım grafikleri
    - Model bazlı maliyet analizi
    - Araç kullanım istatistikleri
    - Başarı/hata oranları
    - Ortalama işlem süreleri
    """)
