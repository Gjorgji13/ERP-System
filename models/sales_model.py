# sales_model.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path("erp_db.sqlite3")


def setup_sales_tables():
    """Create tables for sales orders and sales items if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Sales orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        FOREIGN KEY(created_by) REFERENCES users(id)
    )
    """)

    # Sales order items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sales_order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(sales_order_id) REFERENCES sales_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # Inventory movements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity_change INTEGER NOT NULL,
        type TEXT NOT NULL,  -- 'sale' or 'purchase'
        reference_id INTEGER,  -- sales_order_id or purchase_order_id
        created_at TEXT NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()


def create_sales_order(customer_name: str, created_by: int, items: list):
    """
    Create a sales order and adjust inventory
    items: list of dicts: [{"product_id": int, "quantity": int, "unit_price": float}, ...]
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sales_orders (customer_name, created_by, created_at, status) VALUES (?, ?, ?, ?)",
        (customer_name, created_by, created_at, 'Confirmed')
    )
    sales_order_id = cursor.lastrowid

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price = item["unit_price"]

        # Add to sales_order_items
        cursor.execute(
            "INSERT INTO sales_order_items (sales_order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (sales_order_id, product_id, quantity, unit_price)
        )

        # Reduce inventory
        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", (quantity, product_id))

        # Log inventory movement
        cursor.execute(
            "INSERT INTO inventory_movements (product_id, quantity_change, type, reference_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, -quantity, 'sale', sales_order_id, created_at)
        )

    conn.commit()
    conn.close()
    return sales_order_id


def get_all_sales_orders():
    """
    Return all sales orders with detailed items, including product names
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get orders with creator username
    cursor.execute("""
        SELECT o.id, o.customer_name, o.created_at, o.status, u.username as created_by
        FROM sales_orders o
        JOIN users u ON o.created_by = u.id
        ORDER BY o.created_at DESC
    """)
    orders = [dict(row) for row in cursor.fetchall()]

    # Get items for each order with product names
    for order in orders:
        cursor.execute("""
            SELECT i.product_id, p.name as product_name, i.quantity, i.unit_price, i.quantity * i.unit_price as total_price
            FROM sales_order_items i
            JOIN products p ON i.product_id = p.id
            WHERE i.sales_order_id = ?
        """, (order["id"],))
        order["items"] = [dict(row) for row in cursor.fetchall()]

        # Optional: compute order total
        order["order_total"] = sum(item["total_price"] for item in order["items"])

    conn.close()
    return orders


def delete_sales_order(sales_order_id: int):
    """
    Delete a sales order and revert inventory changes
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get items of this order
    cursor.execute(
        "SELECT product_id, quantity FROM sales_order_items WHERE sales_order_id = ?",
        (sales_order_id,)
    )
    items = cursor.fetchall()

    # Revert inventory
    for item in items:
        product_id, quantity = item
        # Add back the quantity
        cursor.execute(
            "UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?",
            (quantity, product_id)
        )
        # Log inventory reversal
        cursor.execute(
            "INSERT INTO inventory_movements (product_id, quantity_change, type, reference_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, quantity, 'sale_cancellation', sales_order_id, datetime.now().isoformat())
        )

    # Delete order items
    cursor.execute("DELETE FROM sales_order_items WHERE sales_order_id = ?", (sales_order_id,))

    # Delete the order itself
    cursor.execute("DELETE FROM sales_orders WHERE id = ?", (sales_order_id,))

    conn.commit()
    conn.close()
