# gui_order.py - Đặt món mới theo quy trình tuần tự
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QTableWidget, QTableWidgetItem, QSpinBox,
                              QMessageBox, QHeaderView, QStackedWidget, QLineEdit,
                              QScrollArea, QGridLayout, QTabWidget, QComboBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from models import OrderedDish

class SearchTableFrm(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.setup_ui()
        self.load_tables_cinema()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title_row = QHBoxLayout()
        title = QLabel("CHỌN BÀN")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        title_row.addWidget(title)
        
        # Chú thích màu sắc
        legend = QHBoxLayout()
        legend.addWidget(self._create_legend_item("#4caf50", "Trống"))
        legend.addWidget(self._create_legend_item("#fbc02d", "Đang dùng"))
        legend.addWidget(self._create_legend_item("#9e9e9e", "Đã đặt"))
        title_row.addStretch()
        title_row.addLayout(legend)
        layout.addLayout(title_row)

        self.tabs_areas = QTabWidget()
        self.tabs_areas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e0e0e0; background: #fff; border-radius: 8px; }
            QTabBar::tab { background: #f5f5f5; color: #000000; padding: 10px 20px; font: bold 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #2196f3; color: #fff; }
        """)
        layout.addWidget(self.tabs_areas)

    def _create_legend_item(self, color, text):
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(5,0,5,0)
        dot = QFrame()
        dot.setFixedSize(14, 14)
        dot.setStyleSheet(f"background: {color}; border-radius: 7px;")
        l.addWidget(dot)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #000000; font: 12px;")
        l.addWidget(lbl)
        return container

    def load_tables_cinema(self):
        all_tables = self.dao.get_all_tables_cinema(self.rid)
        areas = self.dao.get_all_areas(self.rid)
        
        self.tabs_areas.clear()
        for area in areas:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("background: #fdfdfd; border: none;")
            
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(15)
            grid_layout.setContentsMargins(20, 20, 20, 20)
            
            tables_in_area = [t for t in all_tables if t.area == area]
            row, col = 0, 0
            for t in tables_in_area:
                btn = QPushButton(f"Bàn {t.table_number}\n({t.capacity})")
                btn.setFixedSize(90, 80)
                
                # Màu sắc theo trạng thái
                color = "#4caf50" # available
                if t.status == 'occupied': color = "#fbc02d"
                elif t.status == 'reserved': color = "#9e9e9e"
                
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {color}; color: #fff; border-radius: 8px;
                        font: bold 13px 'Segoe UI'; border: 2px solid rgba(0,0,0,0.1);
                    }}
                    QPushButton:hover {{ border: 2px solid #2196f3; }}
                """)
                
                btn.clicked.connect(lambda checked, table=t: self.actionPerformed_selectTable(table))
                grid_layout.addWidget(btn, row, col)
                col += 1
                if col >= 8: # 8 bàn mỗi hàng
                    col = 0
                    row += 1
            
            grid_layout.setRowStretch(row + 1, 1)
            grid_layout.setColumnStretch(8, 1)
            
            scroll.setWidget(grid_widget)
            self.tabs_areas.addTab(scroll, area)

    def actionPerformed_selectTable(self, table):
        if table.status not in ('available', 'occupied'):
            QMessageBox.warning(self, "Thông báo", f"Bàn {table.table_number} đang {table.status}. Vui lòng chọn bàn trống hoặc bàn đang dùng!")
            return
        search_dish_frm = SearchDishFrm(self.main_stack, self.dao, self.cache, self.user, self.rid, table)
        self.main_stack.addWidget(search_dish_frm)
        self.main_stack.setCurrentWidget(search_dish_frm)

    def showEvent(self, event):
        """Tự động làm mới danh sách bàn mỗi khi trang này được hiển thị"""
        super().showEvent(event)
        self.load_tables_cinema()

class SearchDishFrm(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid, table):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.table = table
        self.temporary_order = []
        self.setup_ui()
        self.load_categories()
        self.load_all_dishes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(f"CHỌN MÓN - Bàn {self.table.table_number}")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        # Thanh lọc
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Loại món:", styleSheet="color:#000; font: 14px;"))
        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumWidth(150)
        self.cmb_cat.setStyleSheet("padding:6px; color:#000; font:14px; border:1px solid #ced4da; border-radius:4px;")
        self.cmb_cat.currentIndexChanged.connect(self.actionPerformed_subSearch)
        filter_row.addWidget(self.cmb_cat)
        
        filter_row.addWidget(QLabel("Tìm tên:", styleSheet="color:#000; font: 14px; margin-left: 20px;"))
        self.txt_key = QLineEdit()
        self.txt_key.setStyleSheet("padding:6px; color:#000; font:14px; border:1px solid #ced4da; border-radius:4px;")
        self.txt_key.textChanged.connect(self.actionPerformed_subSearch)
        filter_row.addWidget(self.txt_key)
        
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.tbl_dishes = QTableWidget(0, 3)
        # Bỏ ID, thêm Loại món
        self.tbl_dishes.setHorizontalHeaderLabels(["Loại món", "Tên món", "Giá"])
        self.tbl_dishes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_dishes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_dishes.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_dishes.setStyleSheet("QTableWidget{background:#ffffff;color:#000;gridline-color:#e0e0e0;}"
                                      "QHeaderView::section{background:#f5f5f5;color:#000;font:bold 13px;border:none;padding:6px;}")
        layout.addWidget(self.tbl_dishes)

        # Dòng thêm món
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Số lượng:", styleSheet="color:#000; font:14px;"))
        self.spn_qty = QSpinBox(); self.spn_qty.setRange(1, 99); self.spn_qty.setValue(1)
        self.spn_qty.setStyleSheet("padding:8px; color:#000; font:14px; border:1px solid #ced4da; border-radius:4px;")
        add_row.addWidget(self.spn_qty)
        
        self.txt_note = QLineEdit(); self.txt_note.setPlaceholderText("Ghi chú món ăn...")
        self.txt_note.setStyleSheet("padding:8px; color:#000; font:14px; border:1px solid #ced4da; border-radius:4px;")
        add_row.addWidget(self.txt_note)

        btn_add = QPushButton("Thêm vào list")
        btn_add.setStyleSheet("""
            QPushButton {
                background: #ff9800; color: #fff; padding: 8px 24px; 
                border-radius: 6px; font: bold 14px; border: none;
            }
            QPushButton:hover { background: #f57c00; }
        """)
        btn_add.clicked.connect(self.actionPerformed_subAddDish)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        btn_view_order = QPushButton("Xem Order & Xác nhận")
        btn_view_order.setStyleSheet("""
            QPushButton {
                background: #4caf50; color: #fff; padding: 12px; 
                border-radius: 6px; font: bold 16px; border: none;
            }
            QPushButton:hover { background: #43a047; }
        """)
        btn_view_order.clicked.connect(self.actionPerformed_subViewOrder)
        layout.addWidget(btn_view_order)
        
        btn_back = QPushButton("Quay lại")
        btn_back.setStyleSheet("""
            QPushButton {
                padding: 10px; border-radius: 6px; background: #e0e0e0;
                color: #000; font: bold 14px; border: none;
            }
            QPushButton:hover { background: #d5d5d5; }
        """)
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))
        layout.addWidget(btn_back)

    def load_categories(self):
        cats = self.dao.get_all_categories(self.rid)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("--- Tất cả ---", None)
        for cat in cats:
            self.cmb_cat.addItem(cat.name, cat.category_id)

    def load_all_dishes(self):
        self.actionPerformed_subSearch()

    def actionPerformed_subSearch(self):
        key = self.txt_key.text().strip()
        cat_id = self.cmb_cat.currentData()
        self.current_dishes = self.dao.search_dish(self.rid, key, cat_id)
        self.display_dishes()

    def display_dishes(self):
        self.tbl_dishes.setRowCount(len(self.current_dishes))
        for i, d in enumerate(self.current_dishes):
            item_cat = QTableWidgetItem(d.category_name)
            item_cat.setFlags(item_cat.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_cat.setForeground(Qt.GlobalColor.darkGray)
            self.tbl_dishes.setItem(i, 0, item_cat)
            
            item_name = QTableWidgetItem(d.name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_dishes.setItem(i, 1, item_name)
            
            item_price = QTableWidgetItem(f"{d.price:,.0f}đ")
            item_price.setFlags(item_price.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_dishes.setItem(i, 2, item_price)

    def actionPerformed_subAddDish(self):
        row = self.tbl_dishes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn món!")
            return
        dish = self.current_dishes[row]
        qty = self.spn_qty.value()
        note = self.txt_note.text().strip()
        
        od = OrderedDish(dish_id=dish.dish_id, quantity=qty, unit_price=dish.price, note=note, dish_name=dish.name)
        self.temporary_order.append(od)
        QMessageBox.information(self, "Thành công", f"Đã thêm {qty} x {dish.name} vào list!")
        
        self.spn_qty.setValue(1)
        self.txt_note.clear()

    def actionPerformed_subViewOrder(self):
        if not self.temporary_order:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn món nào!")
            return
        confirm_frm = ConfirmOrderFrm(self.main_stack, self.dao, self.cache, self.user, self.rid, self.table, self.temporary_order)
        self.main_stack.addWidget(confirm_frm)
        self.main_stack.setCurrentWidget(confirm_frm)

class ConfirmOrderFrm(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid, table, temporary_order):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.table = table
        self.temporary_order = temporary_order
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(f"XÁC NHẬN ĐƠN HÀNG - Bàn {self.table.table_number}")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        self.tbl_order = QTableWidget(0, 5)
        self.tbl_order.setHorizontalHeaderLabels(["Tên món", "SL", "Đơn giá", "Ghi chú", "Thao tác"])
        header = self.tbl_order.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tbl_order.setColumnWidth(4, 80)
        self.tbl_order.setStyleSheet("QTableWidget{background:#ffffff;color:#000;gridline-color:#e0e0e0;}"
                                      "QHeaderView::section{background:#f5f5f5;color:#000;font:bold 13px;border:none;padding:6px;}")
        
        self.tbl_order.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.tbl_order)

        self.lbl_total = QLabel("Tổng tiền tạm tính: 0 đ")
        self.lbl_total.setStyleSheet("color:#d32f2f;font:bold 18px;")
        layout.addWidget(self.lbl_total)

        btn_confirm = QPushButton("XÁC NHẬN VÀ GỬI ĐẾN BẾP")
        btn_confirm.setStyleSheet("""
            QPushButton {
                background: #4caf50; color: #fff; padding: 12px; 
                border-radius: 6px; font: bold 16px; border: none;
            }
            QPushButton:hover { background: #43a047; }
        """)
        btn_confirm.clicked.connect(self.actionPerformed_subConfirm)
        layout.addWidget(btn_confirm)
        
        btn_back = QPushButton("Quay lại")
        btn_back.setStyleSheet("""
            QPushButton {
                padding: 10px; border-radius: 6px; background: #e0e0e0;
                color: #000; font: bold 14px; border: none;
            }
            QPushButton:hover { background: #d5d5d5; }
        """)
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(self.main_stack.currentIndex()-1))
        layout.addWidget(btn_back)

        self.display_order()

    def display_order(self):
        self.tbl_order.blockSignals(True)
        self.tbl_order.setRowCount(len(self.temporary_order))
        total = 0
        for i, od in enumerate(self.temporary_order):
            item_name = QTableWidgetItem(od.dish_name)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_order.setItem(i, 0, item_name)
            
            item_qty = QTableWidgetItem(str(od.quantity))
            self.tbl_order.setItem(i, 1, item_qty)
            
            item_price = QTableWidgetItem(f"{od.unit_price:,.0f}đ")
            item_price.setFlags(item_price.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_order.setItem(i, 2, item_price)
            
            item_note = QTableWidgetItem(od.note)
            self.tbl_order.setItem(i, 3, item_note)
            
            btn_del = QPushButton("Xóa")
            btn_del.setStyleSheet("background:#f44336;color:#fff;border-radius:4px;padding:4px;")
            btn_del.clicked.connect(lambda checked, idx=i: self.delete_item(idx))
            self.tbl_order.setCellWidget(i, 4, btn_del)
            
            total += od.quantity * od.unit_price
            
        self.lbl_total.setText(f"Tổng tiền tạm tính: {total:,.0f} đ")
        self.tbl_order.blockSignals(False)

    def on_item_changed(self, item):
        row = item.row()
        col = item.column()
        if row < len(self.temporary_order):
            od = self.temporary_order[row]
            if col == 1: # qty
                try:
                    qty = int(item.text())
                    if qty > 0:
                        od.quantity = qty
                    else:
                        item.setText(str(od.quantity))
                except ValueError:
                    item.setText(str(od.quantity))
            elif col == 3: # note
                od.note = item.text()
            
            self.update_total()

    def update_total(self):
        total = sum(od.quantity * od.unit_price for od in self.temporary_order)
        self.lbl_total.setText(f"Tổng tiền tạm tính: {total:,.0f} đ")

    def delete_item(self, idx):
        if 0 <= idx < len(self.temporary_order):
            del self.temporary_order[idx]
            self.display_order()

    def actionPerformed_subConfirm(self):
        if not self.temporary_order:
            QMessageBox.warning(self, "Lỗi", "Không có món nào để xác nhận!")
            return
            
        try:
            self.dao.add_order_full(self.table.table_id, self.user.user_id, self.temporary_order)
            self.cache.set_table_status(self.rid, self.table.table_id, 'occupied')
            self.cache.invalidate_tables(self.rid)
            self.cache.invalidate_kitchen(self.rid)
            
            QMessageBox.information(self, "Thành công", "Đặt món thành công! Đơn hàng đã được chuyển đến bếp.")
            while self.main_stack.count() > 1:
                widget = self.main_stack.widget(1)
                self.main_stack.removeWidget(widget)
                widget.deleteLater()
            self.main_stack.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu đơn hàng: {e}")

class OrderWidget(QStackedWidget):
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        # Bỏ qua WaiterHomeFrm, vào thẳng SearchTableFrm
        home = SearchTableFrm(self, dao, cache, user, restaurant_id)
        self.addWidget(home)
