"""Veritabanı yönetimi - İş yeri tanımları ve işlevsellik konfigürasyonları."""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "app_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            business_description TEXT NOT NULL,
            sector TEXT,
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
            FOREIGN KEY (business_id) REFERENCES business_profile(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            functionality_id INTEGER NOT NULL,
            user_inputs TEXT NOT NULL,
            output_file TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (functionality_id) REFERENCES functionalities(id)
        )
    """)

    conn.commit()
    conn.close()


def get_business_profile():
    conn = get_connection()
    row = conn.execute("SELECT * FROM business_profile ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def save_business_profile(name, description, sector):
    conn = get_connection()
    existing = get_business_profile()
    if existing:
        conn.execute(
            "UPDATE business_profile SET business_name=?, business_description=?, sector=?, updated_at=? WHERE id=?",
            (name, description, sector, datetime.now().isoformat(), existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO business_profile (business_name, business_description, sector) VALUES (?, ?, ?)",
            (name, description, sector),
        )
    conn.commit()
    conn.close()


def get_functionalities(business_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM functionalities WHERE business_id=? ORDER BY id", (business_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_functionality(business_id, name, description, input_fields, excel_template, system_prompt):
    conn = get_connection()
    conn.execute(
        """INSERT INTO functionalities
           (business_id, name, description, input_fields, excel_template, system_prompt)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (business_id, name, description, json.dumps(input_fields, ensure_ascii=False),
         json.dumps(excel_template, ensure_ascii=False), system_prompt),
    )
    conn.commit()
    conn.close()


def delete_functionality(func_id):
    conn = get_connection()
    conn.execute("DELETE FROM functionalities WHERE id=?", (func_id,))
    conn.commit()
    conn.close()


def update_functionality(func_id, name, description, input_fields, excel_template, system_prompt):
    conn = get_connection()
    conn.execute(
        """UPDATE functionalities
           SET name=?, description=?, input_fields=?, excel_template=?, system_prompt=?
           WHERE id=?""",
        (name, description, json.dumps(input_fields, ensure_ascii=False),
         json.dumps(excel_template, ensure_ascii=False), system_prompt, func_id),
    )
    conn.commit()
    conn.close()


def save_generation(functionality_id, user_inputs, output_file):
    conn = get_connection()
    conn.execute(
        "INSERT INTO generation_history (functionality_id, user_inputs, output_file) VALUES (?, ?, ?)",
        (functionality_id, json.dumps(user_inputs, ensure_ascii=False), output_file),
    )
    conn.commit()
    conn.close()


def get_history(functionality_id=None, limit=20):
    conn = get_connection()
    if functionality_id:
        rows = conn.execute(
            """SELECT h.*, f.name as func_name FROM generation_history h
               JOIN functionalities f ON h.functionality_id = f.id
               WHERE h.functionality_id=? ORDER BY h.id DESC LIMIT ?""",
            (functionality_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT h.*, f.name as func_name FROM generation_history h
               JOIN functionalities f ON h.functionality_id = f.id
               ORDER BY h.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
