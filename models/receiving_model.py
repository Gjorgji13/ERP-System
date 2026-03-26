import sqlite3
from pathlib import Path

DB_FILE = Path("erp_db.sqlite3")


def get_connection():
    return sqlite3.connect(DB_FILE)


def get_receivable_purchase_orders():
    """Only POs that can still be received"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM purchase_orders
        WHERE status IN ('Open', 'Partially Received')
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_po_items(po_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT poi.id,
               poi.product_id,
               p.name AS product_name,
               poi.ordered_quantity,
               poi.received_quantity
        FROM purchase_order_items poi
        JOIN products p ON poi.product_id = p.id
        WHERE poi.purchase_order_id = ?
    """, (po_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def receive_po_items(po_id, received_map):
    """
    received_map = { po_item_id: received_now }
    """
    conn = get_connection()
    cur = conn.cursor()

    for item_id, qty in received_map.items():
        if qty <= 0:
            continue

        # Update received qty
        cur.execute("""
            UPDATE purchase_order_items
            SET received_quantity = received_quantity + ?
            WHERE id = ?
        """, (qty, item_id))

        # Update inventory
        cur.execute("""
            UPDATE inventory
            SET quantity = quantity + ?
            WHERE product_id = (
                SELECT product_id FROM purchase_order_items WHERE id = ?
            )
        """, (qty, item_id))

    # Recalculate PO status
    cur.execute("""
        SELECT
            SUM(ordered_quantity) AS ordered,
            SUM(received_quantity) AS received
        FROM purchase_order_items
        WHERE purchase_order_id = ?
    """, (po_id,))
    ordered, received = cur.fetchone()

    if received == 0:
        status = "Pending"
    elif received < ordered:
        status = "Partially Received"
    else:
        status = "Fully Received"

    cur.execute("""
        UPDATE purchase_orders
        SET status = ?
        WHERE id = ?
    """, (status, po_id))

    conn.commit()
    conn.close()