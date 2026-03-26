# ui/products_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QMessageBox
)
from models.product_model import get_all_products, add_product

class ProductsWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Products")
        self.setFixedSize(600, 400)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Price", "Quantity"])
        self.load_products()

        # --- Add product form ---
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 100000)
        self.price_input.setPrefix("$ ")
        self.price_input.setDecimals(2)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(0, 10000)

        self.add_button = QPushButton("Add Product")
        self.add_button.clicked.connect(self.add_product)

        form_layout = QHBoxLayout()
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(self.qty_input)
        form_layout.addWidget(self.add_button)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Products"))
        layout.addWidget(self.table)
        layout.addLayout(form_layout)
        self.setLayout(layout)

    def load_products(self):
        self.table.setRowCount(0)
        products = get_all_products()
        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(product["description"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{product['price']:.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(product["quantity"])))

    def add_product(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        price = self.price_input.value()
        qty = self.qty_input.value()

        if not name:
            QMessageBox.warning(self, "Error", "Product name cannot be empty")
            return

        add_product(name, desc, price, qty)
        QMessageBox.information(self, "Success", f"Product '{name}' added")
        self.name_input.clear()
        self.desc_input.clear()
        self.price_input.setValue(0)
        self.qty_input.setValue(0)
        self.load_products()