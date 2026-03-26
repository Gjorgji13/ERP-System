# ui/inventory_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem
)
from models.inventory_model import get_all_inventory

class InventoryWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Inventory")
        self.setFixedSize(700, 400)

        # -------- TABLE --------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Product ID", "Product Name", "Quantity", "Total Value", "Avg Cost"
        ])

        # -------- MAIN LAYOUT --------
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Inventory (Valuation Included)"))
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_inventory()

    def load_inventory(self):
        inventory = get_all_inventory()
        self.table.setRowCount(len(inventory))
        for row, item in enumerate(inventory):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["product_id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item['total_value']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['avg_cost']:.2f}"))