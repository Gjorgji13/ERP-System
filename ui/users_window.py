# ui/users_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
)

from models.user_model import get_all_users


class UsersWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user

        self.setWindowTitle("Users Management")
        self.setFixedSize(500, 350)

        self.label = QLabel("System Users")

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role"])

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_users()

    def load_users(self):
        users = get_all_users()
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(user["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(user["role"]))