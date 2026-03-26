# ui/sales_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox
)
from models.sales_model import get_all_sales_orders, create_sales_order, delete_sales_order
from models.product_model import get_all_products

class SalesWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Sales Orders")
        self.setMinimumSize(600, 400)

        self.label = QLabel(f"Sales Orders (User: {self.user['username']})")

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Order ID", "Customer", "Created By", "Created At", "Status"])
        self.table.cellDoubleClicked.connect(self.view_order_items)

        # Buttons
        self.add_button = QPushButton("Add Sales Order")
        self.delete_button = QPushButton("Delete Selected Order")
        self.refresh_button = QPushButton("Refresh")
        self.add_button.clicked.connect(self.add_sales_order)
        self.delete_button.clicked.connect(self.delete_selected_order)
        self.refresh_button.clicked.connect(self.load_sales_orders)

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.delete_button)
        btn_layout.addWidget(self.refresh_button)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.load_sales_orders()

    def load_sales_orders(self):
        orders = get_all_sales_orders()
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(str(order["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(order["customer_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(order["created_by"])))
            self.table.setItem(row, 3, QTableWidgetItem(order["created_at"]))
            self.table.setItem(row, 4, QTableWidgetItem(order["status"]))

    def view_order_items(self, row, _):
        order_id = int(self.table.item(row, 0).text())
        orders = get_all_sales_orders()
        order = next((o for o in orders if o["id"] == order_id), None)
        if not order:
            return
        items_text = "\n".join([f"Product ID: {i['product_id']}, Qty: {i['quantity']}, Unit Price: {i['unit_price']}"
                                for i in order["items"]])
        QMessageBox.information(self, f"Order {order_id} Items", items_text or "No items.")

    def add_sales_order(self):
        customer_name, ok = QInputDialog.getText(self, "Customer Name", "Enter customer name:")
        if not ok or not customer_name:
            return

        products = get_all_products()
        if not products:
            QMessageBox.warning(self, "Error", "No products available!")
            return

        items = []
        for product in products:
            qty, ok = QInputDialog.getInt(self, f"Quantity for {product['name']}", f"Enter quantity for {product['name']}:", 0, 0)
            if ok and qty > 0:
                items.append({"product_id": product["id"], "quantity": qty, "unit_price": product["price"]})

        if not items:
            QMessageBox.warning(self, "Error", "No products selected for the order!")
            return

        create_sales_order(customer_name, self.user["id"], items)
        QMessageBox.information(self, "Success", "Sales order created successfully!")
        self.load_sales_orders()

    def delete_selected_order(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Error", "No order selected!")
            return
        order_id = int(self.table.item(selected, 0).text())
        confirm = QMessageBox.question(self, "Confirm", f"Delete order {order_id} and restore inventory?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_sales_order(order_id)
            QMessageBox.information(self, "Deleted", "Sales order deleted and inventory restored.")
            self.load_sales_orders()