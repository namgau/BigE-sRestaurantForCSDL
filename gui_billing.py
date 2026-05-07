# gui_billing.py - Thanh toán hóa đơn
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
                              QHeaderView, QMessageBox, QGroupBox, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from models import Bill
from datetime import date


class BillingWidget(QWidget):
    """Widget thanh toán cho thu ngân / lễ tân."""
    def __init__(self, dao, cache, user, restaurant_id):
        super().__init__()
        self.dao = dao
        self.cache = cache
        self.user = user
        self.rid = restaurant_id
        self.current_bill = None
        self.setup_ui()
        self.load_tables()

    def showEvent(self, event):
        """Auto refresh when tab is shown."""
        super().showEvent(event)
        self.load_tables()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("THANH TOÁN")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#000000;")
        layout.addWidget(title)

        # Chọn bàn cần thanh toán
        top = QHBoxLayout()
        top.addWidget(QLabel("Chọn bàn:", styleSheet="color:#000000;font:13px 'Segoe UI';"))
        self.cmb_table = QComboBox()
        self.cmb_table.setMinimumWidth(200)
        self.cmb_table.setStyleSheet("padding:6px;font:13px 'Segoe UI';border:1px solid #ced4da;border-radius:4px;")
        top.addWidget(self.cmb_table)

        btn_find = QPushButton("Tìm hóa đơn")
        btn_find.setStyleSheet("background:#2196f3;color:#fff;border:none;border-radius:6px;"
                                "padding:8px 16px;font:13px 'Segoe UI';")
        btn_find.clicked.connect(self.find_bill)
        top.addWidget(btn_find)
        top.addStretch()
        layout.addLayout(top)

        content = QHBoxLayout()

        # Bảng chi tiết món
        left = QVBoxLayout()
        left.addWidget(QLabel("Chi tiết hóa đơn", styleSheet="color:#1976d2;font:bold 14px 'Segoe UI';"))
        self.tbl_items = QTableWidget(0, 4)
        self.tbl_items.setHorizontalHeaderLabels(["Món", "SL", "Đơn giá", "Thành tiền"])
        self.tbl_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_items.setStyleSheet(
            "QTableWidget{background:#ffffff;color:#000000;gridline-color:#e0e0e0;font:13px 'Segoe UI';border:1px solid #e0e0e0;border-radius:4px;}"
            "QHeaderView::section{background:#f5f5f5;color:#000000;font:bold 13px 'Segoe UI';padding:6px;border:none;}")
        left.addWidget(self.tbl_items)
        content.addLayout(left, 3)

        # Panel tính tiền
        right = QVBoxLayout()
        box = QGroupBox("Thanh toán")
        box.setStyleSheet("QGroupBox{color:#000000;font:bold 14px 'Segoe UI';border:1px solid #e0e0e0;"
                           "border-radius:8px;padding-top:16px;background:#f8f9fa;}"
                           "QGroupBox::title{subcontrol-origin:margin;left:10px;}")
        box_layout = QVBoxLayout(box)

        box_layout.addWidget(QLabel(f"Thu ngân: {self.user.full_name}", styleSheet="color:#000000;font:italic 13px 'Segoe UI';"))
        
        self.lbl_subtotal = QLabel("Tạm tính: 0 đ")
        self.lbl_subtotal.setStyleSheet("color:#000000;font:14px 'Segoe UI';")
        box_layout.addWidget(self.lbl_subtotal)

        # Giảm giá
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Giảm giá (%):", styleSheet="color:#000000;font:13px;"))
        self.spn_discount = QDoubleSpinBox()
        self.spn_discount.setRange(0, 100); self.spn_discount.setValue(0)
        self.spn_discount.setStyleSheet("padding:4px;font:13px;border:1px solid #ced4da;border-radius:4px;background:#ffffff;")
        self.spn_discount.valueChanged.connect(self.calc_total)
        disc_row.addWidget(self.spn_discount)
        box_layout.addLayout(disc_row)

        self.lbl_discount = QLabel("Giảm: 0 đ")
        self.lbl_discount.setStyleSheet("color:#e65100;font:13px 'Segoe UI';")
        box_layout.addWidget(self.lbl_discount)

        self.lbl_tax = QLabel("VAT (10%): 0 đ")
        self.lbl_tax.setStyleSheet("color:#000000;font:13px 'Segoe UI';")
        box_layout.addWidget(self.lbl_tax)

        self.lbl_total = QLabel("TỔNG CỘNG: 0 đ")
        self.lbl_total.setStyleSheet("color:#d32f2f;font:bold 20px 'Segoe UI';")
        box_layout.addWidget(self.lbl_total)

        # Nút kiểm tra đặt bàn
        btn_check_booking = QPushButton("Kiểm tra đặt bàn")
        btn_check_booking.setStyleSheet("background:#00bcd4;color:#fff;border:none;border-radius:6px;"
                                        "padding:8px;font:bold 13px 'Segoe UI';")
        btn_check_booking.clicked.connect(self.check_booking)
        box_layout.addWidget(btn_check_booking)

        # Phương thức thanh toán
        pay_row = QHBoxLayout()
        pay_row.addWidget(QLabel("Phương thức:", styleSheet="color:#000000;font:13px;"))
        self.cmb_pay = QComboBox()
        self.cmb_pay.addItems(["Tiền mặt", "Thẻ", "Chuyển khoản", "Ví điện tử"])
        self.cmb_pay.setStyleSheet("padding:6px;font:13px;border:1px solid #ced4da;border-radius:4px;background:#ffffff;")
        pay_row.addWidget(self.cmb_pay)
        box_layout.addLayout(pay_row)

        # Nút thanh toán
        btn_create = QPushButton("Tạo hóa đơn tạm")
        btn_create.setStyleSheet("background:#ff9800;color:#fff;border:none;border-radius:8px;"
                                  "padding:10px;font:bold 14px 'Segoe UI';")
        btn_create.clicked.connect(self.create_temp_bill)
        box_layout.addWidget(btn_create)

        btn_pay = QPushButton("XÁC NHẬN THANH TOÁN")
        btn_pay.setStyleSheet("background:#4caf50;color:#fff;border:none;border-radius:8px;"
                               "padding:12px;font:bold 15px 'Segoe UI';")
        btn_pay.clicked.connect(self.confirm_payment)
        box_layout.addWidget(btn_pay)

        right.addWidget(box)
        right.addStretch()
        content.addLayout(right, 2)
        layout.addLayout(content)

    def load_tables(self):
        tables = self.dao.get_all_tables(self.rid)
        self.cmb_table.clear()
        self.tables_list = tables
        # Chỉ hiện bàn đang occupied
        for t in tables:
            if t.status == 'occupied':
                self.cmb_table.addItem(f"Bàn {t.table_number} ({t.area})", t.table_id)

    def find_bill(self):
        """Bước 1: Tìm hóa đơn theo bàn - lấy tất cả order active."""
        table_id = self.cmb_table.currentData()
        if not table_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn bàn!")
            return
        orders = self.dao.get_active_orders_by_table(table_id)
        if not orders:
            QMessageBox.information(self, "Thông báo", "Bàn này không có order nào!")
            return

        # Hiển thị tất cả món từ các order
        all_items = []
        self.current_order_ids = []
        for o in orders:
            self.current_order_ids.append(o.order_id)
            all_items.extend([it for it in o.items if it.cook_status != 'cancelled'])

        self.tbl_items.setRowCount(len(all_items))
        subtotal = 0
        for i, it in enumerate(all_items):
            line = it.quantity * it.unit_price
            subtotal += line
            self.tbl_items.setItem(i, 0, QTableWidgetItem(it.dish_name))
            self.tbl_items.setItem(i, 1, QTableWidgetItem(str(it.quantity)))
            self.tbl_items.setItem(i, 2, QTableWidgetItem(f"{it.unit_price:,.0f}đ"))
            self.tbl_items.setItem(i, 3, QTableWidgetItem(f"{line:,.0f}đ"))

        self.subtotal = subtotal
        self.lbl_subtotal.setText(f"Tạm tính: {subtotal:,.0f} đ")
        self.calc_total()

    def calc_total(self):
        """Bước 2: Tính tổng sau giảm giá và thuế."""
        if not hasattr(self, 'subtotal'): return
        disc_pct = self.spn_discount.value()
        disc_amt = self.subtotal * disc_pct / 100
        after_disc = self.subtotal - disc_amt
        tax = after_disc * 0.1
        total = after_disc + tax
        self.lbl_discount.setText(f"Giảm: -{disc_amt:,.0f} đ")
        self.lbl_tax.setText(f"VAT (10%): +{tax:,.0f} đ")
        self.lbl_total.setText(f"TỔNG CỘNG: {total:,.0f} đ")

    def create_temp_bill(self):
        """Bước 3: Tạo hóa đơn tạm (unpaid)."""
        if not hasattr(self, 'current_order_ids') or not self.current_order_ids:
            QMessageBox.warning(self, "Lỗi", "Chưa tìm hóa đơn!")
            return
        table_id = self.cmb_table.currentData()
        pay_map = {"Tiền mặt":"cash","Thẻ":"card","Chuyển khoản":"transfer","Ví điện tử":"e_wallet"}
        bill = Bill(table_id=table_id, user_id=self.user.user_id,
                    discount_percent=self.spn_discount.value(),
                    tax_percent=10, payment_method=pay_map.get(self.cmb_pay.currentText(),"cash"))
        self.current_bill = self.dao.create_bill(bill, self.current_order_ids)
        QMessageBox.information(self, "OK",
            f"Hóa đơn tạm #{self.current_bill.bill_id}\n"
            f"Tổng: {self.current_bill.total_amount:,.0f} đ")

    def confirm_payment(self):
        """Bước 4: Xác nhận thanh toán - đánh dấu paid, giải phóng bàn."""
        if not self.current_bill:
            QMessageBox.warning(self, "Lỗi", "Chưa tạo hóa đơn tạm!")
            return
        reply = QMessageBox.question(self, "Xác nhận",
            f"Xác nhận thanh toán {self.current_bill.total_amount:,.0f} đ?")
        if reply == QMessageBox.StandardButton.Yes:
            pay_map = {"Tiền mặt":"cash","Thẻ":"card","Chuyển khoản":"transfer","Ví điện tử":"e_wallet"}
            self.dao.pay_bill(self.current_bill.bill_id,
                              pay_map.get(self.cmb_pay.currentText(), "cash"))
            # Cập nhật cache: bàn trống, xóa cache doanh thu
            table_id = self.cmb_table.currentData()
            self.cache.set_table_status(self.rid, table_id, 'available')
            self.cache.invalidate_tables(self.rid)
            self.cache.invalidate_revenue(self.rid, str(date.today()))
            self.cache.invalidate_reports(self.rid)
            QMessageBox.information(self, "Thành công", "Thanh toán thành công!")
            self.current_bill = None
            self.tbl_items.setRowCount(0)
            self.lbl_total.setText("TỔNG CỘNG: 0 đ")
            self.load_tables()

    def check_booking(self):
        """Bước kiểm tra đặt bàn để áp dụng giảm giá."""
        table_id = self.cmb_table.currentData()
        if not table_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn bàn!")
            return

        booking = self.dao.get_booking_by_table(table_id)
        if not booking:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy thông tin đặt bàn (Booking) cho bàn này trong ngày hôm nay!")
            return

        # Hiển thị thông tin
        from PyQt6.QtWidgets import QDialog, QFormLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Thông tin đặt bàn")
        dialog.setMinimumWidth(300)
        layout = QFormLayout(dialog)

        layout.addRow("Mã đặt bàn:", QLabel(booking.booking_code or "N/A"))
        layout.addRow("Tên khách hàng:", QLabel(booking.guest_name))
        layout.addRow("Nhân viên nhận đặt:", QLabel(booking.user_name))
        layout.addRow("Giảm giá:", QLabel(f"{booking.discount_percent or 0.0}%"))
        layout.addRow("Ghi chú:", QLabel(booking.note or "Không có"))

        btn_box = QHBoxLayout()
        btn_apply = QPushButton("Áp dụng")
        btn_apply.setStyleSheet("background:#4caf50;color:#fff;padding:6px;border-radius:4px;")
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet("background:#f44336;color:#fff;padding:6px;border-radius:4px;")
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_cancel)

        btn_apply.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        layout.addRow(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.spn_discount.setValue(float(booking.discount_percent or 0.0))
            self.calc_total()
            QMessageBox.information(self, "Thành công", f"Đã áp dụng giảm giá {booking.discount_percent or 0.0}% từ mã đặt bàn!")
