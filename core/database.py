"""Veritabanı yönetimi - Çoklu iş yeri ve işlevsellik konfigürasyonları."""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app_data.db")


def get_connection():
    """Veritabanı bağlantısı."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanı tablolarını oluştur."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            business_description TEXT NOT NULL,
            sector TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS functionalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            input_fields TEXT NOT NULL,
            excel_template TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES business_profile(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            functionality_id INTEGER NOT NULL,
            user_inputs TEXT NOT NULL,
            output_file TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (functionality_id) REFERENCES functionalities(id) ON DELETE CASCADE
        )
    """)

    # Veri tipleri tablosu - özel veri tipleri saklamak için
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            icon TEXT DEFAULT '📊',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Varsayılan veri tiplerini ekle
    default_types = [
        ('Görsel', 'Fotoğraf veya resim dosyası', '📸'),
        ('PDF', 'PDF belgesi', '📄'),
        ('Metin', 'Serbest metin veya yapılandırılmış metin', '✏️'),
        ('Ses', 'Ses kaydı veya ses dosyası', '🎤'),
        ('Form', 'Yapılandırılmış form girişi', '📝'),
        ('Excel', 'Mevcut Excel dosyası', '📊'),
    ]

    for dtype_name, dtype_desc, dtype_icon in default_types:
        cursor.execute(
            "INSERT OR IGNORE INTO data_types (name, description, icon) VALUES (?, ?, ?)",
            (dtype_name, dtype_desc, dtype_icon)
        )

    conn.commit()

    # Migration: is_active sütununu ekle (eski veritabanları için)
    try:
        cursor.execute("SELECT is_active FROM business_profile LIMIT 1")
    except sqlite3.OperationalError:
        # Sütun yok, ekle
        cursor.execute("ALTER TABLE business_profile ADD COLUMN is_active INTEGER DEFAULT 0")
        conn.commit()

    # Migration: data_type_id sütununu ekle (functionalities tablosuna)
    try:
        cursor.execute("SELECT data_type_id FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN data_type_id INTEGER DEFAULT 3")
        conn.commit()

    # Migration: data_type_ids sütunu (çoklu veri tipi desteği - JSON array)
    try:
        cursor.execute("SELECT data_type_ids FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN data_type_ids TEXT DEFAULT '[]'")
        cursor.execute("UPDATE functionalities SET data_type_ids = '[' || COALESCE(data_type_id, 3) || ']' WHERE data_type_ids = '[]' OR data_type_ids IS NULL")
        conn.commit()

    # Migration: is_default sütunu (varsayılan veri tiplerini korumak için)
    try:
        cursor.execute("SELECT is_default FROM data_types LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE data_types ADD COLUMN is_default INTEGER DEFAULT 0")
        cursor.execute("UPDATE data_types SET is_default = 1 WHERE name IN ('Görsel', 'PDF', 'Metin', 'Ses', 'Form', 'Excel')")
        conn.commit()

    # Migration: enriched_definition sütunu (zenginleştirilmiş iş tanımı JSON)
    try:
        cursor.execute("SELECT enriched_definition FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN enriched_definition TEXT DEFAULT NULL")
        conn.commit()

    # Migration: algorithm_path sütunu (üretilen algoritma dosya yolu)
    try:
        cursor.execute("SELECT algorithm_path FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN algorithm_path TEXT DEFAULT NULL")
        conn.commit()

    # Migration: algorithm_version sütunu (algoritma versiyon takibi)
    try:
        cursor.execute("SELECT algorithm_version FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN algorithm_version INTEGER DEFAULT 0")
        conn.commit()

    # Migration: algorithm_generated_at sütunu
    try:
        cursor.execute("SELECT algorithm_generated_at FROM functionalities LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE functionalities ADD COLUMN algorithm_generated_at TEXT DEFAULT NULL")
        conn.commit()

    # Zenginleştirme denemeleri tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            functionality_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL,
            enriched_definition TEXT NOT NULL,
            user_feedback TEXT DEFAULT NULL,
            status TEXT DEFAULT 'rejected',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (functionality_id) REFERENCES functionalities(id) ON DELETE CASCADE
        )
    """)

    # Algoritma denemeleri tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS algorithm_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            functionality_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL,
            code TEXT NOT NULL,
            status TEXT DEFAULT 'failed',
            test_results TEXT,
            user_feedback TEXT,
            ai_failure_report TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (functionality_id) REFERENCES functionalities(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# İş Yeri İşlemleri

def get_all_businesses():
    """Tüm iş yerlerini getir."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM business_profile ORDER BY is_active DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_business_by_id(business_id: int):
    """ID'ye göre iş yeri getir."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM business_profile WHERE id=?", (business_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_active_business():
    """Aktif iş yerini getir."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM business_profile WHERE is_active=1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_business(name: str, description: str, sector: str):
    """Yeni iş yeri oluştur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO business_profile
           (business_name, business_description, sector, is_active)
           VALUES (?, ?, ?, 0)""",
        (name, description, sector),
    )
    business_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return business_id


def update_business(business_id: int, name: str, description: str, sector: str):
    """İş yerini güncelle."""
    conn = get_connection()
    conn.execute(
        """UPDATE business_profile
           SET business_name=?, business_description=?, sector=?, updated_at=?
           WHERE id=?""",
        (name, description, sector, datetime.now().isoformat(), business_id),
    )
    conn.commit()
    conn.close()


def delete_business(business_id: int):
    """İş yerini sil (ve ilişkili tüm veriler)."""
    conn = get_connection()
    conn.execute("DELETE FROM business_profile WHERE id=?", (business_id,))
    conn.commit()
    conn.close()


def set_active_business(business_id: int):
    """Aktif iş yerini ayarla."""
    conn = get_connection()
    # Önce tüm iş yerlerini pasif yap
    conn.execute("UPDATE business_profile SET is_active=0")
    # Seçileni aktif yap
    conn.execute("UPDATE business_profile SET is_active=1 WHERE id=?", (business_id,))
    conn.commit()
    conn.close()


# İşlevsellik İşlemleri

def get_functionalities(business_id: int):
    """Bir iş yerine ait işlevsellikleri getir."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM functionalities WHERE business_id=? ORDER BY id",
        (business_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_functionality(business_id: int, name: str, description: str,
                      input_fields: list, excel_template: dict, system_prompt: str,
                      data_type_id: int = 3, data_type_ids: list = None):
    """Yeni işlevsellik ekle. Aynı isimde varsa None döner."""
    conn = get_connection()

    # Aynı isimde işlevsellik var mı kontrol et
    existing = conn.execute(
        "SELECT id FROM functionalities WHERE business_id=? AND name=?",
        (business_id, name)
    ).fetchone()

    if existing:
        conn.close()
        return None

    if data_type_ids is None:
        data_type_ids = [data_type_id]

    conn.execute(
        """INSERT INTO functionalities
           (business_id, name, description, input_fields, excel_template, system_prompt, data_type_id, data_type_ids)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (business_id, name, description,
         json.dumps(input_fields, ensure_ascii=False),
         json.dumps(excel_template, ensure_ascii=False),
         system_prompt, data_type_ids[0] if data_type_ids else data_type_id,
         json.dumps(data_type_ids)),
    )
    conn.commit()
    conn.close()
    return True


def update_functionality(func_id: int, name: str, description: str,
                        input_fields: list, excel_template: dict, system_prompt: str,
                        data_type_ids: list = None):
    """İşlevselliği güncelle. Aynı isimde başka kayıt varsa None döner."""
    conn = get_connection()

    # Aynı isimde başka işlevsellik var mı kontrol et (kendi kaydı hariç)
    existing = conn.execute(
        """SELECT id FROM functionalities
           WHERE business_id=(SELECT business_id FROM functionalities WHERE id=?)
           AND name=? AND id!=?""",
        (func_id, name, func_id)
    ).fetchone()

    if existing:
        conn.close()
        return None

    if data_type_ids is not None:
        conn.execute(
            """UPDATE functionalities
               SET name=?, description=?, input_fields=?, excel_template=?, system_prompt=?,
                   data_type_id=?, data_type_ids=?
               WHERE id=?""",
            (name, description,
             json.dumps(input_fields, ensure_ascii=False),
             json.dumps(excel_template, ensure_ascii=False),
             system_prompt, data_type_ids[0] if data_type_ids else 3,
             json.dumps(data_type_ids), func_id),
        )
    else:
        conn.execute(
            """UPDATE functionalities
               SET name=?, description=?, input_fields=?, excel_template=?, system_prompt=?
               WHERE id=?""",
            (name, description,
             json.dumps(input_fields, ensure_ascii=False),
             json.dumps(excel_template, ensure_ascii=False),
             system_prompt, func_id),
        )

    conn.commit()
    conn.close()
    return True


def get_functionality_by_id(func_id: int):
    """ID'ye göre işlevsellik getir."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM functionalities WHERE id=?", (func_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def delete_functionality(func_id: int):
    """İşlevselliği sil."""
    conn = get_connection()
    conn.execute("DELETE FROM functionalities WHERE id=?", (func_id,))
    conn.commit()
    conn.close()


# Geçmiş İşlemleri

def save_generation(functionality_id: int, user_inputs: dict, output_file: str):
    """Üretim geçmişi kaydet."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO generation_history (functionality_id, user_inputs, output_file) VALUES (?, ?, ?)",
        (functionality_id, json.dumps(user_inputs, ensure_ascii=False), output_file),
    )
    conn.commit()
    conn.close()


def get_history(functionality_id: Optional[int] = None, limit: int = 20):
    """Geçmiş kayıtları getir."""
    conn = get_connection()
    if functionality_id:
        rows = conn.execute(
            """SELECT h.*, f.name as func_name, b.business_name
               FROM generation_history h
               JOIN functionalities f ON h.functionality_id = f.id
               JOIN business_profile b ON f.business_id = b.id
               WHERE h.functionality_id=?
               ORDER BY h.id DESC LIMIT ?""",
            (functionality_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT h.*, f.name as func_name, b.business_name
               FROM generation_history h
               JOIN functionalities f ON h.functionality_id = f.id
               JOIN business_profile b ON f.business_id = b.id
               ORDER BY h.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Yardımcı Fonksiyonlar

def count_businesses() -> int:
    """Toplam iş yeri sayısı."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM business_profile").fetchone()[0]
    conn.close()
    return count


def count_functionalities(business_id: Optional[int] = None) -> int:
    """İşlevsellik sayısı."""
    conn = get_connection()
    if business_id:
        count = conn.execute(
            "SELECT COUNT(*) FROM functionalities WHERE business_id=?",
            (business_id,)
        ).fetchone()[0]
    else:
        count = conn.execute("SELECT COUNT(*) FROM functionalities").fetchone()[0]
    conn.close()
    return count


# Veri Tipi İşlemleri

def get_all_data_types():
    """Tüm veri tiplerini getir."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM data_types ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_data_type_by_id(dtype_id: int):
    """ID'ye göre veri tipi getir."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM data_types WHERE id=?", (dtype_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_data_type_by_name(name: str):
    """İsme göre veri tipi getir."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM data_types WHERE name=?", (name,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_data_type(name: str, description: str = "", icon: str = "📊"):
    """Yeni veri tipi oluştur."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO data_types (name, description, icon) VALUES (?, ?, ?)",
            (name, description, icon)
        )
        dtype_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return dtype_id
    except sqlite3.IntegrityError:
        # Aynı isimde veri tipi zaten var
        conn.close()
        return None


def delete_data_type(dtype_id: int):
    """Veri tipini sil."""
    conn = get_connection()
    conn.execute("DELETE FROM data_types WHERE id=?", (dtype_id,))
    conn.commit()
    conn.close()


# Zenginleştirme İşlemleri

def save_enrichment_attempt(func_id: int, enriched_definition: str,
                            status: str = "rejected", user_feedback: str = None):
    """Zenginleştirme denemesi kaydet."""
    conn = get_connection()
    # Mevcut deneme sayısını al
    row = conn.execute(
        "SELECT COUNT(*) FROM enrichment_attempts WHERE functionality_id=?",
        (func_id,)
    ).fetchone()
    attempt_number = row[0] + 1

    conn.execute(
        """INSERT INTO enrichment_attempts
           (functionality_id, attempt_number, enriched_definition, status, user_feedback)
           VALUES (?, ?, ?, ?, ?)""",
        (func_id, attempt_number, enriched_definition, status, user_feedback),
    )
    conn.commit()
    conn.close()
    return attempt_number


def get_enrichment_attempts(func_id: int):
    """Bir iş tanımının tüm zenginleştirme denemelerini getir."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM enrichment_attempts
           WHERE functionality_id=? ORDER BY attempt_number""",
        (func_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rejected_enrichments(func_id: int):
    """Reddedilen zenginleştirme denemelerini getir (iteratif prompt için)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM enrichment_attempts
           WHERE functionality_id=? AND status='rejected'
           ORDER BY attempt_number""",
        (func_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def accept_enrichment(func_id: int, enriched_definition: str, attempt_id: int = None):
    """Zenginleştirilmiş tanımı onayla ve functionalities tablosuna kaydet."""
    conn = get_connection()
    # functionalities tablosunu güncelle
    conn.execute(
        "UPDATE functionalities SET enriched_definition=? WHERE id=?",
        (enriched_definition, func_id),
    )
    # Deneme durumunu güncelle
    if attempt_id:
        conn.execute(
            "UPDATE enrichment_attempts SET status='accepted' WHERE id=?",
            (attempt_id,),
        )
    conn.commit()
    conn.close()


def reject_enrichment(attempt_id: int, feedback: str):
    """Zenginleştirme denemesini reddet ve geri bildirim ekle."""
    conn = get_connection()
    conn.execute(
        "UPDATE enrichment_attempts SET status='rejected', user_feedback=? WHERE id=?",
        (feedback, attempt_id),
    )
    conn.commit()
    conn.close()


# Algoritma İşlemleri

def save_algorithm_attempt(func_id: int, code: str, status: str = "failed",
                           test_results: str = None, ai_failure_report: str = None,
                           user_feedback: str = None):
    """Algoritma denemesi kaydet."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM algorithm_attempts WHERE functionality_id=?",
        (func_id,)
    ).fetchone()
    attempt_number = row[0] + 1

    conn.execute(
        """INSERT INTO algorithm_attempts
           (functionality_id, attempt_number, code, status,
            test_results, ai_failure_report, user_feedback)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (func_id, attempt_number, code, status,
         test_results, ai_failure_report, user_feedback),
    )
    conn.commit()
    conn.close()
    return attempt_number


def get_algorithm_attempts(func_id: int):
    """Bir iş tanımının tüm algoritma denemelerini getir."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM algorithm_attempts
           WHERE functionality_id=? ORDER BY attempt_number""",
        (func_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_failed_algorithm_attempts(func_id: int):
    """Başarısız algoritma denemelerini getir (iteratif prompt için)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM algorithm_attempts
           WHERE functionality_id=? AND status='failed'
           ORDER BY attempt_number""",
        (func_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_algorithm_success(func_id: int, algorithm_path: str, code: str,
                           test_results: str = None):
    """Başarılı algoritmayı kaydet — dosya yolu ve versiyon güncelle."""
    conn = get_connection()
    # Mevcut versiyonu al
    row = conn.execute(
        "SELECT algorithm_version FROM functionalities WHERE id=?",
        (func_id,)
    ).fetchone()
    new_version = (row[0] or 0) + 1 if row else 1

    # functionalities tablosunu güncelle
    conn.execute(
        """UPDATE functionalities
           SET algorithm_path=?, algorithm_version=?,
               algorithm_generated_at=?
           WHERE id=?""",
        (algorithm_path, new_version, datetime.now().isoformat(), func_id),
    )

    # Başarılı denemeyi kaydet
    attempt_row = conn.execute(
        "SELECT COUNT(*) FROM algorithm_attempts WHERE functionality_id=?",
        (func_id,)
    ).fetchone()
    attempt_number = attempt_row[0] + 1

    conn.execute(
        """INSERT INTO algorithm_attempts
           (functionality_id, attempt_number, code, status, test_results)
           VALUES (?, ?, ?, 'success', ?)""",
        (func_id, attempt_number, code, test_results),
    )

    conn.commit()
    conn.close()
    return new_version


def clear_algorithm(func_id: int):
    """İş tanımının algoritmasını sıfırla (tanım değiştiğinde)."""
    conn = get_connection()
    conn.execute(
        """UPDATE functionalities
           SET algorithm_path=NULL, algorithm_version=0,
               algorithm_generated_at=NULL
           WHERE id=?""",
        (func_id,),
    )
    conn.commit()
    conn.close()
