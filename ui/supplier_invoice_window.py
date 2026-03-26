# ui/supplier_invoice_window.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QInputDialog, QMessageBox
)

from models.finance_model import record_supplier_payment_finance
from models.purchase_model import get_all_purchase_orders
from models.supplier_invoice_model import (
    get_all_supplier_invoices,
    create_supplier_invoice,
    record_supplier_payment,
    delete_supplier_invoice,
    get_supplier_payments
)


class SupplierInvoiceWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Supplier Invoices")
        self.setMinimumSize(850, 500)

        # Ensure tables exist

        # -------- TABLE --------
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Invoice ID", "PO ID", "Supplier", "Invoice #", "Total Amount", "Due Date", "Status", "PO Remaining"
        ])

        # -------- BUTTONS --------
        self.create_btn = QPushButton("Create Invoice")
        self.pay_btn = QPushButton("Record Payment")
        self.delete_btn = QPushButton("Delete Invoice")
        self.view_payments_btn = QPushButton("View Payments")
        self.refresh_btn = QPushButton("Refresh")

        self.create_btn.clicked.connect(self.create_invoice)
        self.pay_btn.clicked.connect(self.record_payment)
        self.delete_btn.clicked.connect(self.delete_invoice)
        self.view_payments_btn.clicked.connect(self.view_payments)
        self.refresh_btn.clicked.connect(self.load_invoices)

        # -------- LAYOUT --------
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.pay_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.view_payments_btn)
        btn_layout.addWidget(self.refresh_btn)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Supplier Invoices"))
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load invoices initially
        self.load_invoices()

    # ---------------- Load Invoices ----------------
    def load_invoices(self):
        invoices = get_all_supplier_invoices()
        self.table.setRowCount(len(invoices))

        for row, inv in enumerate(invoices):
            self.table.setItem(row, 0, QTableWidgetItem(str(inv["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(inv["purchase_order_id"])))
            self.table.setItem(row, 2, QTableWidgetItem(inv["supplier_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(inv["invoice_number"]))
            self.table.setItem(row, 4, QTableWidgetItem(f"{inv['total_amount']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(inv.get("due_date", "")))
            self.table.setItem(row, 6, QTableWidgetItem(inv["status"]))
            self.table.setItem(row, 7, QTableWidgetItem(f"{inv['po_remaining']:.2f}"))

    # ---------------- Create Invoice ----------------
    def create_invoice(self):
        pos = get_all_purchase_orders()
        if not pos:
            QMessageBox.warning(self, "Error", "No Purchase Orders available")
            return

        po_ids = [str(po["id"]) for po in pos]
        po_id, ok = QInputDialog.getItem(self, "Select PO", "Purchase Order ID:", po_ids, 0, False)
        if not ok:
            return

        invoice_number, ok = QInputDialog.getText(self, "Invoice Number", "Enter Invoice Number:")
        if not ok or not invoice_number:
            return

        total_amount, ok = QInputDialog.getDouble(
            self, "Total Amount", "Enter Invoice Total Amount:", 0, 0, 1_000_000, 2
        )
        if not ok:
            return

        due_date, ok = QInputDialog.getText(
            self, "Due Date (optional)", "Enter Due Date (YYYY-MM-DD):"
        )
        if not ok:
            due_date = None

        selected_po = next((po for po in pos if po["id"] == int(po_id)), None)
        if not selected_po:
            QMessageBox.warning(self, "Error", "Selected Purchase Order not found")
            return
        supplier_id = selected_po["supplier_id"]

        create_supplier_invoice(int(po_id), supplier_id, invoice_number, total_amount, due_date)
        QMessageBox.information(self, "Success", f"Invoice #{invoice_number} created successfully")
        self.load_invoices()



    # ---------------- Record Payment ----------------
    def record_payment(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an invoice first")
            return

        invoice_id = int(self.table.item(row, 0).text())
        amount, ok = QInputDialog.getDouble(
            self, "Payment Amount", "Enter payment amount:", 0, 0, 1_000_000, 2
        )
        if not ok:
            return

        # Update both supplier invoice and finance ledger
        record_supplier_payment(invoice_id, amount)
        record_supplier_payment_finance(invoice_id, amount)

        QMessageBox.information(self, "Success", f"Payment of {amount:.2f} recorded for Invoice #{invoice_id}")
        self.load_invoices()

    # ---------------- Delete Invoice ----------------
    def delete_invoice(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an invoice to delete")
            return

        invoice_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete Invoice #{invoice_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            delete_supplier_invoice(invoice_id)
            QMessageBox.information(self, "Deleted", f"Invoice #{invoice_id} deleted")
            self.load_invoices()

    # ---------------- View Payments ----------------
    def view_payments(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an invoice to view payments")
            return

        invoice_id = int(self.table.item(row, 0).text())
        payments = get_supplier_payments(invoice_id)
        if not payments:
            QMessageBox.information(self, "Payments", "No payments recorded for this invoice")
            return

        msg = "\n".join([f"{p['paid_at']}: {p['amount']:.2f}" for p in payments])
        QMessageBox.information(self, f"Payments for Invoice #{invoice_id}", msg)