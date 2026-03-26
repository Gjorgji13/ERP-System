import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_FILE = Path("erp_db.sqlite3")


def get_connection():
    """Return a connection to the ERP database."""
    return sqlite3.connect(DB_FILE)


# -----------------------------
# 1️⃣ Open Purchase Orders
# -----------------------------
def get_open_purchase_orders(supplier_id=None, date_from=None, date_to=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT po.id, po.total_amount, po.status, po.created_at,
               s.name AS supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.status IN ('Open', 'Partially Received')
    """
    params = []

    if supplier_id:
        query += " AND po.supplier_id = ?"
        params.append(supplier_id)
    if date_from:
        query += " AND po.created_at >= ?"
        params.append(date_from)  # string
    if date_to:
        query += " AND po.created_at <= ?"
        params.append(date_to)    # string

    query += " ORDER BY po.created_at ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -----------------------------
# 2️⃣ Unreceived PO Items
# -----------------------------
def get_unreceived_po_items(supplier_id=None, date_from=None, date_to=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT poi.id, poi.product_id, p.name AS product_name,
               poi.ordered_quantity, poi.received_quantity,
               po.id AS purchase_order_id, po.status AS po_status,
               s.id AS supplier_id
        FROM purchase_order_items poi
        JOIN products p ON poi.product_id = p.id
        JOIN purchase_orders po ON poi.purchase_order_id = po.id
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE poi.received_quantity < poi.ordered_quantity
    """
    params = []

    if supplier_id:
        query += " AND s.id = ?"
        params.append(supplier_id)
    if date_from:
        query += " AND po.created_at >= ?"
        params.append(date_from)
    if date_to:
        query += " AND po.created_at <= ?"
        params.append(date_to)

    query += " ORDER BY po.created_at ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -----------------------------
# 3️⃣ Over-invoiced POs
# -----------------------------
def get_over_invoiced_pos(supplier_id=None, date_from=None, date_to=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT po.id, po.total_amount,
               COALESCE(SUM(si.total_amount), 0) AS invoiced_total,
               s.name AS supplier_name, s.id AS supplier_id,
               po.created_at
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        LEFT JOIN supplier_invoices si ON si.purchase_order_id = po.id
        GROUP BY po.id
        HAVING invoiced_total > po.total_amount
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]

    # Apply filters manually using strings
    if supplier_id:
        result = [r for r in result if r["supplier_id"] == supplier_id]
    if date_from:
        result = [r for r in result if r["created_at"] >= date_from]
    if date_to:
        result = [r for r in result if r["created_at"] <= date_to]

    return result


# -----------------------------
# 4️⃣ Low Stock Alerts
# -----------------------------
def get_low_stock(threshold=10):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.product_id, p.name AS product_name, i.quantity
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.quantity <= ?
        ORDER BY i.quantity ASC
    """, (threshold,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -----------------------------
# 5️⃣ Payables Aging
# -----------------------------
def get_payables_aging(days_overdue=30):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    today = datetime.now().date()
    cutoff = today - timedelta(days=days_overdue)

    cursor.execute("""
        SELECT si.id AS invoice_id, si.invoice_number, si.total_amount, si.status,
               si.due_date, s.name AS supplier_name
        FROM supplier_invoices si
        JOIN suppliers s ON si.supplier_id = s.id
        WHERE (si.status != 'Paid') AND (si.due_date IS NOT NULL AND si.due_date <= ?)
        ORDER BY si.due_date ASC
    """, (cutoff.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -----------------------------
# 6️⃣ Aggregated Dashboard Stats
# -----------------------------
def get_dashboard_summary(low_stock_threshold=10, supplier_id=None, date_from=None, date_to=None):
    return {
        "open_pos_count": len(get_open_purchase_orders(supplier_id, date_from, date_to)),
        "unreceived_items_count": len(get_unreceived_po_items(supplier_id, date_from, date_to)),
        "over_invoiced_pos_count": len(get_over_invoiced_pos(supplier_id, date_from, date_to)),
        "low_stock_count": len(get_low_stock(low_stock_threshold)),
        "payables_overdue_count": len(get_payables_aging())
    }


# -----------------------------
# 7️⃣ Filters for Graphs
# -----------------------------
def get_inventory_for_graph(supplier_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT i.product_id, p.name AS product_name, i.quantity
        FROM inventory i
        JOIN products p ON i.product_id = p.id
    """
    params = []
    if supplier_id:
        query += " JOIN suppliers s ON p.supplier_id = s.id WHERE s.id = ?"
        params.append(supplier_id)

    query += " ORDER BY i.quantity ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_po_values_for_graph(supplier_id=None, date_from=None, date_to=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT po.id AS po_id, po.total_amount AS po_total,
               COALESCE(SUM(si.total_amount), 0) AS invoiced_total,
               po.status AS po_status, po.created_at, po.supplier_id
        FROM purchase_orders po
        LEFT JOIN supplier_invoices si ON si.purchase_order_id = po.id
        ORDER BY po.created_at ASC
    """)
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]

    # Apply filters manually using strings
    if supplier_id:
        result = [r for r in result if r["supplier_id"] == supplier_id]
    if date_from:
        result = [
            r for r in result
            if r["created_at"] is not None and r["created_at"] >= date_from
        ]

    if date_to:
        result = [
            r for r in result
            if r["created_at"] is not None and r["created_at"] <= date_to
        ]

    return result


# -----------------------------
# 8️⃣ Suppliers List
# -----------------------------
def get_suppliers_list():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM suppliers ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]