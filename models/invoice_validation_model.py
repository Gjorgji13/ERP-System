import sqlite3
from pathlib import Path

DB_FILE = Path("erp_db.sqlite3")


def get_connection():
    return sqlite3.connect(DB_FILE)


def get_po_financials(po_id):
    conn = get_connection()
    cur = conn.cursor()

    # PO total
    cur.execute("SELECT total_amount FROM purchase_orders WHERE id = ?", (po_id,))
    po_total = cur.fetchone()[0]

    # Invoiced total
    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM supplier_invoices
        WHERE purchase_order_id = ?
    """, (po_id,))
    invoiced_total = cur.fetchone()[0]

    # Received value (qty * unit cost)
    cur.execute("""
        SELECT SUM(poi.received_quantity * poi.unit_price)
        FROM purchase_order_items poi
        WHERE poi.purchase_order_id = ?
    """, (po_id,))
    received_value = cur.fetchone()[0] or 0

    conn.close()
    return po_total, invoiced_total, received_value