# ui/purchase_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog
)

from models.purchase_model import (
    get_all_purchase_orders,
    create_purchase_order,
    get_purchase_order_items,
    receive_purchase_order_item
)
from models.supplier_model import get_all_suppliers
from models.product_model import get_all_products


class PurchaseWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Purchase Orders")
        self.setMinimumSize(900, 600)

        # -------- PO TABLE --------
        self.po_table = QTableWidget()
        self.po_table.setColumnCount(5)
        self.po_table.setHorizontalHeaderLabels(
            ["PO ID", "Supplier", "Created By", "Created At", "Status"]
        )
        self.po_table.itemSelectionChanged.connect(self.load_po_items)

        # -------- PO ITEMS TABLE --------
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Item ID", "Product", "Ordered", "Received", "Remaining", "Unit Cost"
        ])

        # -------- BUTTONS --------
        self.create_btn = QPushButton("Create PO")
        self.receive_btn = QPushButton("Receive Selected Item")
        self.refresh_btn = QPushButton("Refresh")

        self.create_btn.clicked.connect(self.create_po)
        self.receive_btn.clicked.connect(self.receive_item)
        self.refresh_btn.clicked.connect(self.load_orders)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.receive_btn)
        btn_layout.addWidget(self.refresh_btn)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Purchase Orders"))
        layout.addWidget(self.po_table)
        layout.addWidget(QLabel("PO Items"))
        layout.addWidget(self.items_table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.load_orders()

    # ---------------- Load POs ----------------
    def load_orders(self):
        orders = get_all_purchase_orders()
        self.po_table.setRowCount(len(orders))

        for row, po in enumerate(orders):
            self.po_table.setItem(row, 0, QTableWidgetItem(str(po["id"])))
            self.po_table.setItem(row, 1, QTableWidgetItem(po["supplier_name"]))
            self.po_table.setItem(row, 2, QTableWidgetItem(str(po["created_by"])))
            self.po_table.setItem(row, 3, QTableWidgetItem(po["created_at"]))
            self.po_table.setItem(row, 4, QTableWidgetItem(po["status"]))

        self.items_table.setRowCount(0)

    # ---------------- Load PO Items ----------------
    def load_po_items(self):
        row = self.po_table.currentRow()
        if row < 0:
            return

        po_id = int(self.po_table.item(row, 0).text())
        items = get_purchase_order_items(po_id)

        self.items_table.setRowCount(len(items))
        for r, item in enumerate(items):
            remaining = item["ordered_quantity"] - item["received_quantity"]

            self.items_table.setItem(r, 0, QTableWidgetItem(str(item["id"])))
            self.items_table.setItem(r, 1, QTableWidgetItem(item["product_name"]))
            self.items_table.setItem(r, 2, QTableWidgetItem(str(item["ordered_quantity"])))
            self.items_table.setItem(r, 3, QTableWidgetItem(str(item["received_quantity"])))
            self.items_table.setItem(r, 4, QTableWidgetItem(str(remaining)))
            self.items_table.setItem(r, 5, QTableWidgetItem(f"{item['unit_cost']:.2f}"))

    # ---------------- Create PO ----------------
    def create_po(self):
        suppliers = get_all_suppliers()
        if not suppliers:
            QMessageBox.warning(self, "Error", "No suppliers found")
            return

        supplier_names = [s["name"] for s in suppliers]
        supplier_name, ok = QInputDialog.getItem(
            self, "Supplier", "Select supplier:", supplier_names, 0, False
        )
        if not ok:
            return

        supplier_id = next(s["id"] for s in suppliers if s["name"] == supplier_name)

        products = get_all_products()
        if not products:
            QMessageBox.warning(self, "Error", "No products available")
            return

        items = []
        for p in products:
            qty, ok = QInputDialog.getInt(
                self, f"{p['name']}",
                f"Quantity for {p['name']}:", 0, 0
            )
            if ok and qty > 0:
                items.append({
                    "product_id": p["id"],
                    "quantity": qty,
                    "unit_cost": p["price"]
                })

        if not items:
            QMessageBox.warning(self, "Error", "No items selected")
            return

        create_purchase_order(supplier_id, self.user["id"], items)
        QMessageBox.information(self, "Success", "Purchase Order created")
        self.load_orders()

    # ---------------- Receive Item ----------------
    def receive_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a PO item first")
            return

        po_item_id = int(self.items_table.item(row, 0).text())
        remaining = int(self.items_table.item(row, 4).text())

        if remaining <= 0:
            QMessageBox.information(self, "Info", "Item already fully received")
            return

        qty, ok = QInputDialog.getInt(
            self,
            "Receive Quantity",
            f"Enter quantity to receive (max {remaining}):",
            1, 1, remaining
        )
        if not ok:
            return

        receive_purchase_order_item(po_item_id, qty)
        QMessageBox.information(self, "Success", "Inventory updated")

        self.load_orders()
        self.load_po_items()