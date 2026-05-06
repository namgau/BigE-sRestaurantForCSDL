# gui_login.py - Màn hình đăng nhập
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LoginWindow(QWidget):
    """Cửa sổ đăng nhập hệ thống."""
    login_success = pyqtSignal(object)  # Signal gửi User khi đăng nhập thành công

    def __init__(self, dao):
        super().__init__()
        self.dao = dao
        self.setWindowTitle("Đăng nhập - Quản lý Nhà hàng")
        self.setFixedSize(420, 520)
        self.setup_ui()
        self.setStyleSheet(self._styles())

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card chứa form
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedSize(360, 440)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 32, 32, 32)

        # Icon & Tiêu đề
        icon_lbl = QLabel("")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Epstein's Restaurant")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Hệ thống Quản lý Nhà hàng")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Input username
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Tên đăng nhập")
        self.txt_user.setMinimumHeight(44)

        # Input password
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Mật khẩu")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setMinimumHeight(44)
        self.txt_pass.returnPressed.connect(self.do_login)

        # Nút đăng nhập
        btn_login = QPushButton("ĐĂNG NHẬP")
        btn_login.setObjectName("btnLogin")
        btn_login.setMinimumHeight(46)
        btn_login.clicked.connect(self.do_login)
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)

        hint = QLabel("Xin chào")
        hint.setObjectName("hintLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(icon_lbl)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.txt_user)
        card_layout.addWidget(self.txt_pass)
        card_layout.addSpacing(8)
        card_layout.addWidget(btn_login)
        card_layout.addWidget(hint)
        layout.addWidget(card)

    def do_login(self):
        username = self.txt_user.text().strip()
        password = self.txt_pass.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        user = self.dao.authenticate(username, password)
        if user:
            self.login_success.emit(user)
            self.close()
        else:
            QMessageBox.critical(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")

    def _styles(self):
        return """
        QWidget { background: #f0f2f5; }
        #loginCard { background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px; }
        #titleLabel { color: #000000; font: bold 22px 'Segoe UI'; }
        #subtitleLabel { color: #666666; font: 14px 'Segoe UI'; }
        QLineEdit { background: #ffffff; border: 1px solid #ced4da;
            border-radius: 6px; padding: 10px 14px; color: #000000; font: 14px 'Segoe UI'; }
        QLineEdit:focus { border: 1px solid #1976d2; }
        #btnLogin { background: #1976d2; color: #fff; border: none;
            border-radius: 6px; font: bold 15px 'Segoe UI'; }
        #btnLogin:hover { background: #1565c0; }
        #hintLabel { color: #999999; font: 12px 'Segoe UI'; }
        """
