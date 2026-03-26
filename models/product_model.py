# product_model.py
import sqlite3
from pathlib import Path

DB_FILE = Path("erp_db.sqlite3")


def get_all_products():
    """Return a list of all products as dictionaries"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def add_product(name: str, description: str, price: float, quantity: int):
    """Add a new product to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, quantity) VALUES (?, ?, ?, ?)",
        (name, description, price, quantity)
    )
    conn.commit()
    conn.close()


def get_product_by_id(product_id: int):
    """Return a single product by ID"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_product(product_id: int, name: str, description: str, price: float, quantity: int):
    """Update an existing product"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name=?, description=?, price=?, quantity=? WHERE id=?",
        (name, description, price, quantity, product_id)
    )
    conn.commit()
    conn.close()


def delete_product(product_id: int):
    """Delete a product by ID"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def setup_products_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


