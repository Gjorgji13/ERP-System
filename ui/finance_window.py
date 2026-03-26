# finance_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog
)

from models.finance_model import (
    setup_finance_tables, get_all_invoices, record_payment, get_ledger
)


class FinanceWindow(QWidget):
    def __init__(self, user):
        """
        user: dict returned from authenticate() -> {"id", "username", "role"}
        """
        super().__init__()
        self.user = user
        self.setWindowTitle("Finance / Accounting")
        self.setFixedSize(800, 600)

        # Ensure finance tables exist
        setup_finance_tables()

        # ---------------- Widgets ----------------
        self.invoices_label = QLabel("Invoices")
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(5)
        self.invoices_table.setHorizontalHeaderLabels(
            ["ID", "Sales Order", "Due Date", "Total Amount", "Status"]
        )

        self.payments_label = QLabel("Record Payment")
        self.invoice_id_input = QLineEdit()
        self.invoice_id_input.setPlaceholderText("Invoice ID")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.record_payment_button = QPushButton("Record Payment")
        self.record_payment_button.clicked.connect(self.record_payment_clicked)

        self.ledger_label = QLabel("Ledger")
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(6)
        self.ledger_table.setHorizontalHeaderLabels(
            ["ID", "Date", "Description", "Debit", "Credit", "Balance"]
        )

        # ---------------- Layout ----------------
        layout = QVBoxLayout()
        layout.addWidget(self.invoices_label)
        layout.addWidget(self.invoices_table)

        payment_layout = QHBoxLayout()
        payment_layout.addWidget(self.invoice_id_input)
        payment_layout.addWidget(self.amount_input)
        payment_layout.addWidget(self.record_payment_button)

        layout.addWidget(self.payments_label)
        layout.addLayout(payment_layout)
        layout.addWidget(self.ledger_label)
        layout.addWidget(self.ledger_table)

        self.setLayout(layout)

        # Load initial data
        self.load_invoices()
        self.load_ledger()

    # ---------------- Methods ----------------
    def load_invoices(self):
        invoices = get_all_invoices()
        self.invoices_table.setRowCount(len(invoices))
        for row, invoice in enumerate(invoices):
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice.get("id", ""))))
            self.invoices_table.setItem(row, 1, QTableWidgetItem(str(invoice.get("sales_order_id", ""))))
            self.invoices_table.setItem(row, 2, QTableWidgetItem(invoice.get("due_date", "")))
            self.invoices_table.setItem(row, 3, QTableWidgetItem(str(invoice.get("total_amount", ""))))
            self.invoices_table.setItem(row, 4, QTableWidgetItem(invoice.get("status", "")))

    def load_ledger(self):
        ledger_entries = get_ledger()
        self.ledger_table.setRowCount(len(ledger_entries))
        for row, entry in enumerate(ledger_entries):
            self.ledger_table.setItem(row, 0, QTableWidgetItem(str(entry.get("id", ""))))
            self.ledger_table.setItem(row, 1, QTableWidgetItem(entry.get("date", "")))
            self.ledger_table.setItem(row, 2, QTableWidgetItem(entry.get("description", "")))
            self.ledger_table.setItem(row, 3, QTableWidgetItem(str(entry.get("debit", ""))))
            self.ledger_table.setItem(row, 4, QTableWidgetItem(str(entry.get("credit", ""))))
            self.ledger_table.setItem(row, 5, QTableWidgetItem(str(entry.get("balance", ""))))

    def record_payment_clicked(self):
        try:
            invoice_id = int(self.invoice_id_input.text())
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Invoice ID must be an integer and Amount must be numeric")
            return

        record_payment(invoice_id, amount)
        QMessageBox.information(
            self, "Success", f"Payment of {amount} recorded for Invoice #{invoice_id}"
        )

        # Refresh tables
        self.load_invoices()
        self.load_ledger()

        # Clear inputs
        self.invoice_id_input.clear()
        self.amount_input.clear()