# gui_booking.py - Quản lý đặt bàn chuẩn quy trình (Booking Workflow)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
                              QLineEdit, QDateEdit, QTimeEdit, QSpinBox, QMessageBox, QTextEdit,
                              QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QColor, QBrush
from models import Booking, Client
from datetime import date, time

class ReceptionistHomeView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("QUẢN LÝ ĐẶT BÀN")
        lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        lbl.setStyleSheet("color:#000000;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        buttons_layout = QHBoxLayout()
        btn_booking = QPushButton("ĐẶT BÀN MỚI")
        btn_booking.setStyleSheet("""
            QPushButton { background: #4caf50; color: #fff; border-radius: 12px; padding: 20px 40px; font: bold 18px 'Segoe UI'; }
            QPushButton:hover { background: #43a047; }
        """)
        btn_booking.clicked.connect(self.actionPerformed_subBooking)
        
        btn_manage = QPushButton("QUẢN LÝ LỊCH ĐẶT")
        btn_manage.setStyleSheet("""
            QPushButton { background: #2196f3; color: #fff; border-radius: 12px; padding: 20px 40px; font: bold 18px 'Segoe UI'; }
            QPushButton:hover { background: #1976d2; }
        """)
        btn_manage.clicked.connect(self.actionPerformed_subManageBooking)
        
        buttons_layout.addWidget(btn_booking)
        buttons_layout.addWidget(btn_manage)
        layout.addLayout(buttons_layout)

    def actionPerformed_subBooking(self):
        view = SearchFreeTableView(self.main_stack, self.dao, self.cache, self.user, self.rid)
        self.main_stack.addWidget(view)
        self.main_stack.setCurrentWidget(view)

    def actionPerformed_subManageBooking(self):
        view = ManageBookingView(self.main_stack, self.dao, self.cache, self.user, self.rid)
        self.main_stack.addWidget(view)
        self.main_stack.setCurrentWidget(view)


class SearchFreeTableView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.free_tables = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("TÌM BÀN TRỐNG")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        # Input Row
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Ngày:", styleSheet="color:#000000;font:14px;"))
        self.inDate = QDateEdit(QDate.currentDate())
        self.inDate.setCalendarPopup(True)
        self.inDate.setStyleSheet("padding:6px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        input_row.addWidget(self.inDate)
        
        input_row.addWidget(QLabel("Giờ:", styleSheet="color:#000000;font:14px;margin-left:15px;"))
        self.inTime = QTimeEdit(QTime.currentTime())
        self.inTime.setStyleSheet("padding:6px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        input_row.addWidget(self.inTime)
        
        input_row.addWidget(QLabel("Số lượng khách:", styleSheet="color:#000000;font:14px;margin-left:15px;"))
        self.inCapacity = QSpinBox()
        self.inCapacity.setRange(1, 100)
        self.inCapacity.setValue(2)
        self.inCapacity.setStyleSheet("padding:6px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        input_row.addWidget(self.inCapacity)
        
        btn_search = QPushButton("Tìm kiếm")
        btn_search.setStyleSheet("background:#ff9800;color:#fff;border-radius:6px;padding:8px 20px;font:bold 14px;")
        btn_search.clicked.connect(self.actionPerformed_subSearch)
        input_row.addWidget(btn_search)
        input_row.addStretch()
        layout.addLayout(input_row)

        # Table Row
        self.outsubListTable = QTableWidget(0, 5)
        self.outsubListTable.setHorizontalHeaderLabels(["ID", "Số bàn", "Sức chứa", "Khu vực", "Thao tác"])
        self.outsubListTable.setColumnHidden(0, True)  # Ẩn cột ID
        self.outsubListTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._style_table(self.outsubListTable)
        layout.addWidget(self.outsubListTable)

        btn_back = QPushButton("Quay lại")
        btn_back.setStyleSheet("padding:10px;border-radius:6px;background:#e0e0e0;color:#000;font:bold 14px;border:none;")
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))
        layout.addWidget(btn_back)
        
        self.actionPerformed_subSearch()

    def actionPerformed_subSearch(self):
        qd = self.inDate.date()
        dt = date(qd.year(), qd.month(), qd.day())
        qt = self.inTime.time()
        # simplified time check: we don't pass time to search_free_tables currently
        cap = self.inCapacity.value()
        
        self.free_tables = self.dao.search_free_tables(self.rid, dt, qt, cap)
        
        self.outsubListTable.setRowCount(len(self.free_tables))
        for i, t in enumerate(self.free_tables):
            self.outsubListTable.setItem(i, 0, self._ro_item(str(t.table_id)))
            self.outsubListTable.setItem(i, 1, self._ro_item(str(t.table_number)))
            self.outsubListTable.setItem(i, 2, self._ro_item(str(t.capacity)))
            self.outsubListTable.setItem(i, 3, self._ro_item(t.area))
            
            btn_select = QPushButton("Chọn bàn")
            btn_select.setStyleSheet("background:#4caf50;color:#fff;border-radius:4px;padding:4px;")
            btn_select.clicked.connect(lambda _, tbl=t: self.select_table(tbl))
            self.outsubListTable.setCellWidget(i, 4, btn_select)

    def select_table(self, table):
        booking_info = {
            'table': table,
            'date': date(self.inDate.date().year(), self.inDate.date().month(), self.inDate.date().day()),
            'time': time(self.inTime.time().hour(), self.inTime.time().minute()),
            'capacity': self.inCapacity.value()
        }
        view = SearchClientView(self.main_stack, self.dao, self.cache, self.user, self.rid, booking_info)
        self.main_stack.addWidget(view)
        self.main_stack.setCurrentWidget(view)

    def _ro_item(self, text):
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return it

    def _style_table(self, tbl):
        tbl.setStyleSheet("""
            QTableWidget { background: #ffffff; color: #000000; gridline-color: #e8e8e8; font: 13px 'Segoe UI'; border: 1px solid #e0e0e0; border-radius: 4px; alternate-background-color: #f5f6fa; }
            QHeaderView::section { background: #f8f9fa; color: #000000; font: bold 13px 'Segoe UI'; padding: 8px 6px; border: none; border-bottom: 2px solid #e0e0e0; }
        """)
        tbl.setAlternatingRowColors(True)


class SearchClientView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid, booking_info):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.booking_info = booking_info
        self.clients = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(f"TÌM KHÁCH HÀNG - Đặt bàn {self.booking_info['table'].table_number}")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        # Search Bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Từ khóa (Tên/SĐT):", styleSheet="color:#000000;font:14px;"))
        self.inKey = QLineEdit()
        self.inKey.setStyleSheet("padding:6px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        search_row.addWidget(self.inKey)
        
        btn_search = QPushButton("Tìm kiếm")
        btn_search.setStyleSheet("background:#2196f3;color:#fff;border-radius:6px;padding:8px 20px;font:bold 14px;")
        btn_search.clicked.connect(self.actionPerformed_subSearch)
        search_row.addWidget(btn_search)
        
        btn_add = QPushButton("+ Thêm Khách mới")
        btn_add.setStyleSheet("background:#4caf50;color:#fff;border-radius:6px;padding:8px 20px;font:bold 14px;")
        btn_add.clicked.connect(self.actionPerformed_subAddClient)
        search_row.addWidget(btn_add)
        layout.addLayout(search_row)

        # Table
        self.outsubListClient = QTableWidget(0, 5)
        self.outsubListClient.setHorizontalHeaderLabels(["ID", "Họ tên", "SĐT", "Email", "Thao tác"])
        self.outsubListClient.setColumnHidden(0, True)  # Ẩn cột ID
        self.outsubListClient.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.outsubListClient.setStyleSheet("""
            QTableWidget { background: #ffffff; color: #000000; gridline-color: #e8e8e8; font: 13px 'Segoe UI'; border: 1px solid #e0e0e0; border-radius: 4px; alternate-background-color: #f5f6fa; }
            QHeaderView::section { background: #f8f9fa; color: #000000; font: bold 13px 'Segoe UI'; padding: 8px 6px; border: none; border-bottom: 2px solid #e0e0e0; }
        """)
        self.outsubListClient.setAlternatingRowColors(True)
        layout.addWidget(self.outsubListClient)

        btn_back = QPushButton("Quay lại")
        btn_back.setStyleSheet("padding:10px;border-radius:6px;background:#e0e0e0;color:#000;font:bold 14px;border:none;")
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(self.main_stack.currentIndex()-1))
        layout.addWidget(btn_back)

    def actionPerformed_subSearch(self):
        key = self.inKey.text().strip()
        self.clients = self.dao.search_clients(key) if key else []
        self.outsubListClient.setRowCount(len(self.clients))
        for i, c in enumerate(self.clients):
            self.outsubListClient.setItem(i, 0, self._ro_item(str(c.client_id)))
            self.outsubListClient.setItem(i, 1, self._ro_item(c.full_name))
            self.outsubListClient.setItem(i, 2, self._ro_item(c.phone))
            self.outsubListClient.setItem(i, 3, self._ro_item(c.email))
            
            btn_select = QPushButton("Chọn khách")
            btn_select.setStyleSheet("background:#4caf50;color:#fff;border-radius:4px;padding:4px;")
            btn_select.clicked.connect(lambda _, client=c: self.select_client(client))
            self.outsubListClient.setCellWidget(i, 4, btn_select)

    def select_client(self, client):
        self.booking_info['client'] = client
        view = BookingConfirmView(self.main_stack, self.dao, self.cache, self.user, self.rid, self.booking_info)
        self.main_stack.addWidget(view)
        self.main_stack.setCurrentWidget(view)

    def actionPerformed_subAddClient(self):
        view = AddClientView(self.main_stack, self.dao, self.cache, self.user, self.rid, self.booking_info)
        self.main_stack.addWidget(view)
        self.main_stack.setCurrentWidget(view)

    def _ro_item(self, text):
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return it


class AddClientView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid, booking_info):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.booking_info = booking_info
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("THÊM KHÁCH HÀNG MỚI")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        grid = QGridLayout()
        self.inFullName = QLineEdit(); self.inFullName.setStyleSheet("padding:8px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        self.inTel = QLineEdit(); self.inTel.setStyleSheet("padding:8px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        self.inEmail = QLineEdit(); self.inEmail.setStyleSheet("padding:8px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        self.inAddress = QLineEdit(); self.inAddress.setStyleSheet("padding:8px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        
        grid.addWidget(QLabel("Họ tên *:", styleSheet="color:#000000;font:14px;"), 0, 0)
        grid.addWidget(self.inFullName, 0, 1)
        grid.addWidget(QLabel("SĐT *:", styleSheet="color:#000000;font:14px;"), 1, 0)
        grid.addWidget(self.inTel, 1, 1)
        grid.addWidget(QLabel("Email:", styleSheet="color:#000000;font:14px;"), 2, 0)
        grid.addWidget(self.inEmail, 2, 1)
        grid.addWidget(QLabel("Địa chỉ:", styleSheet="color:#000000;font:14px;"), 3, 0)
        grid.addWidget(self.inAddress, 3, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

        btns = QHBoxLayout()
        btn_add = QPushButton("Xác nhận & Thêm")
        btn_add.setStyleSheet("background:#4caf50;color:#fff;border-radius:6px;padding:12px;font:bold 14px;")
        btn_add.clicked.connect(self.actionPerformed_subAdd)
        
        btn_back = QPushButton("Hủy")
        btn_back.setStyleSheet("background:#e0e0e0;color:#000;border-radius:6px;padding:12px;font:bold 14px;")
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(self.main_stack.currentIndex()-1))
        
        btns.addWidget(btn_back)
        btns.addWidget(btn_add)
        layout.addLayout(btns)

    def actionPerformed_subAdd(self):
        name = self.inFullName.text().strip()
        tel = self.inTel.text().strip()
        if not name or not tel:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Họ tên và SĐT!")
            return
        
        client = Client(full_name=name, phone=tel, email=self.inEmail.text().strip())
        try:
            client_id = self.dao.add_client(client)
            client.client_id = client_id
            QMessageBox.information(self, "Thành công", "Đã thêm khách hàng!")
            
            # Tự động chọn khách vừa thêm và đi tới xác nhận
            self.booking_info['client'] = client
            view = BookingConfirmView(self.main_stack, self.dao, self.cache, self.user, self.rid, self.booking_info)
            self.main_stack.addWidget(view)
            self.main_stack.setCurrentWidget(view)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))


class BookingConfirmView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid, booking_info):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.booking_info = booking_info
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("XÁC NHẬN PHIẾU ĐẶT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        client = self.booking_info['client']
        table = self.booking_info['table']
        dt_str = self.booking_info['date'].strftime('%d/%m/%Y')
        tm_str = self.booking_info['time'].strftime('%H:%M')
        
        info = f"""
        <div style='font-size:16px; color:#000000; line-height: 1.5;'>
        <b>Khách hàng:</b> {client.full_name} ({client.phone})<br/>
        <b>Bàn chọn:</b> Bàn {table.table_number} - {table.area} (Sức chứa {table.capacity})<br/>
        <b>Thời gian:</b> {tm_str} ngày {dt_str}<br/>
        <b>Số khách:</b> {self.booking_info['capacity']}
        </div>
        """
        self.outoutBookingInfo = QLabel(info)
        layout.addWidget(self.outoutBookingInfo)

        layout.addWidget(QLabel("Ghi chú ca đặt:", styleSheet="color:#000000;font:14px;font-weight:bold;"))
        self.inNote = QTextEdit()
        self.inNote.setMaximumHeight(80)
        self.inNote.setStyleSheet("padding:8px;font:14px;border:1px solid #ced4da;border-radius:4px;")
        layout.addWidget(self.inNote)
        
        layout.addStretch()

        btns = QHBoxLayout()
        btn_confirm = QPushButton("Xác nhận Đặt bàn")
        btn_confirm.setStyleSheet("background:#2ecc71;color:#fff;border-radius:6px;padding:15px;font:bold 16px;")
        btn_confirm.clicked.connect(self.actionPerformed_subConfirm)
        
        btn_back = QPushButton("Hủy")
        btn_back.setStyleSheet("background:#e0e0e0;color:#000;border-radius:6px;padding:15px;font:bold 16px;")
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))
        
        btns.addWidget(btn_back)
        btns.addWidget(btn_confirm)
        layout.addLayout(btns)

    def actionPerformed_subConfirm(self):
        client = self.booking_info['client']
        b = Booking(
            table_id=self.booking_info['table'].table_id,
            client_id=client.client_id,
            user_id=self.user.user_id,
            guest_name=client.full_name,
            guest_phone=client.phone,
            guest_count=self.booking_info['capacity'],
            booking_date=self.booking_info['date'],
            booking_time=self.booking_info['time'],
            note=self.inNote.toPlainText().strip()
        )
        try:
            self.dao.create_booking(b)
            self.cache.set_table_status(self.rid, b.table_id, 'reserved')
            self.cache.invalidate_tables(self.rid)
            QMessageBox.information(self, "Thành công", "Đặt bàn thành công!")
            
            # Về trang chủ Lễ tân và xóa các view thừa
            while self.main_stack.count() > 1:
                w = self.main_stack.widget(1)
                self.main_stack.removeWidget(w)
                w.deleteLater()
            self.main_stack.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu lịch đặt: {e}")


class ManageBookingView(QWidget):
    def __init__(self, main_stack, dao, cache, user, rid):
        super().__init__()
        self.main_stack = main_stack
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = rid
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("QUẢN LÝ LỊCH ĐÃ ĐẶT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        self.outsubListBooking = QTableWidget(0, 9)
        self.outsubListBooking.setHorizontalHeaderLabels(["ID", "Bàn", "Khách hàng", "SĐT", "Ngày", "Giờ", "Người tạo", "Trạng thái", "Thao tác"])
        self.outsubListBooking.setColumnHidden(0, True)  # Ẩn cột ID
        self.outsubListBooking.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.outsubListBooking.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.outsubListBooking.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.outsubListBooking.setColumnWidth(8, 160)
        self.outsubListBooking.setStyleSheet("""
            QTableWidget { background: #ffffff; color: #000000; gridline-color: #e8e8e8; font: 13px 'Segoe UI'; border: 1px solid #e0e0e0; border-radius: 4px; alternate-background-color: #f5f6fa; }
            QHeaderView::section { background: #f8f9fa; color: #000000; font: bold 13px 'Segoe UI'; padding: 8px 6px; border: none; border-bottom: 2px solid #e0e0e0; }
        """)
        self.outsubListBooking.setAlternatingRowColors(True)
        layout.addWidget(self.outsubListBooking)

        btns = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.setStyleSheet("background:#2196f3;color:#fff;border-radius:6px;padding:10px 20px;font:bold 14px;")
        btn_refresh.clicked.connect(self.load_bookings)
        btns.addWidget(btn_refresh)
        btns.addStretch()
        
        btn_back = QPushButton("Quay lại")
        btn_back.setStyleSheet("padding:10px 20px;border-radius:6px;background:#e0e0e0;color:#000;font:bold 14px;border:none;")
        btn_back.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))
        btns.addWidget(btn_back)
        
        layout.addLayout(btns)
        self.load_bookings()

    def load_bookings(self):
        bookings = self.dao.get_all_bookings(self.rid)
        self.outsubListBooking.setRowCount(len(bookings))
        
        status_map = {'confirmed':'Đã xác nhận', 'cancelled':'Đã hủy', 'completed':'Hoàn thành', 'no_show':'Khách không đến'}
        for i, b in enumerate(bookings):
            self.outsubListBooking.setItem(i, 0, self._ro_item(str(b.booking_id)))
            self.outsubListBooking.setItem(i, 1, self._ro_item(f"Bàn {b.table_number}"))
            self.outsubListBooking.setItem(i, 2, self._ro_item(b.guest_name))
            self.outsubListBooking.setItem(i, 3, self._ro_item(b.guest_phone))
            self.outsubListBooking.setItem(i, 4, self._ro_item(b.booking_date.strftime('%d/%m/%Y') if b.booking_date else ''))
            self.outsubListBooking.setItem(i, 5, self._ro_item(b.booking_time.strftime('%H:%M') if b.booking_time else ''))
            self.outsubListBooking.setItem(i, 6, self._ro_item(b.user_name))
            
            st_item = self._ro_item(status_map.get(b.status, b.status))
            if b.status == 'confirmed': st_item.setForeground(QBrush(QColor("#2e7d32")))
            elif b.status == 'cancelled': st_item.setForeground(QBrush(QColor("#c62828")))
            self.outsubListBooking.setItem(i, 7, st_item)
            
            actions = QWidget()
            al = QHBoxLayout(actions); al.setContentsMargins(2,2,2,2); al.setSpacing(4)
            
            if b.status == 'confirmed':
                btn_upd = QPushButton("Đến nơi")
                btn_upd.setStyleSheet("background:#2196f3;color:#fff;border-radius:4px;padding:4px 8px;")
                btn_upd.clicked.connect(lambda _, bk=b: self.actionPerformed_subUpdate(bk))
                al.addWidget(btn_upd)
                
                btn_del = QPushButton("Hủy")
                btn_del.setStyleSheet("background:#f44336;color:#fff;border-radius:4px;padding:4px 8px;")
                btn_del.clicked.connect(lambda _, bk=b: self.actionPerformed_subDelete(bk))
                al.addWidget(btn_del)
            else:
                btn_del_forever = QPushButton("Xóa vĩnh viễn")
                btn_del_forever.setStyleSheet("background:#9e9e9e;color:#fff;border-radius:4px;padding:4px 8px;")
                btn_del_forever.clicked.connect(lambda _, bk=b: self.actionPerformed_subDeleteForever(bk))
                al.addWidget(btn_del_forever)
                
            self.outsubListBooking.setCellWidget(i, 8, actions)

    def actionPerformed_subUpdate(self, booking):
        # Đánh dấu khách đã đến (Chuyển trạng thái booking thành completed, bàn thành occupied)
        reply = QMessageBox.question(self, "Xác nhận", f"Xác nhận khách '{booking.guest_name}' đã đến nhận bàn?")
        if reply == QMessageBox.StandardButton.Yes:
            booking.status = 'completed'
            self.dao.update_booking(booking)
            self.dao.update_table_status(booking.table_id, 'occupied')
            self.cache.set_table_status(self.rid, booking.table_id, 'occupied')
            self.cache.invalidate_tables(self.rid)
            QMessageBox.information(self, "Thành công", "Đã cập nhật trạng thái bàn.")
            self.load_bookings()

    def actionPerformed_subDelete(self, booking):
        reply = QMessageBox.question(self, "Xác nhận hủy", f"Hủy lịch đặt của '{booking.guest_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dao.cancel_booking(booking.booking_id)
                self.cache.set_table_status(self.rid, booking.table_id, 'available')
                self.cache.invalidate_tables(self.rid)
                QMessageBox.information(self, "Thành công", "Hủy đặt bàn thành công.")
                self.load_bookings()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def actionPerformed_subDeleteForever(self, booking):
        reply = QMessageBox.question(self, "Xóa vĩnh viễn", f"Bạn có chắc chắn muốn xóa vĩnh viễn lịch đặt của '{booking.guest_name}' khỏi hệ thống?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dao.delete_booking(booking.booking_id)
                QMessageBox.information(self, "Thành công", "Đã xóa lịch đặt vĩnh viễn.")
                self.load_bookings()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _ro_item(self, text):
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return it

class BookingWidget(QStackedWidget):
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.setStyleSheet("background:#f0f2f5;")
        home = ReceptionistHomeView(self, dao, cache, user, restaurant_id)
        self.addWidget(home)
