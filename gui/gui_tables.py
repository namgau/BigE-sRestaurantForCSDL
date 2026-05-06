# gui_tables.py - Sơ đồ bàn & Đặt bàn
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QGridLayout, QFrame, QDialog, QLineEdit, QSpinBox,
                              QDateEdit, QTimeEdit, QTextEdit, QMessageBox,
                              QComboBox, QScrollArea, QGroupBox)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import date, time
from database.models import Booking


class TableButton(QPushButton):
    """Nút đại diện cho một bàn ăn trên sơ đồ."""
    def __init__(self, table):
        super().__init__()
        self.table = table
        self.setFixedSize(130, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_display()

    def update_display(self):
        t = self.table
        self.setText(f"Bàn {t.table_number}\n{t.area}\n{t.capacity} chỗ\n{self._vn_status()}")
        colors = {'available': '#2ecc71', 'occupied': '#e74c3c',
                  'reserved': '#f39c12', 'maintenance': '#95a5a6'}
        c = colors.get(t.status, '#95a5a6')
        self.setStyleSheet(f"""
            QPushButton {{ background: {c}; color: white; border-radius: 12px;
                font: bold 12px 'Segoe UI'; border: 2px solid rgba(255,255,255,0.3); }}
            QPushButton:hover {{ border: 3px solid #fff; }}
        """)

    def _vn_status(self):
        m = {'available': '🟢 Trống', 'occupied': '🔴 Đang dùng',
             'reserved': '🟡 Đã đặt', 'maintenance': '⚪ Bảo trì'}
        return m.get(self.table.status, self.table.status)


class BookingDialog(QDialog):
    """Dialog đặt bàn."""
    def __init__(self, table, user_id, parent=None):
        super().__init__(parent)
        self.table = table
        self.user_id = user_id
        self.result_booking = None
        self.setWindowTitle(f"Đặt bàn {table.table_number}")
        self.setFixedSize(400, 420)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("QDialog { background: #ffffff; color: #000000; } QLabel { color: #000000; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"<b>Bàn {self.table.table_number}</b> - {self.table.area} ({self.table.capacity} chỗ)"))

        self.txt_name = QLineEdit(); self.txt_name.setPlaceholderText("Tên khách")
        self.txt_name.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")
        self.txt_phone = QLineEdit(); self.txt_phone.setPlaceholderText("Số điện thoại")
        self.txt_phone.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")
        self.spn_count = QSpinBox(); self.spn_count.setRange(1, self.table.capacity); self.spn_count.setValue(2)
        self.spn_count.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")
        self.date_edit = QDateEdit(QDate.currentDate()); self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")
        self.txt_note = QTextEdit(); self.txt_note.setMaximumHeight(60)
        self.txt_note.setPlaceholderText("Ghi chú...")
        self.txt_note.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#ffffff;")

        for lbl, w in [("Tên khách *:", self.txt_name), ("SĐT:", self.txt_phone),
                        ("Số khách:", self.spn_count), ("Ngày:", self.date_edit),
                        ("Giờ:", self.time_edit), ("Ghi chú:", self.txt_note)]:
            layout.addWidget(QLabel(lbl))
            layout.addWidget(w)

        btn = QPushButton("✅ Xác nhận đặt bàn")
        btn.setMinimumHeight(40)
        btn.setStyleSheet("background:#2ecc71;color:#fff;border:none;border-radius:8px;font:bold 14px 'Segoe UI';")
        btn.clicked.connect(self.confirm)
        layout.addWidget(btn)

    def confirm(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên khách!")
            return
        qd = self.date_edit.date(); qt = self.time_edit.time()
        self.result_booking = Booking(
            table_id=self.table.table_id, user_id=self.user_id,
            guest_name=self.txt_name.text().strip(),
            guest_phone=self.txt_phone.text().strip(),
            guest_count=self.spn_count.value(),
            booking_date=date(qd.year(), qd.month(), qd.day()),
            booking_time=time(qt.hour(), qt.minute()),
            note=self.txt_note.toPlainText().strip()
        )
        self.accept()


class TableMapWidget(QWidget):
    """Widget sơ đồ bàn chính."""
    table_clicked = pyqtSignal(object)  # Gửi table object khi click

    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = restaurant_id
        self.table_buttons = []
        self.setup_ui()
        self.load_tables()

    def showEvent(self, event):
        """Auto refresh when tab is shown."""
        super().showEvent(event)
        self.load_tables()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Header
        header = QHBoxLayout()
        title = QLabel("SƠ ĐỒ BÀN")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.setStyleSheet("background:#3498db;color:#fff;border:none;border-radius:6px;padding:8px 16px;font:13px 'Segoe UI';")
        btn_refresh.clicked.connect(self.load_tables)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Scroll area chứa grid bàn
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        # Legend
        legend = QHBoxLayout()
        for color, text in [("#2ecc71","Trống"),("#e74c3c","Đang dùng"),
                             ("#f39c12","Đã đặt"),("#95a5a6","Bảo trì")]:
            lbl = QLabel(f"  ⬤ {text}")
            lbl.setStyleSheet(f"color:{color};font:12px 'Segoe UI';")
            legend.addWidget(lbl)
        legend.addStretch()
        layout.addLayout(legend)

    def load_tables(self):
        """Tải danh sách bàn - ưu tiên từ Redis, fallback SQL Server."""
        # Xóa grid cũ
        for btn in self.table_buttons:
            btn.deleteLater()
        self.table_buttons.clear()

        # Lấy bàn từ SQL Server (source of truth)
        tables = self.dao.get_all_tables(self.rid)

        # Cập nhật cache Redis (nếu có)
        tables_data = [{'table_id': t.table_id, 'table_number': t.table_number,
                        'capacity': t.capacity, 'area': t.area, 'status': t.status}
                       for t in tables]
        self.cache.set_all_tables(self.rid, tables_data)

        # Nhóm bàn theo khu vực
        areas = {}
        for t in tables:
            areas.setdefault(t.area, []).append(t)

        row = 0
        for area, area_tables in areas.items():
            lbl = QLabel(f"📍 {area}")
            lbl.setStyleSheet("color:#f39c12;font:bold 14px 'Segoe UI';padding:4px;")
            self.grid_layout.addWidget(lbl, row, 0, 1, 5)
            row += 1
            col = 0
            for t in area_tables:
                btn = TableButton(t)
                btn.clicked.connect(lambda checked, tb=t: self.table_clicked.emit(tb))
                self.grid_layout.addWidget(btn, row, col)
                self.table_buttons.append(btn)
                col += 1
                if col >= 5:
                    col = 0; row += 1
            row += 1
