# models/purchase_model.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path("erp_db.sqlite3")


# --------------------------------------------------
# CREATE PURCHASE ORDER
# --------------------------------------------------
def create_purchase_order(supplier_id: int, created_by: int, items: list):
    """
    items = [{"product_id": int, "quantity": int, "unit_cost": float}]
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    # Calculate PO total
    total_amount = sum(i["quantity"] * i["unit_cost"] for i in items)

    cursor.execute("""
        INSERT INTO purchase_orders
        (supplier_id, created_by, total_amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (supplier_id, created_by, total_amount, "Open", created_at))

    po_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
            INSERT INTO purchase_order_items
            (purchase_order_id, product_id, ordered_quantity, unit_cost)
            VALUES (?, ?, ?, ?)
        """, (
            po_id,
            item["product_id"],
            item["quantity"],
            item["unit_cost"]
        ))

    conn.commit()
    conn.close()
    return po_id


# --------------------------------------------------
# GET ALL PURCHASE ORDERS
# --------------------------------------------------
def get_all_purchase_orders():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT po.*, s.name AS supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        ORDER BY po.created_at DESC
    """)

    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders


# --------------------------------------------------
# GET ITEMS FOR A SINGLE PO
# --------------------------------------------------
def get_purchase_order_items(po_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            poi.id,
            poi.product_id,
            p.name AS product_name,
            poi.ordered_quantity,
            poi.received_quantity,
            poi.unit_cost
        FROM purchase_order_items poi
        JOIN products p ON poi.product_id = p.id
        WHERE poi.purchase_order_id = ?
    """, (po_id,))

    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


# --------------------------------------------------
# RECEIVE PO ITEM (ITEM-LEVEL)
# --------------------------------------------------
def receive_purchase_order_item(po_item_id: int, quantity_received: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch PO item
    cursor.execute("""
        SELECT purchase_order_id, product_id, ordered_quantity, received_quantity
        FROM purchase_order_items
        WHERE id = ?
    """, (po_item_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Purchase order item not found")

    po_id, product_id, ordered_qty, received_qty = row

    new_received = received_qty + quantity_received
    if new_received > ordered_qty:
        conn.close()
        raise ValueError("Cannot receive more than ordered")

    # Update received quantity
    cursor.execute("""
        UPDATE purchase_order_items
        SET received_quantity = ?
        WHERE id = ?
    """, (new_received, po_item_id))

    # Update inventory (UPSERT)
    cursor.execute("""
        INSERT INTO inventory (product_id, quantity)
        VALUES (?, ?)
        ON CONFLICT(product_id)
        DO UPDATE SET quantity = quantity + excluded.quantity
    """, (product_id, quantity_received))

    # Update PO status
    cursor.execute("""
        SELECT
            SUM(ordered_quantity),
            SUM(received_quantity)
        FROM purchase_order_items
        WHERE purchase_order_id = ?
    """, (po_id,))

    ordered_sum, received_sum = cursor.fetchone()

    if received_sum == 0:
        status = "Open"
    elif received_sum < ordered_sum:
        status = "Partially Received"
    else:
        status = "Fully Received"

    cursor.execute("""
        UPDATE purchase_orders
        SET status = ?
        WHERE id = ?
    """, (status, po_id))

    conn.commit()
    conn.close()


# --------------------------------------------------
# TABLE SETUP
# --------------------------------------------------
def setup_purchase_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            ordered_quantity INTEGER NOT NULL,
            received_quantity INTEGER DEFAULT 0,
            unit_cost REAL NOT NULL,
            FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


def get_po_invoiced_total(po_id: int) -> float:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM supplier_invoices
        WHERE purchase_order_id = ?
    """, (po_id,))

    total = cursor.fetchone()[0]
    conn.close()
    return total

def get_po_received_value(po_id: int) -> float:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(received_quantity * unit_cost), 0)
        FROM purchase_order_items
        WHERE purchase_order_id = ?
    """, (po_id,))

    value = cursor.fetchone()[0]
    conn.close()
    return value


def update_po_status(po_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT total_amount FROM purchase_orders WHERE id = ?",
        (po_id,)
    )
    po_total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM supplier_invoices
        WHERE purchase_order_id = ?
    """, (po_id,))
    invoiced = cursor.fetchone()[0]

    if invoiced == 0:
        status = "Open"
    elif invoiced < po_total:
        status = "Partially Invoiced"
    else:
        status = "Fully Invoiced"

    cursor.execute(
        "UPDATE purchase_orders SET status = ? WHERE id = ?",
        (status, po_id)
    )

    conn.commit()
    conn.close()