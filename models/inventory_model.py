# models/inventory_model.py
import sqlite3
from pathlib import Path
from database import get_connection  # Optional if you have a helper
DB_FILE = Path("erp_db.sqlite3")

# ------------------- TABLE SETUP -------------------
def setup_inventory_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Add total_value and avg_cost
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        total_value REAL NOT NULL DEFAULT 0,
        avg_cost REAL NOT NULL DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()


# ------------------- GET INVENTORY -------------------
def get_all_inventory():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.product_id, p.name AS product_name,
               i.quantity, i.total_value, i.avg_cost
        FROM inventory i
        JOIN products p ON i.product_id = p.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ------------------- UPDATE INVENTORY -------------------
def add_inventory(product_id: int, quantity: int, unit_cost: float):
    """Add inventory and update valuation (avg_cost)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if inventory exists
    cursor.execute("SELECT id, quantity, total_value FROM inventory WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    if row:
        inv_id, current_qty, current_value = row
        new_qty = current_qty + quantity
        new_total_value = current_value + quantity * unit_cost
        avg_cost = new_total_value / new_qty if new_qty else 0
        cursor.execute("""
            UPDATE inventory
            SET quantity=?, total_value=?, avg_cost=?
            WHERE id=?
        """, (new_qty, new_total_value, avg_cost, inv_id))
    else:
        cursor.execute("""
            INSERT INTO inventory (product_id, quantity, total_value, avg_cost)
            VALUES (?, ?, ?, ?)
        """, (product_id, quantity, quantity * unit_cost, unit_cost))

    conn.commit()
    conn.close()


def update_inventory(inventory_id: int, quantity: int, total_value: float = None):
    """Manually update quantity and optionally total_value (recompute avg_cost)."""
    conn = get_connection()
    cursor = conn.cursor()

    if total_value is not None:
        avg_cost = total_value / quantity if quantity else 0
        cursor.execute("""
            UPDATE inventory SET quantity=?, total_value=?, avg_cost=? WHERE id=?
        """, (quantity, total_value, avg_cost, inventory_id))
    else:
        cursor.execute("UPDATE inventory SET quantity=? WHERE id=?", (quantity, inventory_id))

    conn.commit()
    conn.close()


def delete_inventory(inventory_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id=?", (inventory_id,))
    conn.commit()
    conn.close()