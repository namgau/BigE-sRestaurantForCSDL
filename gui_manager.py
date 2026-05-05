# gui_manager.py - Quản lý (Thực đơn, Nhân sự, Sơ đồ bàn, Doanh thu)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QTableWidget, QTableWidgetItem, QComboBox, QTabWidget,
                              QLineEdit, QSpinBox, QDoubleSpinBox, QHeaderView,
                              QMessageBox, QDialog, QDateEdit, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush
from models import Category, Dish, User, Table
from datetime import date


class ManagerWidget(QWidget):
    """Widget quản lý dành cho Manager."""
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = restaurant_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("QUẢN LÝ HỆ THỐNG")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000; padding: 8px 0;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #e0e0e0;background:#ffffff;border-radius:8px;}
            QTabBar::tab{background:#f5f5f5;color:#000000;padding:10px 20px;font:13px 'Segoe UI';
                border-top-left-radius:6px;border-top-right-radius:6px;margin-right:2px;
                border:1px solid #e0e0e0; border-bottom:none;}
            QTabBar::tab:selected{background:#ffffff;color:#1976d2;font:bold 13px 'Segoe UI';
                border-top:2px solid #1976d2;}
            QTabBar::tab:hover{background:#e8f0fe;color:#1976d2;}
        """)
        tabs.addTab(self._create_menu_tab(), "Thực đơn")
        tabs.addTab(self._create_staff_tab(), "Nhân sự")
        tabs.addTab(self._create_table_tab(), "Sơ đồ bàn")
        tabs.addTab(ReportWidget(self.dao, self.cache, self.user, self.rid), "Báo cáo thống kê")
        layout.addWidget(tabs)

    # ===================== TAB THỰC ĐƠN =====================
    def _create_menu_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_dish = QTableWidget(0, 6)
        self.tbl_dish.setHorizontalHeaderLabels(["ID", "Tên món", "Danh mục", "Giá", "Trạng thái", "Thao tác"])
        self.tbl_dish.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_dish.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_dish.setColumnWidth(5, 230)
        self._style_table(self.tbl_dish)
        layout.addWidget(self.tbl_dish)

        form = QHBoxLayout()
        self.txt_dish_name = QLineEdit(); self.txt_dish_name.setPlaceholderText("Tên món")
        self.txt_dish_name.setStyleSheet(self._input_style())
        self.cmb_dish_cat = QComboBox(); self.cmb_dish_cat.setStyleSheet(self._input_style())
        self.spn_price = QDoubleSpinBox(); self.spn_price.setRange(0, 99999999)
        self.spn_price.setPrefix(""); self.spn_price.setSuffix(" đ")
        self.spn_price.setStyleSheet(self._input_style())
        form.addWidget(self.txt_dish_name)
        form.addWidget(self.cmb_dish_cat)
        form.addWidget(self.spn_price)

        btn_add = QPushButton("Thêm")
        btn_add.setStyleSheet(self._btn_style("#4caf50"))
        btn_add.clicked.connect(self.add_dish)
        form.addWidget(btn_add)

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.setStyleSheet(self._btn_style("#2196f3"))
        btn_refresh.clicked.connect(self.load_dishes)
        form.addWidget(btn_refresh)
        layout.addLayout(form)

        self.load_dish_categories()
        self.load_dishes()
        return w

    def load_dish_categories(self):
        cats = self.dao.get_all_categories(self.rid)
        self.cmb_dish_cat.clear()
        for c in cats:
            self.cmb_dish_cat.addItem(c.name, c.category_id)

    def load_dishes(self):
        dishes = self.dao.get_all_dishes(self.rid)
        self.tbl_dish.setRowCount(len(dishes))
        for i, d in enumerate(dishes):
            self.tbl_dish.setItem(i, 0, self._read_only_item(str(d.dish_id)))
            self.tbl_dish.setItem(i, 1, self._read_only_item(d.name))
            self.tbl_dish.setItem(i, 2, self._read_only_item(d.category_name))
            self.tbl_dish.setItem(i, 3, self._read_only_item(f"{d.price:,.0f}đ"))

            status_txt = "Đang bán" if d.is_available else "Ngừng bán"
            item_st = self._read_only_item(status_txt)
            if d.is_available:
                item_st.setForeground(QBrush(QColor("#2e7d32")))
            else:
                item_st.setForeground(QBrush(QColor("#c62828")))
            self.tbl_dish.setItem(i, 4, item_st)

            # Nút thao tác
            actions = QWidget()
            al = QHBoxLayout(actions); al.setContentsMargins(2,2,2,2); al.setSpacing(4)
            
            btn_edit = QPushButton("Sửa")
            btn_edit.setStyleSheet(self._small_btn("#2196f3"))
            btn_edit.clicked.connect(lambda _, dish=d: self.edit_dish(dish))
            al.addWidget(btn_edit)
            
            toggle_text = "Ngừng bán" if d.is_available else "Mở bán"
            btn_toggle = QPushButton(toggle_text)
            btn_toggle.setStyleSheet(self._small_btn("#ff9800"))
            btn_toggle.clicked.connect(lambda _, dish=d: self.toggle_dish_status(dish))
            al.addWidget(btn_toggle)
            btn_del = QPushButton("Xóa")
            btn_del.setStyleSheet(self._small_btn("#f44336"))
            btn_del.clicked.connect(lambda _, dish=d: self.delete_dish(dish))
            al.addWidget(btn_del)
            self.tbl_dish.setCellWidget(i, 5, actions)

    def add_dish(self):
        name = self.txt_dish_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Nhập tên món!"); return
        dish = Dish(category_id=self.cmb_dish_cat.currentData(), name=name,
                    price=self.spn_price.value())
        self.dao.add_dish(dish)
        self.txt_dish_name.clear(); self.spn_price.setValue(0)
        self.load_dishes()

    def edit_dish(self, dish):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Chỉnh sửa món ăn")
        dlg.setFixedSize(320, 200)
        layout = QFormLayout(dlg)
        
        txt_name = QLineEdit(dish.name)
        txt_name.setStyleSheet(self._input_style())
        
        cmb_cat = QComboBox()
        cmb_cat.setStyleSheet(self._input_style())
        cats = self.dao.get_all_categories(self.rid)
        for c in cats:
            cmb_cat.addItem(c.name, c.category_id)
        idx = cmb_cat.findData(dish.category_id)
        if idx >= 0: cmb_cat.setCurrentIndex(idx)
            
        spn_price = QDoubleSpinBox()
        spn_price.setRange(0, 99999999)
        spn_price.setValue(dish.price)
        spn_price.setStyleSheet(self._input_style())
        
        layout.addRow("Tên món:", txt_name)
        layout.addRow("Danh mục:", cmb_cat)
        layout.addRow("Giá (đ):", spn_price)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        
        # Style các nút chuẩn của QDialogButtonBox
        btn_box.button(QDialogButtonBox.StandardButton.Save).setStyleSheet("background:#4caf50;color:#fff;padding:6px 16px;border-radius:4px;")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#f44336;color:#fff;padding:6px 16px;border-radius:4px;")
        
        layout.addWidget(btn_box)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_name = txt_name.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Lỗi", "Tên món không được để trống!")
                return
            dish.name = new_name
            dish.category_id = cmb_cat.currentData()
            dish.price = spn_price.value()
            try:
                self.dao.update_dish(dish)
                self.load_dishes()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật món ăn: {e}")

    def toggle_dish_status(self, dish):
        new_status = not dish.is_available
        dish.is_available = new_status
        self.dao.update_dish(dish)
        self.load_dishes()

    def delete_dish(self, dish):
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa món '{dish.name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dao.delete_dish(dish.dish_id)
                self.load_dishes()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")

    # ===================== TAB NHÂN SỰ =====================
    def _create_staff_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_staff = QTableWidget(0, 6)
        self.tbl_staff.setHorizontalHeaderLabels(["ID", "Họ tên", "Username", "Vai trò", "SĐT", "Thao tác"])
        self.tbl_staff.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_staff.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_staff.setColumnWidth(5, 140)
        self._style_table(self.tbl_staff)
        layout.addWidget(self.tbl_staff)

        form = QHBoxLayout()
        self.txt_staff_name = QLineEdit(); self.txt_staff_name.setPlaceholderText("Họ tên")
        self.txt_staff_name.setStyleSheet(self._input_style())
        self.txt_staff_user = QLineEdit(); self.txt_staff_user.setPlaceholderText("Username")
        self.txt_staff_user.setStyleSheet(self._input_style())
        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["manager","receptionist","waiter","chef"])
        self.cmb_role.setStyleSheet(self._input_style())
        self.txt_staff_phone = QLineEdit(); self.txt_staff_phone.setPlaceholderText("SĐT")
        self.txt_staff_phone.setStyleSheet(self._input_style())
        form.addWidget(self.txt_staff_name)
        form.addWidget(self.txt_staff_user)
        form.addWidget(self.cmb_role)
        form.addWidget(self.txt_staff_phone)

        btn_add = QPushButton("Thêm")
        btn_add.setStyleSheet(self._btn_style("#4caf50"))
        btn_add.clicked.connect(self.add_staff)
        form.addWidget(btn_add)

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.setStyleSheet(self._btn_style("#2196f3"))
        btn_refresh.clicked.connect(self.load_staff)
        form.addWidget(btn_refresh)
        layout.addLayout(form)
        self.load_staff()
        return w

    def load_staff(self):
        users = self.dao.get_all_users(self.rid)
        self.tbl_staff.setRowCount(len(users))
        role_vn = {'manager':'Quản lý','receptionist':'Lễ tân','waiter':'Phục vụ','chef':'Bếp'}
        for i, u in enumerate(users):
            self.tbl_staff.setItem(i, 0, self._read_only_item(str(u.user_id)))
            self.tbl_staff.setItem(i, 1, self._read_only_item(u.full_name))
            self.tbl_staff.setItem(i, 2, self._read_only_item(u.username))
            self.tbl_staff.setItem(i, 3, self._read_only_item(role_vn.get(u.role, u.role)))
            self.tbl_staff.setItem(i, 4, self._read_only_item(u.phone))

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(2, 2, 2, 2)
            al.setSpacing(4)
            
            btn_edit = QPushButton("Sửa")
            btn_edit.setStyleSheet(self._small_btn("#2196f3"))
            btn_edit.clicked.connect(lambda _, user_obj=u: self.edit_staff(user_obj))
            al.addWidget(btn_edit)
            
            btn_del = QPushButton("Xóa")
            btn_del.setStyleSheet(self._small_btn("#f44336"))
            btn_del.clicked.connect(lambda _, user_obj=u: self.delete_staff(user_obj))
            al.addWidget(btn_del)
            
            self.tbl_staff.setCellWidget(i, 5, actions)

    def add_staff(self):
        name = self.txt_staff_name.text().strip()
        uname = self.txt_staff_user.text().strip()
        if not name or not uname:
            QMessageBox.warning(self, "Lỗi", "Nhập đầy đủ thông tin!"); return
        user = User(restaurant_id=self.rid, username=uname, full_name=name,
                    role=self.cmb_role.currentText(), phone=self.txt_staff_phone.text().strip())
        try:
            self.dao.add_user(user)
            self.load_staff()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def edit_staff(self, user):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Chỉnh sửa nhân viên")
        dlg.setFixedSize(320, 250)
        layout = QFormLayout(dlg)
        
        txt_name = QLineEdit(user.full_name)
        txt_name.setStyleSheet(self._input_style())
        
        cmb_role = QComboBox()
        cmb_role.setStyleSheet(self._input_style())
        cmb_role.addItems(["manager","receptionist","waiter","chef"])
        cmb_role.setCurrentText(user.role)
        
        txt_phone = QLineEdit(user.phone or "")
        txt_phone.setStyleSheet(self._input_style())
        
        layout.addRow("Username:", QLabel(user.username))
        layout.addRow("Họ tên:", txt_name)
        layout.addRow("Vai trò:", cmb_role)
        layout.addRow("SĐT:", txt_phone)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        
        btn_box.button(QDialogButtonBox.StandardButton.Save).setStyleSheet("background:#4caf50;color:#fff;padding:6px 16px;border-radius:4px;")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("background:#f44336;color:#fff;padding:6px 16px;border-radius:4px;")
        
        layout.addWidget(btn_box)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_name = txt_name.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Lỗi", "Họ tên không được để trống!")
                return
            user.full_name = new_name
            user.role = cmb_role.currentText()
            user.phone = txt_phone.text().strip()
            try:
                self.dao.update_user(user)
                self.load_staff()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")

    def delete_staff(self, user):
        if user.user_id == self.user.user_id:
            QMessageBox.warning(self, "Lỗi", "Không thể xóa chính mình!"); return
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa nhân viên '{user.full_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dao.delete_user(user.user_id)
                self.load_staff()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")

    # ===================== TAB SƠ ĐỒ BÀN =====================
    def _create_table_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_tables = QTableWidget(0, 6)
        self.tbl_tables.setHorizontalHeaderLabels(["ID", "Số bàn", "Sức chứa", "Khu vực", "Trạng thái", "Thao tác"])
        self.tbl_tables.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_tables.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tbl_tables.setColumnWidth(5, 220)
        self._style_table(self.tbl_tables)
        layout.addWidget(self.tbl_tables)

        form = QHBoxLayout()
        self.spn_tbl_num = QSpinBox(); self.spn_tbl_num.setRange(1, 999)
        self.spn_tbl_num.setPrefix("Bàn "); self.spn_tbl_num.setStyleSheet(self._input_style())
        self.spn_tbl_cap = QSpinBox(); self.spn_tbl_cap.setRange(1, 50); self.spn_tbl_cap.setValue(4)
        self.spn_tbl_cap.setSuffix(" chỗ"); self.spn_tbl_cap.setStyleSheet(self._input_style())
        self.txt_tbl_area = QLineEdit(); self.txt_tbl_area.setPlaceholderText("Khu vực")
        self.txt_tbl_area.setStyleSheet(self._input_style())
        form.addWidget(self.spn_tbl_num)
        form.addWidget(self.spn_tbl_cap)
        form.addWidget(self.txt_tbl_area)

        btn_add = QPushButton("Thêm bàn")
        btn_add.setStyleSheet(self._btn_style("#4caf50"))
        btn_add.clicked.connect(self.add_table)
        form.addWidget(btn_add)

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.setStyleSheet(self._btn_style("#2196f3"))
        btn_refresh.clicked.connect(self.load_tables_mgmt)
        form.addWidget(btn_refresh)
        layout.addLayout(form)
        self.load_tables_mgmt()
        return w

    def load_tables_mgmt(self):
        tables = self.dao.get_all_tables(self.rid)
        self.tbl_tables.setRowCount(len(tables))
        status_vn = {'available':'Trống','occupied':'Đang dùng','reserved':'Đã đặt','maintenance':'Bảo trì'}
        status_colors = {'available':'#2e7d32','occupied':'#e65100','reserved':'#f9a825','maintenance':'#757575'}
        for i, t in enumerate(tables):
            self.tbl_tables.setItem(i, 0, self._read_only_item(str(t.table_id)))
            self.tbl_tables.setItem(i, 1, self._read_only_item(str(t.table_number)))
            self.tbl_tables.setItem(i, 2, self._read_only_item(str(t.capacity)))
            self.tbl_tables.setItem(i, 3, self._read_only_item(t.area))
            item_st = self._read_only_item(status_vn.get(t.status, t.status))
            color = status_colors.get(t.status, '#000000')
            item_st.setForeground(QBrush(QColor(color)))
            self.tbl_tables.setItem(i, 4, item_st)

            actions = QWidget()
            al = QHBoxLayout(actions); al.setContentsMargins(2,2,2,2); al.setSpacing(4)

            # Nút đổi trạng thái
            cmb = QComboBox()
            cmb.addItems(["Trống", "Đang dùng", "Đã đặt", "Bảo trì"])
            map_vn = {'available':0,'occupied':1,'reserved':2,'maintenance':3}
            cmb.setCurrentIndex(map_vn.get(t.status, 0))
            cmb.setStyleSheet("padding:3px;font:11px 'Segoe UI';border:1px solid #ccc;border-radius:3px;color:#000000;")
            cmb.currentIndexChanged.connect(lambda idx, tbl=t: self._change_table_status(tbl, idx))
            al.addWidget(cmb)

            # Nút khóa bàn (đặt maintenance)
            btn_lock = QPushButton("Khóa")
            btn_lock.setStyleSheet(self._small_btn("#757575"))
            btn_lock.clicked.connect(lambda _, tbl=t: self._lock_table(tbl))
            al.addWidget(btn_lock)

            self.tbl_tables.setCellWidget(i, 5, actions)

    def _change_table_status(self, table, idx):
        map_status = {0:'available',1:'occupied',2:'reserved',3:'maintenance'}
        new_status = map_status.get(idx, 'available')
        try:
            self.dao.update_table_status(table.table_id, new_status)
            self.cache.set_table_status(self.rid, table.table_id, new_status)
            self.cache.invalidate_tables(self.rid)
            self.load_tables_mgmt()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def _lock_table(self, table):
        reply = QMessageBox.question(self, "Xác nhận", f"Khóa bàn {table.table_number} (Bảo trì)?")
        if reply == QMessageBox.StandardButton.Yes:
            self.dao.update_table_status(table.table_id, 'maintenance')
            self.cache.set_table_status(self.rid, table.table_id, 'maintenance')
            self.cache.invalidate_tables(self.rid)
            self.load_tables_mgmt()

    def add_table(self):
        tbl = Table(restaurant_id=self.rid, table_number=self.spn_tbl_num.value(),
                    capacity=self.spn_tbl_cap.value(), area=self.txt_tbl_area.text().strip() or "Tầng 1")
        try:
            self.dao.add_table(tbl)
            self.cache.invalidate_tables(self.rid)
            self.load_tables_mgmt()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    # ===================== HELPERS =====================
    def _style_table(self, tbl):
        tbl.setStyleSheet("""
            QTableWidget {
                background: #ffffff; color: #000000; gridline-color: #e8e8e8;
                font: 13px 'Segoe UI'; border: 1px solid #e0e0e0; border-radius: 4px;
                selection-background-color: #e3f2fd; selection-color: #000000;
                alternate-background-color: #f5f6fa;
            }
            QTableWidget::item { padding: 4px 8px; color: #000000; }
            QHeaderView::section {
                background: #f8f9fa; color: #000000; font: bold 13px 'Segoe UI';
                padding: 8px 6px; border: none; border-bottom: 2px solid #e0e0e0;
            }
        """)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setDefaultSectionSize(36)

    def _read_only_item(self, text):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _input_style(self):
        return "padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#fff;"

    def _btn_style(self, color):
        return f"QPushButton{{background:{color};color:#fff;border:none;border-radius:6px;padding:8px 16px;font:bold 13px 'Segoe UI';}}" \
               f"QPushButton:hover{{opacity:0.85;}}"

    def _small_btn(self, color):
        return f"QPushButton{{background:{color};color:#fff;border:none;border-radius:4px;padding:4px 8px;font:11px 'Segoe UI';}}" \
               f"QPushButton:hover{{opacity:0.85;}}"

class ReportWidget(QWidget):
    """Widget Báo cáo Thống kê độc lập cho Quản lý và Lễ tân/Thu ngân."""
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = restaurant_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("BÁO CÁO THỐNG KÊ")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000; padding: 8px 0;")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.addWidget(QLabel("Loại báo cáo:", styleSheet="color:#000000;font:13px 'Segoe UI';"))
        self.cmb_stat_type = QComboBox()
        self.cmb_stat_type.addItems([
            "Doanh thu theo bàn",
            "Món ăn bán chạy",
            "Chi tiêu khách hàng",
            "Lượt khách trong ngày"
        ])
        self.cmb_stat_type.setStyleSheet(self._input_style())
        row.addWidget(self.cmb_stat_type)

        row.addWidget(QLabel("Từ ngày:", styleSheet="color:#000000;font:13px 'Segoe UI';"))
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(self._input_style())
        row.addWidget(self.date_from)
        row.addWidget(QLabel("Đến ngày:", styleSheet="color:#000000;font:13px 'Segoe UI';"))
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(self._input_style())
        row.addWidget(self.date_to)
        btn = QPushButton("Xem báo cáo")
        btn.setStyleSheet(self._btn_style("#9c27b0"))
        btn.clicked.connect(self.load_report)
        row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

        self.tbl_revenue = QTableWidget(0, 3)
        self.tbl_revenue.setHorizontalHeaderLabels(["Ngày", "Số hóa đơn", "Doanh thu"])
        self.tbl_revenue.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._style_table(self.tbl_revenue)
        layout.addWidget(self.tbl_revenue)

        self.lbl_rev_total = QLabel("Tổng doanh thu: 0 đ")
        self.lbl_rev_total.setStyleSheet("color:#d32f2f;font:bold 18px 'Segoe UI';")
        layout.addWidget(self.lbl_rev_total)

    def load_report(self):
        from dataclasses import asdict
        from models import TableStat, DishStat, ClientStat, HourlyStat
        
        stat_type_idx = self.cmb_stat_type.currentIndex()
        stat_types = ["table_revenue", "best_sellers", "client_spending", "hourly_stats"]
        stat_type = stat_types[stat_type_idx]
        
        qd_from = self.date_from.date()
        qd_to = self.date_to.date()
        d_from = date(qd_from.year(), qd_from.month(), qd_from.day())
        d_to = date(qd_to.year(), qd_to.month(), qd_to.day())
        
        params = {"from": str(d_from), "to": str(d_to)}
        if d_from > d_to:
            QMessageBox.warning(self, "Lỗi", "Khoảng thời gian không hợp lệ!")
            return

        self.tbl_revenue.clear()
        self.tbl_revenue.setRowCount(0)

        # Thử lấy từ cache
        cached_data = self.cache.get_report_stats(self.rid, stat_type, params)
        stats = []
        
        if cached_data:
            if stat_type_idx == 0: stats = [TableStat(**d) for d in cached_data]
            elif stat_type_idx == 1: stats = [DishStat(**d) for d in cached_data]
            elif stat_type_idx == 2: stats = [ClientStat(**d) for d in cached_data]
            elif stat_type_idx == 3: stats = [HourlyStat(**d) for d in cached_data]
        else:
            if stat_type_idx == 0: stats = self.dao.get_table_revenue_stats(self.rid, d_from, d_to)
            elif stat_type_idx == 1: stats = self.dao.get_best_sellers_stats(self.rid, d_from, d_to)
            elif stat_type_idx == 2: stats = self.dao.get_client_spending_stats(d_from, d_to)
            elif stat_type_idx == 3: stats = self.dao.get_hourly_customer_stats(self.rid, d_from)
            if stats:
                self.cache.set_report_stats(self.rid, stat_type, params, [asdict(s) for s in stats])

        grand_total = 0
        if stat_type_idx == 0:
            self.tbl_revenue.setColumnCount(4)
            self.tbl_revenue.setHorizontalHeaderLabels(["Bàn", "Khu vực", "Tổng lượt khách", "Tổng doanh thu"])
            self.tbl_revenue.setRowCount(len(stats))
            for i, s in enumerate(stats):
                self.tbl_revenue.setItem(i, 0, self._read_only_item(str(s.table_number)))
                self.tbl_revenue.setItem(i, 1, self._read_only_item(s.area))
                self.tbl_revenue.setItem(i, 2, self._read_only_item(str(s.total_guests)))
                self.tbl_revenue.setItem(i, 3, self._read_only_item(f"{s.total_revenue:,.0f}đ"))
                grand_total += s.total_revenue
            self.lbl_rev_total.setText(f"Tổng doanh thu: {grand_total:,.0f} đ")
        elif stat_type_idx == 1:
            self.tbl_revenue.setColumnCount(4)
            self.tbl_revenue.setHorizontalHeaderLabels(["Tên món", "Danh mục", "Số lượng bán", "Doanh thu đóng góp"])
            self.tbl_revenue.setRowCount(len(stats))
            for i, s in enumerate(stats):
                self.tbl_revenue.setItem(i, 0, self._read_only_item(s.dish_name))
                self.tbl_revenue.setItem(i, 1, self._read_only_item(s.category_name))
                self.tbl_revenue.setItem(i, 2, self._read_only_item(str(s.quantity_sold)))
                self.tbl_revenue.setItem(i, 3, self._read_only_item(f"{s.revenue_contribution:,.0f}đ"))
                grand_total += s.revenue_contribution
            self.lbl_rev_total.setText(f"Tổng doanh thu từ món: {grand_total:,.0f} đ")
        elif stat_type_idx == 2:
            self.tbl_revenue.setColumnCount(3)
            self.tbl_revenue.setHorizontalHeaderLabels(["Khách hàng", "SĐT", "Tổng chi tiêu"])
            self.tbl_revenue.setRowCount(len(stats))
            for i, s in enumerate(stats):
                self.tbl_revenue.setItem(i, 0, self._read_only_item(s.client_name))
                self.tbl_revenue.setItem(i, 1, self._read_only_item(s.phone))
                self.tbl_revenue.setItem(i, 2, self._read_only_item(f"{s.total_spent:,.0f}đ"))
                grand_total += s.total_spent
            self.lbl_rev_total.setText(f"Tổng doanh thu khách hàng: {grand_total:,.0f} đ")
        elif stat_type_idx == 3:
            self.tbl_revenue.setColumnCount(4)
            self.tbl_revenue.setHorizontalHeaderLabels(["Khung giờ", "Lượt khách", "Số bàn đã dùng", "Doanh thu"])
            self.tbl_revenue.setRowCount(len(stats))
            for i, s in enumerate(stats):
                self.tbl_revenue.setItem(i, 0, self._read_only_item(s.time_frame))
                self.tbl_revenue.setItem(i, 1, self._read_only_item(str(s.guest_count)))
                self.tbl_revenue.setItem(i, 2, self._read_only_item(str(s.table_count)))
                self.tbl_revenue.setItem(i, 3, self._read_only_item(f"{s.revenue:,.0f}đ"))
                grand_total += s.revenue
            self.lbl_rev_total.setText(f"Tổng doanh thu ngày: {grand_total:,.0f} đ")
            
        self.tbl_revenue.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _style_table(self, tbl):
        tbl.setStyleSheet("""
            QTableWidget {
                background: #ffffff; color: #000000; gridline-color: #e8e8e8;
                font: 13px 'Segoe UI'; border: 1px solid #e0e0e0; border-radius: 4px;
                selection-background-color: #e3f2fd; selection-color: #000000;
                alternate-background-color: #f5f6fa;
            }
            QTableWidget::item { padding: 4px 8px; color: #000000; }
            QHeaderView::section {
                background: #f8f9fa; color: #000000; font: bold 13px 'Segoe UI';
                padding: 8px 6px; border: none; border-bottom: 2px solid #e0e0e0;
            }
        """)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setDefaultSectionSize(36)

    def _read_only_item(self, text):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _input_style(self):
        return "padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;color:#000000;background:#fff;"

    def _btn_style(self, color):
        return f"QPushButton{{background:{color};color:#fff;border:none;border-radius:6px;padding:8px 16px;font:bold 13px 'Segoe UI';}}" \
               f"QPushButton:hover{{opacity:0.85;}}"
