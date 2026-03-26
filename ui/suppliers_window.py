# ui/suppliers_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)

from models.supplier_model import (
    get_all_suppliers,
    delete_supplier,
    add_supplier,
)


class SuppliersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Suppliers")
        self.setMinimumSize(700, 400)

        # -------- Inputs --------
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Supplier Name")

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contact Person")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone")

        self.add_button = QPushButton("Add Supplier")
        self.delete_button = QPushButton("Delete Selected")

        self.add_button.clicked.connect(self.add_supplier)
        self.delete_button.clicked.connect(self.delete_supplier)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.contact_input)
        input_layout.addWidget(self.email_input)
        input_layout.addWidget(self.phone_input)
        input_layout.addWidget(self.add_button)

        # -------- Table --------
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Contact", "Email", "Phone"]
        )

        # -------- Layout --------
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Suppliers"))
        layout.addLayout(input_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        self.load_suppliers()

    def load_suppliers(self):
        suppliers = get_all_suppliers()
        self.table.setRowCount(len(suppliers))
        for row, s in enumerate(suppliers):
            self.table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(s["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(s.get("contact_person", "")))
            self.table.setItem(row, 3, QTableWidgetItem(s.get("email", "")))
            self.table.setItem(row, 4, QTableWidgetItem(s.get("phone", "")))

    def add_supplier(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Supplier name is required")
            return

        add_supplier(
            name,
            self.contact_input.text().strip(),
            self.email_input.text().strip(),
            self.phone_input.text().strip()
        )

        self.name_input.clear()
        self.contact_input.clear()
        self.email_input.clear()
        self.phone_input.clear()

        self.load_suppliers()

    def delete_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a supplier")
            return

        supplier_id = int(self.table.item(row, 0).text())

        confirm = QMessageBox.question(
            self,
            "Confirm",
            "Delete this supplier?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            delete_supplier(supplier_id)
            self.load_suppliers()