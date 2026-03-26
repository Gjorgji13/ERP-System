from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QSpinBox
)

from models.receiving_model import (
    get_receivable_purchase_orders,
    get_po_items,
    receive_po_items
)


class ReceivePurchaseOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Receive Purchase Order")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)

        # PO selector
        top = QHBoxLayout()
        top.addWidget(QLabel("Purchase Order:"))

        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.load_items)
        top.addWidget(self.po_combo)

        layout.addLayout(top)

        # Items table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Item ID",
            "Product",
            "Ordered",
            "Received",
            "Remaining",
            "Receive Now"
        ])
        layout.addWidget(self.table)

        # Receive button
        self.receive_btn = QPushButton("Receive Items")
        self.receive_btn.clicked.connect(self.receive_items)
        layout.addWidget(self.receive_btn)

        self.load_pos()

    def load_pos(self):
        self.po_combo.clear()
        for po in get_receivable_purchase_orders():
            self.po_combo.addItem(f"PO #{po['id']}", po["id"])

    def load_items(self):
        po_id = self.po_combo.currentData()
        if not po_id:
            return

        items = get_po_items(po_id)
        self.table.setRowCount(0)

        for row, item in enumerate(items):
            remaining = item["ordered_quantity"] - item["received_quantity"]
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["ordered_quantity"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item["received_quantity"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(remaining)))

            spin = QSpinBox()
            spin.setRange(0, remaining)
            self.table.setCellWidget(row, 5, spin)

    def receive_items(self):
        po_id = self.po_combo.currentData()
        if not po_id:
            return

        received_map = {}

        for row in range(self.table.rowCount()):
            item_id = int(self.table.item(row, 0).text())
            spin = self.table.cellWidget(row, 5)
            qty = spin.value()
            if qty > 0:
                received_map[item_id] = qty

        if not received_map:
            QMessageBox.warning(self, "Nothing to receive", "Enter quantities first.")
            return

        receive_po_items(po_id, received_map)
        QMessageBox.information(self, "Success", "Items received successfully.")

        self.load_items()