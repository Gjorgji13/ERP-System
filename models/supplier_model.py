# models/supplier_model.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path("erp_db.sqlite3")

def add_supplier(name, contact_person, email, phone):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO suppliers (name, contact_person, email, phone, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, contact_person, email, phone, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_suppliers():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suppliers ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def setup_supplier_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT,
        email TEXT,
        phone TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def delete_supplier(supplier_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit()
    conn.close()