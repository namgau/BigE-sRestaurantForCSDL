# gui_kitchen.py - Màn hình Bếp
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor


class KitchenWidget(QWidget):
    """Widget hiển thị hàng đợi chế biến cho bếp."""
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = restaurant_id
        self.queue_items = []
        self.setup_ui()
        self.load_queue()
        # Tự động refresh mỗi 15 giây
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_queue)
        self.timer.start(15000)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = QLabel("BẾP - HÀNG ĐỢI CHẾ BIẾN")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: black;") 
        header.addWidget(title)
        header.addStretch()

        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.setStyleSheet("background:#3498db;color:#fff;border:none;border-radius:6px;"
                                   "padding:8px 16px;font:13px 'Segoe UI';")
        btn_refresh.clicked.connect(self.load_queue)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Bảng hàng đợi
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Bàn", "Món", "SL", "Ghi chú", "Trạng thái", "Thao tác"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget{background:#2c3e50;color:#ecf0f1;gridline-color:#34495e;"
            "font:13px 'Segoe UI';alternate-background-color:#34495e;}"
            "QHeaderView::section{background:#e67e22;color:#fff;font:bold 13px 'Segoe UI';padding:8px;}")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Nút hành động
        btn_row = QHBoxLayout()
        btn_cooking = QPushButton("Bắt đầu chế biến")
        btn_cooking.setStyleSheet("background:#e67e22;color:#fff;border:none;border-radius:8px;"
                                   "padding:10px 24px;font:bold 14px 'Segoe UI';")
        btn_cooking.clicked.connect(lambda: self.update_status('cooking'))
        btn_row.addWidget(btn_cooking)

        btn_done = QPushButton("Hoàn thành")
        btn_done.setStyleSheet("background:#27ae60;color:#fff;border:none;border-radius:8px;"
                                "padding:10px 24px;font:bold 14px 'Segoe UI';")
        btn_done.clicked.connect(lambda: self.update_status('done'))
        btn_row.addWidget(btn_done)

        btn_cancel = QPushButton("Hủy món")
        btn_cancel.setStyleSheet("background:#c0392b;color:#fff;border:none;border-radius:8px;"
                                  "padding:10px 24px;font:bold 14px 'Segoe UI';")
        btn_cancel.clicked.connect(lambda: self.update_status('cancelled'))
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def load_queue(self):
        """
        Tải hàng đợi chế biến.
        Ưu tiên đọc từ Redis cache, nếu miss thì query SQL Server.
        """
        # Thử đọc từ Redis cache trước
        cached = self.cache.get_kitchen_queue(self.rid)
        if cached:
            self.queue_items = cached
            self._fill_table(cached)
            return

        # Cache miss -> query SQL Server
        items = self.dao.get_kitchen_queue(self.rid)
        self.queue_items = items

        # Lưu vào Redis cache cho lần đọc tiếp theo
        cache_data = [{'id': it.ordered_dish_id, 'order_id': it.order_id,
                       'dish_name': it.dish_name, 'quantity': it.quantity,
                       'note': it.note, 'cook_status': it.cook_status,
                       'table_number': it.table_number} for it in items]
        self.cache.set_kitchen_queue(self.rid, cache_data)
        self._fill_table_from_objects(items)

    def _fill_table(self, data_list):
        """Fill bảng từ dữ liệu cache (list of dict)."""
        self.table.setRowCount(len(data_list))
        for i, d in enumerate(data_list):
            status_vn = {'pending': '⏳ Chờ chế biến', 'cooking': '🔥 Đang chế biến'}
            self.table.setItem(i, 0, QTableWidgetItem(f"Bàn {d.get('table_number','')}"))
            self.table.setItem(i, 1, QTableWidgetItem(d.get('dish_name', '')))
            self.table.setItem(i, 2, QTableWidgetItem(str(d.get('quantity', 1))))
            self.table.setItem(i, 3, QTableWidgetItem(d.get('note', '')))
            st = d.get('cook_status', 'pending')
            item = QTableWidgetItem(status_vn.get(st, st))
            if st == 'cooking':
                item.setForeground(QColor('#e67e22'))
            self.table.setItem(i, 4, item)
            self.table.setItem(i, 5, QTableWidgetItem(str(d.get('id', ''))))

    def _fill_table_from_objects(self, items):
        """Fill bảng từ danh sách OrderedDish objects."""
        self.table.setRowCount(len(items))
        status_vn = {'pending': '⏳ Chờ chế biến', 'cooking': '🔥 Đang chế biến'}
        for i, it in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(f"Bàn {it.table_number}"))
            self.table.setItem(i, 1, QTableWidgetItem(it.dish_name))
            self.table.setItem(i, 2, QTableWidgetItem(str(it.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(it.note))
            item = QTableWidgetItem(status_vn.get(it.cook_status, it.cook_status))
            if it.cook_status == 'cooking':
                item.setForeground(QColor('#e67e22'))
            self.table.setItem(i, 4, item)
            self.table.setItem(i, 5, QTableWidgetItem(str(it.ordered_dish_id)))

    def update_status(self, new_status):
        """
        Cập nhật trạng thái chế biến.
        Luồng: pending -> cooking -> done (hoặc cancelled)
        """
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn món cần cập nhật!")
            return
        # Lấy ordered_dish_id từ cột ẩn
        id_item = self.table.item(row, 5)
        if not id_item: return
        od_id = int(id_item.text())

        # Cập nhật SQL Server
        self.dao.update_cook_status(od_id, new_status)
        # Xóa cache bếp để refresh
        self.cache.invalidate_kitchen(self.rid)

        status_vn = {'cooking': 'Đang chế biến', 'done': 'Hoàn thành', 'cancelled': 'Đã hủy'}
        QMessageBox.information(self, "OK", f"Đã cập nhật: {status_vn.get(new_status, new_status)}")
        self.load_queue()
