# ui/main_window.py
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout

from ui.finance_window import FinanceWindow
from ui.inventory_window import InventoryWindow
from ui.products_window import ProductsWindow
from ui.sales_window import SalesWindow
from ui.users_window import UsersWindow
from ui.suppliers_window import SuppliersWindow
from ui.purchase_window import PurchaseWindow
from ui.supplier_invoice_window import SupplierInvoiceWindow
from ui.dashboard_window import DashboardWindow


class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.windows = {}  # store open windows

        self.setWindowTitle("ERP Dashboard")
        self.setFixedSize(700, 450)

        # -------- Welcome Label --------
        self.welcome_label = QLabel(f"Welcome, {self.user['username']} ({self.user['role']})")

        # -------- Buttons --------
        self.products_button = QPushButton("Products")
        self.inventory_button = QPushButton("Inventory")
        self.sales_button = QPushButton("Sales")
        self.finance_button = QPushButton("Finance")
        self.suppliers_button = QPushButton("Suppliers")
        self.purchase_button = QPushButton("Purchase Orders")
        self.supplier_invoice_button = QPushButton("Supplier Invoices")
        self.users_button = QPushButton("Users")
        self.dashboard_button = QPushButton("Dashboard")

        # -------- Connections --------
        self.products_button.clicked.connect(lambda: self.open_window('products', ProductsWindow, self.user))
        self.inventory_button.clicked.connect(lambda: self.open_window('inventory', InventoryWindow, self.user))
        self.sales_button.clicked.connect(lambda: self.open_window('sales', SalesWindow, self.user))
        self.finance_button.clicked.connect(lambda: self.open_window('finance', FinanceWindow, self.user))
        self.suppliers_button.clicked.connect(lambda: self.open_window('suppliers', SuppliersWindow))
        self.purchase_button.clicked.connect(lambda: self.open_window('purchase', PurchaseWindow, self.user))
        self.supplier_invoice_button.clicked.connect(lambda: self.open_window('supplier_invoice', SupplierInvoiceWindow, self.user))
        self.dashboard_button.clicked.connect(lambda: self.open_window('dashboard', DashboardWindow))
        if self.user["role"] == "admin":
            self.users_button.clicked.connect(lambda: self.open_window('users', UsersWindow, self.user))

        # -------- Layout --------
        layout = QVBoxLayout()
        layout.addWidget(self.welcome_label)

        # Row 1
        row1 = QHBoxLayout()
        row1.addWidget(self.products_button)
        row1.addWidget(self.inventory_button)
        row1.addWidget(self.sales_button)

        # Row 2
        row2 = QHBoxLayout()
        row2.addWidget(self.suppliers_button)
        row2.addWidget(self.purchase_button)
        row2.addWidget(self.supplier_invoice_button)

        # Row 3
        row3 = QHBoxLayout()
        row3.addWidget(self.finance_button)
        row3.addWidget(self.dashboard_button)
        if self.user["role"] == "admin":
            row3.addWidget(self.users_button)

        # Add rows to main layout
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)

        self.setLayout(layout)

    # -------- Generic Window Handler --------
    def open_window(self, key: str, window_class, *args):
        """
        Opens a sub-window by key. If already open, bring to front. Otherwise create new.
        """
        window = self.windows.get(key)

        if window is None or not window.isVisible():
            # Create new window
            window = window_class(*args)
            self.windows[key] = window
            window.show()
            window.raise_()

            # Remove reference when closed
            window.destroyed.connect(lambda: self.windows.pop(key, None))
        else:
            # Window exists, bring to front
            window.raise_()
            window.activateWindow()