from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from auth import authenticate
from ui.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP Login")
        self.setFixedSize(300, 200)

        # ---------------- Inputs ----------------
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # ---------------- Login Button ----------------
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        # ---------------- Layout ----------------
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Login"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        user_obj = authenticate(username, password)

        if not user_obj:
            QMessageBox.warning(self, "Error", "Invalid credentials")
            return

        # Convert user object to dictionary for MainWindow
        user_dict = {
            "id": user_obj["id"],
            "username": user_obj["username"],
            "role": user_obj["role"]
        }

        QMessageBox.information(self, "Success", f"Welcome {user_dict['username']}!")

        # Open main dashboard
        self.dashboard = MainWindow(user_dict)
        self.dashboard.show()
        self.close()
