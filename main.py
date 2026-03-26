# main.py
import sys
from PySide6.QtWidgets import QApplication

from ui.login_window import LoginWindow

# --- IMPORT ALL SETUP FUNCTIONS ---
from models.user_model import setup_users_table, create_user
from models.product_model import setup_products_tables
from models.inventory_model import setup_inventory_tables
from models.sales_model import setup_sales_tables
from models.purchase_model import setup_purchase_tables
from models.supplier_model import setup_supplier_tables
from models.finance_model import setup_finance_tables
from models.supplier_invoice_model import setup_supplier_invoice_tables


def setup_database():
    """Create ALL database tables. Safe to run every startup."""
    setup_users_table()
    setup_supplier_tables()
    setup_products_tables()
    setup_inventory_tables()
    setup_sales_tables()
    setup_purchase_tables()
    setup_supplier_invoice_tables()
    setup_finance_tables()

    # Ensure admin user exists
    create_user("admin", "admin123", "admin")


if __name__ == "__main__":
    setup_database()  # 🔑 THIS IS THE KEY

    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())