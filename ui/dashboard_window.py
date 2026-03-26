# ui/dashboard_window.py
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QSpinBox, QMessageBox,
    QComboBox, QDateEdit
)
from PySide6.QtCharts import (
    QChart, QChartView,
    QBarSeries, QBarSet,
    QCategoryAxis, QValueAxis
)

from models.dashboard_model import (
    get_dashboard_summary,
    get_inventory_for_graph,
    get_po_values_for_graph,
    get_open_purchase_orders,
    get_unreceived_po_items,
    get_over_invoiced_pos,
    get_low_stock,
    get_payables_aging,
    get_suppliers_list
)


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP Management Dashboard")
        self.setMinimumSize(1300, 750)

        # Drill-down state
        self.inventory_drill_product = None
        self.po_drill_po_id = None

        # ----------------- KPI LABELS -----------------
        self.kpi_labels = {
            "open_pos_count": QLabel(),
            "unreceived_items_count": QLabel(),
            "over_invoiced_pos_count": QLabel(),
            "low_stock_count": QLabel(),
            "payables_overdue_count": QLabel()
        }

        kpi_layout = QHBoxLayout()
        for label in self.kpi_labels.values():
            label.setStyleSheet("font-size:16px; font-weight:bold; padding:6px;")
            kpi_layout.addWidget(label)

        # ----------------- CHART VIEWS -----------------
        self.inventory_chart_view = QChartView()
        self.po_chart_view = QChartView()

        charts_layout = QHBoxLayout()
        charts_layout.addWidget(self.inventory_chart_view)
        charts_layout.addWidget(self.po_chart_view)

        # ----------------- FILTERS -----------------
        self.low_stock_spin = QSpinBox()
        self.low_stock_spin.setRange(1, 100)
        self.low_stock_spin.setValue(10)

        self.po_filter_combo = QComboBox()
        self.po_filter_combo.addItems(["All POs", "Open POs", "Over-invoiced POs"])

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("All Suppliers", None)
        for s in get_suppliers_list() or []:
            self.supplier_combo.addItem(s["name"], s["id"])

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        self.refresh_btn = QPushButton("Refresh Dashboard")
        self.refresh_btn.clicked.connect(self.refresh_dashboard)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Low Stock ≤"))
        filter_layout.addWidget(self.low_stock_spin)
        filter_layout.addWidget(QLabel("PO Filter"))
        filter_layout.addWidget(self.po_filter_combo)
        filter_layout.addWidget(QLabel("Supplier"))
        filter_layout.addWidget(self.supplier_combo)
        filter_layout.addWidget(QLabel("From"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(self.refresh_btn)

        # ----------------- DETAIL TABLE -----------------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Type", "ID", "Name", "Quantity / Amount", "Status / Info"]
        )

        # ----------------- MAIN LAYOUT -----------------
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(kpi_layout)
        main_layout.addLayout(charts_layout)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(QLabel("Detailed View"))
        main_layout.addWidget(self.table)

        self.refresh_dashboard()

    # ----------------- REFRESH -----------------
    def refresh_dashboard(self):
        try:
            self.low_stock_threshold = self.low_stock_spin.value()
            self.po_filter = self.po_filter_combo.currentText()
            self.supplier_id = self.supplier_combo.currentData()
            self.date_from_val = self.date_from.date().toString("yyyy-MM-dd")
            self.date_to_val = self.date_to.date().toString("yyyy-MM-dd")

            summary = get_dashboard_summary(
                self.low_stock_threshold,
                self.supplier_id,
                self.date_from_val,
                self.date_to_val
            )

            self.kpi_labels["open_pos_count"].setText(f"Open POs: {summary['open_pos_count']}")
            self.kpi_labels["unreceived_items_count"].setText(f"Unreceived Items: {summary['unreceived_items_count']}")
            self.kpi_labels["over_invoiced_pos_count"].setText(f"Over-invoiced POs: {summary['over_invoiced_pos_count']}")
            self.kpi_labels["low_stock_count"].setText(f"Low Stock: {summary['low_stock_count']}")
            self.kpi_labels["payables_overdue_count"].setText(f"Payables Overdue: {summary['payables_overdue_count']}")

            self.update_inventory_chart()
            self.update_po_chart()
            self.update_detail_table()

        except Exception as e:
            QMessageBox.critical(self, "Dashboard Error", str(e))

    # ----------------- INVENTORY CHART -----------------
    def update_inventory_chart(self):
        data = get_inventory_for_graph(self.supplier_id)

        series = QBarSeries()
        bar_set = QBarSet("Quantity")
        categories = []

        for row in data:
            bar_set.append(row["quantity"])
            categories.append(row["product_name"])

        bar_set.clicked.connect(self.on_inventory_bar_clicked)
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Inventory Quantities")

        axis_x = QCategoryAxis()
        for i, name in enumerate(categories):
            axis_x.append(name, i)
        axis_y = QValueAxis()

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self.inventory_chart_view.setChart(chart)

    def on_inventory_bar_clicked(self, index):
        data = get_inventory_for_graph(self.supplier_id)
        self.inventory_drill_product = data[index]["product_name"]
        self.update_detail_table()

    # ----------------- PO CHART -----------------
    def update_po_chart(self):
        data = get_po_values_for_graph(
            self.supplier_id,
            self.date_from_val,
            self.date_to_val
        )

        if self.po_filter == "Open POs":
            data = [d for d in data if d["po_status"] == "Open"]
        elif self.po_filter == "Over-invoiced POs":
            data = [d for d in data if d["invoiced_total"] > d["po_total"]]

        series = QBarSeries()
        po_set = QBarSet("PO Total")
        inv_set = QBarSet("Invoiced")

        categories = []
        for row in data:
            po_set.append(row["po_total"])
            inv_set.append(row["invoiced_total"])
            categories.append(str(row["po_id"]))

        po_set.clicked.connect(self.on_po_bar_clicked)
        series.append(po_set)
        series.append(inv_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"PO vs Invoiced ({self.po_filter})")

        axis_x = QCategoryAxis()
        for i, c in enumerate(categories):
            axis_x.append(c, i)
        axis_y = QValueAxis()

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self.po_chart_view.setChart(chart)
        self._po_chart_data = data

    def on_po_bar_clicked(self, index):
        self.po_drill_po_id = self._po_chart_data[index]["po_id"]
        self.update_detail_table()

    # ----------------- DETAIL TABLE -----------------
    def update_detail_table(self):
        self.table.setRowCount(0)

        def add_row(values):
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, v in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))

        for po in get_open_purchase_orders(self.supplier_id, self.date_from_val, self.date_to_val):
            if self.po_drill_po_id and po["id"] != self.po_drill_po_id:
                continue
            add_row(["Open PO", po["id"], po["supplier_name"], po["total_amount"], po["status"]])

        for item in get_unreceived_po_items(self.supplier_id, self.date_from_val, self.date_to_val):
            if self.inventory_drill_product and item["product_name"] != self.inventory_drill_product:
                continue
            add_row([
                "Unreceived Item",
                item["id"],
                item["product_name"],
                f"{item['ordered_quantity']} / {item['received_quantity']}",
                item["po_status"]
            ])

        for po in get_over_invoiced_pos(self.supplier_id, self.date_from_val, self.date_to_val):
            add_row(["Over-invoiced PO", po["id"], po["supplier_name"], po["invoiced_total"], "Over"])

        for p in get_low_stock(self.low_stock_threshold):
            if self.inventory_drill_product and p["product_name"] != self.inventory_drill_product:
                continue
            add_row(["Low Stock", p["product_id"], p["product_name"], p["quantity"], "Below Threshold"])

        for inv in get_payables_aging():
            add_row(["Overdue Invoice", inv["invoice_id"], inv["supplier_name"], inv["total_amount"], inv["due_date"]])