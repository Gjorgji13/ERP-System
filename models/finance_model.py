# finance_model.py
import sqlite3
from datetime import datetime
from pathlib import Path

from models.supplier_invoice_model import record_supplier_payment as sip_record_payment

DB_FILE = Path("erp_db.sqlite3")


def setup_finance_tables():
    """Create finance-related tables if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Invoices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sales_order_id INTEGER NOT NULL,
        invoice_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Unpaid',
        FOREIGN KEY(sales_order_id) REFERENCES sales_orders(id)
    )
    """)

    # Payments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """)

    # Ledger Entries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        balance REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# ---------------- CRUD Functions ----------------

def create_invoice(sales_order_id: int, due_date: str, total_amount: float):
    """Add a new invoice"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    invoice_date = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO invoices (sales_order_id, invoice_date, due_date, total_amount, status)
        VALUES (?, ?, ?, ?, 'Unpaid')
    """, (sales_order_id, invoice_date, due_date, total_amount))
    invoice_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return invoice_id


def get_all_invoices():
    """Return all invoices as dictionaries"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices")
    invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return invoices


def record_payment(invoice_id: int, amount: float):
    """Record a payment for an invoice and update invoice status"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    payment_date = datetime.now().isoformat()

    # Add payment
    cursor.execute("""
        INSERT INTO payments (invoice_id, payment_date, amount)
        VALUES (?, ?, ?)
    """, (invoice_id, payment_date, amount))

    # Update invoice status
    cursor.execute("SELECT total_amount FROM invoices WHERE id=?", (invoice_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id=?", (invoice_id,))
    paid = cursor.fetchone()[0]

    status = 'Paid' if paid >= total else 'Partial'
    cursor.execute("UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))

    # Add to ledger
    cursor.execute("SELECT MAX(balance) FROM ledger")
    last_balance = cursor.fetchone()[0] or 0
    new_balance = last_balance + amount  # income increases balance
    cursor.execute("""
        INSERT INTO ledger (date, description, debit, credit, balance)
        VALUES (?, ?, 0, ?, ?)
    """, (payment_date, f"Payment for invoice #{invoice_id}", amount, new_balance))

    conn.commit()
    conn.close()


def get_all_payments():
    """Return all payments as dictionaries"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments")
    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return payments


def get_ledger():
    """Return all ledger entries"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ledger ORDER BY date")
    ledger_entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ledger_entries

# models/finance_model.py (append at the end)

def record_supplier_payment_finance(invoice_id: int, amount: float):
    """
    Record supplier payment and also update the general ledger
    """
    # Step 1: Record payment in supplier invoice system
    sip_record_payment(invoice_id, amount)

    # Step 2: Update Ledger
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    payment_date = datetime.now().isoformat()
    description = f"Supplier Payment for Invoice #{invoice_id}"

    # For simplicity: Debit = Accounts Payable (Expense), Credit = Cash
    cursor.execute("""
        INSERT INTO ledger (date, description, debit, credit, balance)
        SELECT ?, ?, ?, 0, 
            COALESCE((SELECT balance FROM ledger ORDER BY id DESC LIMIT 1), 0) + ? - 0
    """, (payment_date, description, amount, amount))  # Debit
    cursor.execute("""
        INSERT INTO ledger (date, description, debit, credit, balance)
        SELECT ?, ?, 0, ?, 
            COALESCE((SELECT balance FROM ledger ORDER BY id DESC LIMIT 1), 0) - 0 + 0 - ?
    """, (payment_date, description, amount, amount))  # Credit

    conn.commit()
    conn.close()