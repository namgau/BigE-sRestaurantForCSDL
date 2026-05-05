# ============================================================
# main_gui.py - File khởi chạy chính
# Hệ thống Quản lý Nhà hàng - PyQt6
# ============================================================
# Chạy: python main_gui.py
# ============================================================
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget,
                              QVBoxLayout, QHBoxLayout, QWidget, QLabel,
                              QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from app_config import APP_CONFIG
from database_dao import DatabaseDAO
from redis_cache import RedisCache
from gui_login import LoginWindow
from gui_tables import TableMapWidget, BookingDialog
from gui_order import OrderWidget
from gui_kitchen import KitchenWidget
from gui_billing import BillingWidget
from gui_manager import ManagerWidget, ReportWidget
from gui_booking import BookingWidget


class MainWindow(QMainWindow):
    """Cửa sổ chính sau khi đăng nhập thành công."""
    def __init__(self, user, dao, cache):
        super().__init__()
        self.user = user
        self.dao = dao
        self.cache = cache
        self.rid = APP_CONFIG['RESTAURANT_ID']
        self.setWindowTitle(f"{APP_CONFIG['APP_TITLE']} | {user.full_name} ({self._role_vn()})")
        self.setMinimumSize(1200, 750)
        self.setup_ui()

    def _role_vn(self):
        m = {'manager':'Quản lý','receptionist':'Lễ tân','waiter':'Phục vụ',
             'chef':'Bếp'}
        return m.get(self.user.position, self.user.position)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== SIDEBAR =====
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame{background: #ffffff; border-right: 1px solid #e0e0e0;}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo = QLabel("Epstein's")
        logo.setStyleSheet("color:#000000;font:bold 18px 'Segoe UI';padding:20px;background:#f8f9fa;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(logo)

        # User info
        info = QLabel(f"👤 {self.user.full_name}\n🏷️ {self._role_vn()}")
        info.setStyleSheet("color:#555555;font:12px 'Segoe UI';padding:12px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(info)

        # Stacked widget cho content
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:#f0f2f5;")

        # Tạo menu theo vai trò
        self.nav_buttons = []
        pages = self._get_pages_for_role()
        for name, widget in pages:
            btn = QPushButton(f"  {name}")
            btn.setStyleSheet("""
                QPushButton{text-align:left;color:#000000;background:transparent;
                    border:none;padding:14px 20px;font:14px 'Segoe UI';}
                QPushButton:hover{background:#f8f9fa;}
                QPushButton:checked{background:#e3f2fd;
                    border-left:4px solid #1976d2;font:bold 14px 'Segoe UI';color:#1976d2;}
            """)
            btn.setCheckable(True)
            idx = self.stack.addWidget(widget)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._switch_page(i, b))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Nút đăng xuất
        btn_logout = QPushButton("  Đăng xuất")
        btn_logout.setStyleSheet("""
            QPushButton{text-align:left;color:#d32f2f;background:transparent;
                border:none;padding:14px 20px;font:14px 'Segoe UI';}
            QPushButton:hover{background:#ffebee;}
        """)
        btn_logout.clicked.connect(self.logout)
        sb_layout.addWidget(btn_logout)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

        # Chọn trang đầu tiên
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
            self.stack.setCurrentIndex(0)

    def _get_pages_for_role(self):
        """Trả về danh sách trang theo vai trò người dùng."""
        pages = []
        role = self.user.position

        # Lễ tân và Quản lý có tab Đặt bàn chuẩn (Booking Workflow)
        if role in ('receptionist', 'manager'):
            pages.append(("Đặt bàn", BookingWidget(self.dao, self.cache, self.user, self.rid)))

        table_map = TableMapWidget(self.dao, self.cache, self.user, self.rid)
        table_map.table_clicked.connect(self._on_table_clicked)

        # Tất cả vai trò đều thấy sơ đồ bàn
        pages.append(("Sơ đồ bàn", table_map))

        if role in ('receptionist', 'manager'):
            pages.append(("Thanh toán", BillingWidget(self.dao, self.cache, self.user, self.rid)))
            if role == 'receptionist':
                pages.append(("Báo cáo", ReportWidget(self.dao, self.cache, self.user, self.rid)))

        if role in ('waiter', 'manager'):
            pages.append(("Gọi món", OrderWidget(self.dao, self.cache, self.user, self.rid)))

        if role in ('chef', 'manager'):
            pages.append(("Bếp", KitchenWidget(self.dao, self.cache, self.user, self.rid)))

        if role == 'manager':
            pages.append(("Quản lý", ManagerWidget(self.dao, self.cache, self.user, self.rid)))

        return pages

    def _switch_page(self, index, btn):
        """Chuyển trang và highlight nút sidebar."""
        self.stack.setCurrentIndex(index)
        for b in self.nav_buttons:
            b.setChecked(False)
        btn.setChecked(True)

    def _on_table_clicked(self, table):
        """Xử lý khi click vào bàn trên sơ đồ."""
        if table.status == 'available':
            # Hiện dialog đặt bàn
            dlg = BookingDialog(table, self.user.user_id, self)
            if dlg.exec():
                booking = dlg.result_booking
                self.dao.create_booking(booking)
                # Cập nhật cache
                self.cache.set_table_status(self.rid, table.table_id, 'reserved')
                self.cache.invalidate_tables(self.rid)
                QMessageBox.information(self, "Thành công", f"Đã đặt bàn {table.table_number} thành công!")
                # Refresh sơ đồ bàn
                for i in range(self.stack.count()):
                    w = self.stack.widget(i)
                    if isinstance(w, TableMapWidget):
                        w.load_tables()
                        break
        elif table.status == 'occupied':
            QMessageBox.information(self, f"Bàn {table.table_number}",
                f"Bàn đang được sử dụng.\nChuyển sang tab Gọi món hoặc Thanh toán để thao tác.")
        elif table.status == 'reserved':
            # Lễ tân hoặc Quản lý có thể mở khóa bàn đã đặt khi khách đến
            if self.user.position in ('receptionist', 'manager'):
                reply = QMessageBox.question(self, f"Bàn {table.table_number} - Đã đặt",
                    f"Bàn {table.table_number} đã được đặt trước.\n\n"
                    f"Khách đã đến? Mở khóa bàn để phục vụ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.dao.update_table_status(table.table_id, 'occupied')
                    self.cache.set_table_status(self.rid, table.table_id, 'occupied')
                    self.cache.invalidate_tables(self.rid)
                    QMessageBox.information(self, "Thành công",
                        f"Đã mở khóa bàn {table.table_number}. Bàn sẵn sàng phục vụ!")
                    for i in range(self.stack.count()):
                        w = self.stack.widget(i)
                        if isinstance(w, TableMapWidget):
                            w.load_tables()
                            break
            else:
                QMessageBox.information(self, f"Bàn {table.table_number}",
                    f"Bàn đã được đặt trước.")

    def logout(self):
        reply = QMessageBox.question(self, "Đăng xuất", "Bạn có muốn đăng xuất?")
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            start_app()


def start_app():
    """Khởi chạy ứng dụng: Login -> MainWindow."""
    dao = DatabaseDAO()
    cache = RedisCache()

    login = LoginWindow(dao)
    login.login_success.connect(lambda user: show_main(user, dao, cache))
    login.show()
    return login

def show_main(user, dao, cache):
    global main_win
    main_win = MainWindow(user, dao, cache)
    main_win.showMaximized()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # Font mặc định
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    # Global stylesheet
    app.setStyleSheet("""
        QWidget{font-family:'Segoe UI'; color: #000000;}
        QMainWindow{background: #f0f2f5;}
        QMessageBox{background:#ffffff;}
        QMessageBox QLabel{color:#000000; background: transparent;}
        QMessageBox QPushButton{background:#e0e0e0;color:#000000;border:none;
            border-radius:6px;padding:8px 20px;font:13px 'Segoe UI';}
        QMessageBox QPushButton:hover{background:#d5d5d5;}
        QToolTip{background:#ffffff;color:#000000;border:1px solid #cccccc;
            padding:4px;font:12px 'Segoe UI';}
        QTabWidget::pane { border: 1px solid #e0e0e0; background: #ffffff; border-radius: 4px; }
        QTabBar::tab { background: #f8f9fa; color: #000000; border: 1px solid #e0e0e0; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
        QTabBar::tab:selected { background: #ffffff; color: #000000; border-bottom-color: #ffffff; font-weight: bold; }
        QTabBar::tab:hover { background: #e9ecef; }
    """)
    global login_win
    login_win = start_app()
    sys.exit(app.exec())
