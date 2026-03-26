# models/supplier_invoice_model.py
import sqlite3
from pathlib import Path
from datetime import datetime

from models.purchase_model import (
    get_po_invoiced_total,
    get_po_received_value,
    update_po_status
)

DB_FILE = Path("erp_db.sqlite3")


def get_connection():
    return sqlite3.connect(DB_FILE)


# ---------- SETUP TABLES ----------
def setup_supplier_invoice_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_order_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        invoice_number TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        due_date TEXT,
        FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders(id),
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_invoice_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        paid_at TEXT NOT NULL,
        FOREIGN KEY(supplier_invoice_id) REFERENCES supplier_invoices(id)
    )
    """)

    conn.commit()
    conn.close()


# ---------- INVOICE CREATION (ACCOUNTING CONTROL) ----------
from typing import Optional

def create_supplier_invoice(
    purchase_order_id: int,
    supplier_id: int,
    invoice_number: str,
    total_amount: float,
    due_date: Optional[str] = None
):
    conn = get_connection()
    cursor = conn.cursor()

    # --- PO total ---
    cursor.execute(
        "SELECT total_amount FROM purchase_orders WHERE id = ?",
        (purchase_order_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Purchase Order not found")

    po_total = row[0]

    # --- Invoiced so far ---
    invoiced_total = get_po_invoiced_total(purchase_order_id)
    remaining = po_total - invoiced_total

    # ❌ HARD BLOCK: over PO balance
    if total_amount > remaining:
        conn.close()
        raise ValueError(
            f"Invoice exceeds PO remaining balance.\n"
            f"Remaining: {remaining:.2f}"
        )

    # ⚠ SOFT WARNING: over received goods value
    received_value = get_po_received_value(purchase_order_id)
    warning = None
    if total_amount > received_value:
        warning = (
            f"Invoice exceeds received goods value.\n"
            f"Received value: {received_value:.2f}"
        )

    # --- Create invoice ---
    cursor.execute("""
        INSERT INTO supplier_invoices
        (purchase_order_id, supplier_id, invoice_number,
         total_amount, status, created_at, due_date)
        VALUES (?, ?, ?, ?, 'Pending', ?, ?)
    """, (
        purchase_order_id,
        supplier_id,
        invoice_number,
        total_amount,
        datetime.now().isoformat(),
        due_date
    ))

    conn.commit()
    conn.close()

    # 🔁 Update PO status
    update_po_status(purchase_order_id)

    return warning


# ---------- READ ----------
def get_all_supplier_invoices():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            si.id,
            si.invoice_number,
            si.total_amount,
            si.status,
            si.created_at,
            si.due_date,
            po.id AS purchase_order_id,
            po.total_amount AS po_total,
            (
                SELECT COALESCE(SUM(total_amount), 0)
                FROM supplier_invoices
                WHERE purchase_order_id = po.id
            ) AS po_invoiced,
            (po.total_amount - (
                SELECT COALESCE(SUM(total_amount), 0)
                FROM supplier_invoices
                WHERE purchase_order_id = po.id
            )) AS po_remaining,
            po.status AS po_status,
            s.name AS supplier_name
        FROM supplier_invoices si
        JOIN purchase_orders po ON si.purchase_order_id = po.id
        JOIN suppliers s ON si.supplier_id = s.id
        ORDER BY si.created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------- PAYMENTS ----------
def record_supplier_payment(invoice_id: int, amount: float):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO supplier_payments (supplier_invoice_id, amount, paid_at)
        VALUES (?, ?, ?)
    """, (invoice_id, amount, datetime.now().isoformat()))

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM supplier_payments
        WHERE supplier_invoice_id = ?
    """, (invoice_id,))
    total_paid = cursor.fetchone()[0]

    cursor.execute(
        "SELECT total_amount FROM supplier_invoices WHERE id = ?",
        (invoice_id,)
    )
    total_amount = cursor.fetchone()[0]

    if total_paid >= total_amount:
        status = "Paid"
    elif total_paid > 0:
        status = "Partial"
    else:
        status = "Pending"

    cursor.execute(
        "UPDATE supplier_invoices SET status = ? WHERE id = ?",
        (status, invoice_id)
    )

    conn.commit()
    conn.close()


# ---------- DELETE ----------
def delete_supplier_invoice(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM supplier_payments WHERE supplier_invoice_id = ?",
        (invoice_id,)
    )
    cursor.execute(
        "DELETE FROM supplier_invoices WHERE id = ?",
        (invoice_id,)
    )

    conn.commit()
    conn.close()


# ---------- PAYMENTS READ ----------
def get_supplier_payments(invoice_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, amount, paid_at
        FROM supplier_payments
        WHERE supplier_invoice_id = ?
        ORDER BY paid_at ASC
    """, (invoice_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]