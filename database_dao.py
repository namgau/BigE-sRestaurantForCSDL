# ============================================================
# database_dao.py - Data Access Object (Lớp truy xuất CSDL)
# ============================================================
import pyodbc
import hashlib
from datetime import datetime, date
from app_config import get_sql_connection_string
from models import (User, Table, Category, Dish, Client,
                    Booking, Order, OrderedDish, Bill)


class DatabaseDAO:
    """Lớp DAO chịu trách nhiệm tương tác trực tiếp với SQL Server."""

    def __init__(self):
        self.conn_str = get_sql_connection_string()

    def _get_connection(self):
        """Mở kết nối mới tới SQL Server."""
        return pyodbc.connect(self.conn_str)

    # ==========================================================
    # AUTH - Xác thực người dùng
    # ==========================================================
    def authenticate(self, username, password):
        """Xác thực đăng nhập. Trả về User hoặc None."""
        pwd_hash = hashlib.md5(password.encode()).hexdigest()
        sql = "SELECT * FROM Users WHERE username=? AND password_hash=? AND is_active=1"
        with self._get_connection() as conn:
            row = conn.execute(sql, username, pwd_hash).fetchone()
            if row:
                return User(user_id=row.user_id,
                            username=row.username, password_hash=row.password_hash,
                            full_name=row.full_name, position=row.position,
                            phone=row.phone, is_active=row.is_active)
        return None

    # ==========================================================
    # USERS - Quản lý nhân sự
    # ==========================================================
    def get_all_users(self):
        sql = "SELECT * FROM Users ORDER BY user_id"
        with self._get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [User(user_id=r.user_id,
                         username=r.username, full_name=r.full_name,
                         position=r.position, phone=r.phone, is_active=r.is_active) for r in rows]

    def add_user(self, user: User):
        pwd_hash = hashlib.md5('123456'.encode()).hexdigest()
        sql = """INSERT INTO Users(username,password_hash,full_name,position,phone)
                 VALUES(?,?,?,?,?)"""
        with self._get_connection() as conn:
            conn.execute(sql, user.username, pwd_hash,
                         user.full_name, user.position, user.phone)
            conn.commit()

    def update_user(self, user: User):
        sql = "UPDATE Users SET full_name=?,position=?,phone=?,is_active=? WHERE user_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, user.full_name, user.position, user.phone,
                         user.is_active, user.user_id)
            conn.commit()

    def delete_user(self, user_id):
        """Vô hiệu hóa nhân viên (soft delete để giữ tham chiếu)."""
        sql = "UPDATE Users SET is_active=0 WHERE user_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, user_id)
            conn.commit()

    def reset_password(self, user_id):
        pwd_hash = hashlib.md5('123456'.encode()).hexdigest()
        sql = "UPDATE Users SET password_hash=? WHERE user_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, pwd_hash, user_id)
            conn.commit()

    # ==========================================================
    # TABLES - Quản lý bàn
    # ==========================================================
    def get_all_tables(self, restaurant_id):
        """Lấy tất cả bàn của nhà hàng, sắp xếp theo số bàn."""
        sql = "SELECT * FROM Tables WHERE restaurant_id=? ORDER BY table_number"
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [Table(table_id=r.table_id, restaurant_id=r.restaurant_id,
                          table_number=r.table_number, capacity=r.capacity,
                          area=r.area, status=r.status) for r in rows]

    def update_table_status(self, table_id, status):
        """Cập nhật trạng thái bàn trong SQL Server."""
        sql = "UPDATE Tables SET status=? WHERE table_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, status, table_id)
            conn.commit()

    def add_table(self, table: Table):
        sql = "INSERT INTO Tables(restaurant_id,table_number,capacity,area) VALUES(?,?,?,?)"
        with self._get_connection() as conn:
            conn.execute(sql, table.restaurant_id, table.table_number,
                         table.capacity, table.area)
            conn.commit()

    def delete_table(self, table_id):
        sql = "DELETE FROM Tables WHERE table_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, table_id)
            conn.commit()

    # ==========================================================
    # CATEGORY - Danh mục món ăn
    # ==========================================================
    def get_all_categories(self, restaurant_id):
        sql = "SELECT * FROM Category WHERE restaurant_id=? AND is_active=1 ORDER BY display_order"
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [Category(category_id=r.category_id, restaurant_id=r.restaurant_id,
                             name=r.name, description=r.description,
                             display_order=r.display_order) for r in rows]

    def add_category(self, cat: Category):
        sql = "INSERT INTO Category(restaurant_id,name,description,display_order) VALUES(?,?,?,?)"
        with self._get_connection() as conn:
            conn.execute(sql, cat.restaurant_id, cat.name, cat.description, cat.display_order)
            conn.commit()

    def update_category(self, cat: Category):
        sql = "UPDATE Category SET name=?,description=?,display_order=? WHERE category_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, cat.name, cat.description, cat.display_order, cat.category_id)
            conn.commit()

    # ==========================================================
    # DISH - Món ăn
    # ==========================================================
    def get_dishes_by_category(self, category_id):
        sql = """SELECT d.*, c.name as cat_name FROM Dish d
                 JOIN Category c ON d.category_id=c.category_id
                 WHERE d.category_id=? AND d.is_available=1 ORDER BY d.name"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, category_id).fetchall()
            return [Dish(dish_id=r.dish_id, category_id=r.category_id, name=r.name,
                         description=r.description, price=float(r.price),
                         is_available=r.is_available, category_name=r.cat_name) for r in rows]

    def get_all_dishes(self, restaurant_id):
        sql = """SELECT d.*, c.name as cat_name FROM Dish d
                 JOIN Category c ON d.category_id=c.category_id
                 WHERE c.restaurant_id=? ORDER BY c.display_order, d.name"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [Dish(dish_id=r.dish_id, category_id=r.category_id, name=r.name,
                         description=r.description, price=float(r.price),
                         is_available=r.is_available, category_name=r.cat_name) for r in rows]

    def add_dish(self, dish: Dish):
        sql = "INSERT INTO Dish(category_id,name,description,price) VALUES(?,?,?,?)"
        with self._get_connection() as conn:
            conn.execute(sql, dish.category_id, dish.name, dish.description, dish.price)
            conn.commit()

    def update_dish(self, dish: Dish):
        sql = "UPDATE Dish SET category_id=?,name=?,description=?,price=?,is_available=? WHERE dish_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, dish.category_id, dish.name, dish.description,
                         dish.price, dish.is_available, dish.dish_id)
            conn.commit()

    def delete_dish(self, dish_id):
        """Xóa món ăn khỏi database."""
        sql = "DELETE FROM Dish WHERE dish_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, dish_id)
            conn.commit()

    # ==========================================================
    # CLIENT - Khách hàng
    # ==========================================================
    def search_client(self, phone):
        sql = "SELECT * FROM Client WHERE phone=?"
        with self._get_connection() as conn:
            r = conn.execute(sql, phone).fetchone()
            if r:
                return Client(client_id=r.client_id, full_name=r.full_name,
                              phone=r.phone, email=r.email, loyalty_points=r.loyalty_points)
        return None

    def search_clients(self, keyword):
        """Tìm kiếm khách hàng theo tên hoặc số điện thoại."""
        sql = "SELECT * FROM Client WHERE full_name LIKE ? OR phone LIKE ?"
        keyword_param = f"%{keyword}%"
        with self._get_connection() as conn:
            rows = conn.execute(sql, keyword_param, keyword_param).fetchall()
            return [Client(client_id=r.client_id, full_name=r.full_name,
                           phone=r.phone, email=r.email, loyalty_points=r.loyalty_points) for r in rows]

    def add_client(self, client: Client):
        sql = "INSERT INTO Client(full_name,phone,email) OUTPUT INSERTED.client_id VALUES(?,?,?)"
        with self._get_connection() as conn:
            cursor = conn.execute(sql, client.full_name, client.phone, client.email)
            client_id = cursor.fetchone()[0]
            conn.commit()
            return client_id

    # ==========================================================
    # BOOKING - Đặt bàn
    # ==========================================================
    def search_free_tables(self, restaurant_id, booking_date, booking_time, capacity):
        """Kiểm tra bàn trống dựa trên thời gian và sức chứa."""
        sql = """SELECT * FROM Tables t
                 WHERE t.restaurant_id=? AND t.capacity >= ? AND t.status != 'maintenance'
                 AND t.table_id NOT IN (
                     SELECT table_id FROM Booking 
                     WHERE booking_date=? AND status='confirmed'
                 ) ORDER BY t.capacity, t.table_number"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id, capacity, booking_date).fetchall()
            return [Table(table_id=r.table_id, restaurant_id=r.restaurant_id,
                          table_number=r.table_number, capacity=r.capacity,
                          area=r.area, status=r.status) for r in rows]

    def create_booking(self, booking: Booking):
        """Tạo đặt bàn mới và cập nhật trạng thái bàn thành 'reserved'."""
        with self._get_connection() as conn:
            sql = """INSERT INTO Booking(table_id,client_id,user_id,guest_name,
                     guest_phone,guest_count,booking_date,booking_time,note,discount_percent,booking_code)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)"""
            conn.execute(sql, booking.table_id, booking.client_id, booking.user_id,
                         booking.guest_name, booking.guest_phone, booking.guest_count,
                         booking.booking_date, booking.booking_time, booking.note,
                         booking.discount_percent, booking.booking_code)
            # Cập nhật trạng thái bàn sang 'reserved'
            conn.execute("UPDATE Tables SET status='reserved' WHERE table_id=?",
                         booking.table_id)
            conn.commit()

    def get_bookings_by_date(self, restaurant_id, target_date):
        sql = """SELECT b.*, t.table_number, t.area, u.full_name as user_name FROM Booking b
                 JOIN Tables t ON b.table_id=t.table_id
                 JOIN Users u ON b.user_id=u.user_id
                 WHERE t.restaurant_id=? AND b.booking_date=?
                 ORDER BY b.booking_time"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id, target_date).fetchall()
            return [Booking(booking_id=r.booking_id, table_id=r.table_id, client_id=r.client_id, user_id=r.user_id,
                            guest_name=r.guest_name, guest_phone=r.guest_phone,
                            guest_count=r.guest_count, booking_date=r.booking_date,
                            booking_time=r.booking_time, status=r.status,
                            note=r.note, discount_percent=r.discount_percent, booking_code=r.booking_code,
                            table_number=r.table_number,
                            table_area=r.area, user_name=r.user_name) for r in rows]

    def get_all_bookings(self, restaurant_id):
        sql = """SELECT b.*, t.table_number, t.area, u.full_name as user_name FROM Booking b
                 JOIN Tables t ON b.table_id=t.table_id
                 JOIN Users u ON b.user_id=u.user_id
                 WHERE t.restaurant_id=?
                 ORDER BY b.booking_date DESC, b.booking_time DESC"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [Booking(booking_id=r.booking_id, table_id=r.table_id, client_id=r.client_id, user_id=r.user_id,
                            guest_name=r.guest_name, guest_phone=r.guest_phone,
                            guest_count=r.guest_count, booking_date=r.booking_date,
                            booking_time=r.booking_time, status=r.status,
                            note=r.note, discount_percent=r.discount_percent, booking_code=r.booking_code,
                            table_number=r.table_number,
                            table_area=r.area, user_name=r.user_name) for r in rows]

    def update_booking(self, booking: Booking):
        sql = """UPDATE Booking SET guest_name=?, guest_phone=?, guest_count=?, 
                 booking_date=?, booking_time=?, note=?, status=?, discount_percent=?, booking_code=? 
                 WHERE booking_id=?"""
        with self._get_connection() as conn:
            conn.execute(sql, booking.guest_name, booking.guest_phone, booking.guest_count,
                         booking.booking_date, booking.booking_time, booking.note, 
                         booking.status, booking.discount_percent, booking.booking_code,
                         booking.booking_id)
            conn.commit()

    def get_booking_by_table(self, table_id, target_date=None):
        if not target_date:
            target_date = date.today()
        sql = """SELECT TOP 1 b.*, t.table_number, t.area, u.full_name as user_name FROM Booking b
                 JOIN Tables t ON b.table_id=t.table_id
                 JOIN Users u ON b.user_id=u.user_id
                 WHERE b.table_id=? AND b.booking_date=? AND b.status IN ('confirmed', 'completed')
                 ORDER BY b.booking_time DESC"""
        with self._get_connection() as conn:
            r = conn.execute(sql, table_id, target_date).fetchone()
            if r:
                return Booking(booking_id=r.booking_id, table_id=r.table_id, client_id=r.client_id, user_id=r.user_id,
                               guest_name=r.guest_name, guest_phone=r.guest_phone,
                               guest_count=r.guest_count, booking_date=r.booking_date,
                               booking_time=r.booking_time, status=r.status,
                               note=r.note, discount_percent=r.discount_percent, booking_code=r.booking_code,
                               table_number=r.table_number, table_area=r.area, user_name=r.user_name)
        return None

    def cancel_booking(self, booking_id):
        with self._get_connection() as conn:
            row = conn.execute("SELECT table_id FROM Booking WHERE booking_id=?", booking_id).fetchone()
            if row:
                conn.execute("UPDATE Booking SET status='cancelled' WHERE booking_id=?", booking_id)
                conn.execute("UPDATE Tables SET status='available' WHERE table_id=?", row.table_id)
                conn.commit()

    def delete_booking(self, booking_id):
        """Xóa vĩnh viễn lịch đặt khỏi database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM Booking WHERE booking_id=?", booking_id)
            conn.commit()

    # ==========================================================
    # ORDER - Phiếu gọi món
    # ==========================================================
    def get_all_tables_cinema(self, restaurant_id):
        """Lấy tất cả bàn của nhà hàng để hiển thị sơ đồ cinema."""
        sql = "SELECT * FROM Tables WHERE restaurant_id=? ORDER BY table_number"
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [Table(table_id=r.table_id, restaurant_id=r.restaurant_id,
                          table_number=r.table_number, capacity=r.capacity,
                          area=r.area, status=r.status) for r in rows]

    def get_all_areas(self, restaurant_id):
        """Lấy danh sách các khu vực duy nhất."""
        sql = "SELECT DISTINCT area FROM Tables WHERE restaurant_id=?"
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [r.area for r in rows]

    def search_dish(self, restaurant_id, keyword="", category_id=None):
        """Tìm món ăn theo từ khóa tên và danh mục."""
        sql = """SELECT d.*, c.name as cat_name FROM Dish d
                 JOIN Category c ON d.category_id=c.category_id
                 WHERE c.restaurant_id=? AND d.is_available=1"""
        params = [restaurant_id]
        if keyword:
            sql += " AND d.name LIKE ?"
            params.append(f"%{keyword}%")
        if category_id:
            sql += " AND d.category_id = ?"
            params.append(category_id)
        sql += " ORDER BY d.name"
        with self._get_connection() as conn:
            rows = conn.execute(sql, *params).fetchall()
            return [Dish(dish_id=r.dish_id, category_id=r.category_id, name=r.name,
                         description=r.description, price=float(r.price),
                         is_available=r.is_available, category_name=r.cat_name) for r in rows]

    def get_all_categories(self, restaurant_id):
        """Lấy danh sách danh mục món ăn."""
        sql = "SELECT * FROM Category WHERE restaurant_id=? ORDER BY display_order"
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return rows

    def add_order_full(self, table_id, user_id, ordered_dishes):
        """Lưu thông tin đơn hàng mới vào DB (bảng Order và OrderedDish), cập nhật trạng thái bàn."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO Orders(table_id,user_id,note) OUTPUT INSERTED.order_id
                   VALUES(?,?,?)""", table_id, user_id, "")
            order_id = cursor.fetchone()[0]
            
            for dish in ordered_dishes:
                conn.execute("""INSERT INTO OrderedDish(order_id,dish_id,quantity,unit_price,note)
                                VALUES(?,?,?,?,?)""", 
                             order_id, dish.dish_id, dish.quantity, dish.unit_price, dish.note)
                             
            conn.execute("UPDATE Tables SET status='occupied' WHERE table_id=?", table_id)
            conn.commit()
            return order_id

    def create_order(self, table_id, user_id, note=""):
        """Tạo order mới, cập nhật bàn thành 'occupied'. Trả về order_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO Orders(table_id,user_id,note) OUTPUT INSERTED.order_id
                   VALUES(?,?,?)""", table_id, user_id, note)
            order_id = cursor.fetchone()[0]
            conn.execute("UPDATE Tables SET status='occupied' WHERE table_id=?", table_id)
            conn.commit()
            return order_id

    def add_dish_to_order(self, order_id, dish_id, quantity, unit_price, note=""):
        """Thêm món vào order. Ghi unit_price tại thời điểm gọi."""
        sql = """INSERT INTO OrderedDish(order_id,dish_id,quantity,unit_price,note)
                 VALUES(?,?,?,?,?)"""
        with self._get_connection() as conn:
            conn.execute(sql, order_id, dish_id, quantity, unit_price, note)
            conn.commit()

    def get_order_items(self, order_id):
        """Lấy danh sách món của một order."""
        sql = """SELECT od.*, d.name as dish_name FROM OrderedDish od
                 JOIN Dish d ON od.dish_id=d.dish_id
                 WHERE od.order_id=? ORDER BY od.created_at"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, order_id).fetchall()
            return [OrderedDish(ordered_dish_id=r.ordered_dish_id, order_id=r.order_id,
                                dish_id=r.dish_id, quantity=r.quantity,
                                unit_price=float(r.unit_price), note=r.note or "",
                                cook_status=r.cook_status, dish_name=r.dish_name) for r in rows]

    def get_active_orders_by_table(self, table_id):
        """Lấy các order đang active của bàn."""
        sql = """SELECT o.*, t.table_number, u.full_name as waiter_name
                 FROM Orders o JOIN Tables t ON o.table_id=t.table_id
                 JOIN Users u ON o.user_id=u.user_id
                 WHERE o.table_id=? AND o.status='active'"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, table_id).fetchall()
            orders = []
            for r in rows:
                o = Order(order_id=r.order_id, table_id=r.table_id, user_id=r.user_id,
                          order_time=r.order_time, status=r.status,
                          table_number=r.table_number, waiter_name=r.waiter_name)
                o.items = self.get_order_items(o.order_id)
                orders.append(o)
            return orders

    def transfer_table(self, order_id, old_table_id, new_table_id):
        """Chuyển bàn: cập nhật order sang bàn mới, đổi trạng thái 2 bàn."""
        with self._get_connection() as conn:
            conn.execute("UPDATE Orders SET table_id=? WHERE order_id=?", new_table_id, order_id)
            # Kiểm tra bàn cũ còn order active không
            remaining = conn.execute(
                "SELECT COUNT(*) FROM Orders WHERE table_id=? AND status='active'",
                old_table_id).fetchone()[0]
            if remaining == 0:
                conn.execute("UPDATE Tables SET status='available' WHERE table_id=?", old_table_id)
            conn.execute("UPDATE Tables SET status='occupied' WHERE table_id=?", new_table_id)
            conn.commit()

    # ==========================================================
    # KITCHEN - Bếp (cập nhật trạng thái món)
    # ==========================================================
    def get_kitchen_queue(self, restaurant_id):
        """Lấy danh sách món chờ chế biến và đang chế biến."""
        sql = """SELECT od.*, d.name as dish_name, t.table_number
                 FROM OrderedDish od
                 JOIN Dish d ON od.dish_id=d.dish_id
                 JOIN Orders o ON od.order_id=o.order_id
                 JOIN Tables t ON o.table_id=t.table_id
                 WHERE t.restaurant_id=? AND od.cook_status IN ('pending','cooking')
                   AND o.status='active'
                 ORDER BY od.created_at"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id).fetchall()
            return [OrderedDish(ordered_dish_id=r.ordered_dish_id, order_id=r.order_id,
                                dish_id=r.dish_id, quantity=r.quantity,
                                unit_price=float(r.unit_price), note=r.note or "",
                                cook_status=r.cook_status, dish_name=r.dish_name,
                                table_number=r.table_number) for r in rows]

    def update_cook_status(self, ordered_dish_id, new_status):
        """Cập nhật trạng thái chế biến: pending -> cooking -> done."""
        sql = "UPDATE OrderedDish SET cook_status=? WHERE ordered_dish_id=?"
        with self._get_connection() as conn:
            conn.execute(sql, new_status, ordered_dish_id)
            conn.commit()

    # ==========================================================
    # BILL - Hóa đơn thanh toán
    # ==========================================================
    def create_bill(self, bill: Bill, order_ids: list):
        """
        Tạo hóa đơn: tính tổng tiền từ các order, áp giảm giá, thuế.
        Luồng: Tìm order -> Tính subtotal -> Áp giảm giá -> Tính thuế -> Lưu Bill -> Gắn bill_id vào Orders.
        """
        with self._get_connection() as conn:
            # Bước 1: Tính subtotal từ các món trong các order
            placeholders = ','.join(['?'] * len(order_ids))
            sql_sum = f"""SELECT ISNULL(SUM(od.quantity * od.unit_price), 0)
                          FROM OrderedDish od WHERE od.order_id IN ({placeholders})
                          AND od.cook_status != 'cancelled'"""
            subtotal = float(conn.execute(sql_sum, *order_ids).fetchone()[0])

            # Bước 2: Tính giảm giá
            discount_amt = subtotal * bill.discount_percent / 100
            after_discount = subtotal - discount_amt

            # Bước 3: Tính thuế
            tax_amt = after_discount * bill.tax_percent / 100
            total = after_discount + tax_amt

            # Bước 4: Lưu hóa đơn
            cursor = conn.execute(
                """INSERT INTO Bill(table_id,user_id,client_id,subtotal,discount_percent,
                   discount_amount,tax_percent,tax_amount,total_amount,payment_method,note)
                   OUTPUT INSERTED.bill_id
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                bill.table_id, bill.user_id, bill.client_id, subtotal,
                bill.discount_percent, discount_amt, bill.tax_percent,
                tax_amt, total, bill.payment_method, bill.note)
            bill_id = cursor.fetchone()[0]

            # Bước 5: Gắn bill_id vào các order (thay thế BillOrder)
            for oid in order_ids:
                conn.execute("UPDATE Orders SET bill_id=? WHERE order_id=?", bill_id, oid)

            conn.commit()
            bill.bill_id = bill_id
            bill.subtotal = subtotal
            bill.discount_amount = discount_amt
            bill.tax_amount = tax_amt
            bill.total_amount = total
            return bill

    def pay_bill(self, bill_id, payment_method="cash"):
        """Thanh toán hóa đơn: đánh dấu paid, giải phóng bàn."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE Bill SET status='paid',payment_method=?,paid_at=GETDATE() WHERE bill_id=?",
                payment_method, bill_id)
            # Lấy table_id và hoàn tất các order
            row = conn.execute("SELECT table_id FROM Bill WHERE bill_id=?", bill_id).fetchone()
            if row:
                # Đánh dấu các order thuộc bill này là completed
                conn.execute(
                    "UPDATE Orders SET status='completed' WHERE bill_id=?", bill_id)
                # Kiểm tra bàn còn order active không
                remaining = conn.execute(
                    "SELECT COUNT(*) FROM Orders WHERE table_id=? AND status='active'",
                    row.table_id).fetchone()[0]
                if remaining == 0:
                    conn.execute("UPDATE Tables SET status='available' WHERE table_id=?", row.table_id)
            conn.commit()
        # Cập nhật thống kê vào các bảng Stat (ERD Requirement)
        self.sync_statistics(bill_id)

    def sync_statistics(self, bill_id):
        """Đồng bộ dữ liệu từ Bill vừa thanh toán vào các bảng Thống kê (Stat)."""
        bill = self.get_bill_by_id(bill_id)
        if not bill or bill.status != 'paid': return
        
        pay_date = bill.paid_at.date() if bill.paid_at else date.today()
        
        with self._get_connection() as conn:
            # 1. Cập nhật RestaurantStat
            row_r = conn.execute("SELECT restaurant_id FROM Tables WHERE table_id=?", bill.table_id).fetchone()
            if row_r:
                rid = row_r.restaurant_id
                exist = conn.execute("SELECT stat_id FROM RestaurantStat WHERE restaurant_id=? AND day=?", rid, pay_date).fetchone()
                if exist:
                    conn.execute("""UPDATE RestaurantStat SET revenue = revenue + ?, total_bills = total_bills + 1 
                                 WHERE stat_id=?""", bill.total_amount, exist.stat_id)
                else:
                    conn.execute("""INSERT INTO RestaurantStat (restaurant_id, day, revenue, total_bills) 
                                 VALUES (?, ?, ?, 1)""", rid, pay_date, bill.total_amount)

            # 2. Cập nhật TableStat
            exist_t = conn.execute("SELECT stat_id FROM TableStat WHERE table_id=? AND day=?", bill.table_id, pay_date).fetchone()
            if exist_t:
                conn.execute("UPDATE TableStat SET income = income + ?, total_guests = total_guests + 1 WHERE stat_id=?", 
                             bill.total_amount, exist_t.stat_id)
            else:
                conn.execute("INSERT INTO TableStat (table_id, day, income, total_guests) VALUES (?, ?, ?, 1)", 
                             bill.table_id, pay_date, bill.total_amount)

            # 3. Cập nhật ClientStat
            if bill.client_id:
                exist_c = conn.execute("SELECT stat_id FROM ClientStat WHERE client_id=? AND day=?", bill.client_id, pay_date).fetchone()
                if exist_c:
                    conn.execute("UPDATE ClientStat SET payment = payment + ? WHERE stat_id=?", bill.total_amount, exist_c.stat_id)
                else:
                    conn.execute("INSERT INTO ClientStat (client_id, day, payment) VALUES (?, ?, ?)", bill.client_id, pay_date, bill.total_amount)

            # 4. Cập nhật DishStat
            sql_dishes = """SELECT od.dish_id, SUM(od.quantity) as qty, SUM(od.quantity * od.unit_price) as rev
                            FROM OrderedDish od JOIN Orders o ON od.order_id = o.order_id
                            WHERE o.bill_id=? GROUP BY od.dish_id"""
            dishes = conn.execute(sql_dishes, bill_id).fetchall()
            for d in dishes:
                exist_d = conn.execute("SELECT stat_id FROM DishStat WHERE dish_id=? AND day=?", d.dish_id, pay_date).fetchone()
                if exist_d:
                    conn.execute("UPDATE DishStat SET total_sold = total_sold + ?, revenue = revenue + ? WHERE stat_id=?", 
                                 d.qty, d.rev, exist_d.stat_id)
                else:
                    conn.execute("INSERT INTO DishStat (dish_id, day, total_sold, revenue) VALUES (?, ?, ?, ?)", 
                                 d.dish_id, pay_date, d.qty, d.rev)

            # 5. Cập nhật IncomeStat
            hr = bill.paid_at.hour if bill.paid_at else 0
            period = "06:00 - 10:00" if 6 <= hr < 10 else "10:00 - 14:00" if 10 <= hr < 14 else "14:00 - 18:00" if 14 <= hr < 18 else "18:00 - 22:00" if 18 <= hr < 22 else "22:00 - 06:00"
            conn.execute("INSERT INTO IncomeStat (bill_id, period, revenue) VALUES (?, ?, ?)", bill_id, period, bill.total_amount)
            
            conn.commit()

    def get_bill_by_id(self, bill_id):
        sql = """SELECT b.*, t.table_number, u.full_name as cashier_name
                 FROM Bill b JOIN Tables t ON b.table_id=t.table_id
                 JOIN Users u ON b.user_id=u.user_id WHERE b.bill_id=?"""
        with self._get_connection() as conn:
            r = conn.execute(sql, bill_id).fetchone()
            if r:
                return Bill(bill_id=r.bill_id, table_id=r.table_id, user_id=r.user_id,
                            client_id=r.client_id, subtotal=float(r.subtotal),
                            discount_percent=float(r.discount_percent),
                            discount_amount=float(r.discount_amount),
                            tax_percent=float(r.tax_percent),
                            tax_amount=float(r.tax_amount),
                            total_amount=float(r.total_amount),
                            payment_method=r.payment_method, status=r.status,
                            created_at=r.created_at, paid_at=r.paid_at,
                            table_number=r.table_number, cashier_name=r.cashier_name)
        return None

    def get_unpaid_bill_by_table(self, table_id):
        sql = """SELECT b.bill_id FROM Bill b WHERE b.table_id=? AND b.status='unpaid'
                 ORDER BY b.created_at DESC"""
        with self._get_connection() as conn:
            r = conn.execute(sql, table_id).fetchone()
            if r:
                return self.get_bill_by_id(r.bill_id)
        return None

    # ==========================================================
    # REVENUE - Doanh thu (cho báo cáo)
    # ==========================================================
    def get_revenue_by_date(self, restaurant_id, target_date):
        """Thống kê doanh thu theo ngày."""
        sql = """SELECT COUNT(*) as bill_count, ISNULL(SUM(total_amount),0) as total
                 FROM Bill b JOIN Tables t ON b.table_id=t.table_id
                 WHERE t.restaurant_id=? AND CAST(b.paid_at AS DATE)=? AND b.status='paid'"""
        with self._get_connection() as conn:
            r = conn.execute(sql, restaurant_id, target_date).fetchone()
            return {'date': str(target_date), 'bill_count': r.bill_count,
                    'total': float(r.total)}

    def get_revenue_by_month(self, restaurant_id, year, month):
        """Thống kê doanh thu theo tháng."""
        sql = """SELECT CAST(b.paid_at AS DATE) as pay_date,
                        COUNT(*) as bill_count, SUM(total_amount) as total
                 FROM Bill b JOIN Tables t ON b.table_id=t.table_id
                 WHERE t.restaurant_id=? AND YEAR(b.paid_at)=? AND MONTH(b.paid_at)=?
                   AND b.status='paid'
                 GROUP BY CAST(b.paid_at AS DATE) ORDER BY pay_date"""
        with self._get_connection() as conn:
            rows = conn.execute(sql, restaurant_id, year, month).fetchall()
            return [{'date': str(r.pay_date), 'bill_count': r.bill_count,
                     'total': float(r.total)} for r in rows]

    # ==========================================================
    # STATISTICS REPORT (QUẢN LÝ)
    # ==========================================================
    from models import TableStat, DishStat, ClientStat, HourlyStat

    def get_table_revenue_stats(self, restaurant_id, start_date, end_date):
        sql = """SELECT t.table_number, t.area, SUM(ts.total_guests) as total_guests, SUM(ts.income) as total_revenue
                 FROM Tables t
                 LEFT JOIN TableStat ts ON t.table_id = ts.table_id AND ts.day BETWEEN ? AND ?
                 WHERE t.restaurant_id = ?
                 GROUP BY t.table_id, t.table_number, t.area
                 ORDER BY t.table_number"""
        with self._get_connection() as conn:
            from models import TableStat
            rows = conn.execute(sql, start_date, end_date, restaurant_id).fetchall()
            return [TableStat(table_number=str(r.table_number), area=r.area or "Tầng 1", 
                              total_guests=r.total_guests or 0, total_revenue=float(r.total_revenue or 0)) for r in rows]

    def get_best_sellers_stats(self, restaurant_id, start_date, end_date):
        sql = """SELECT d.name as dish_name, c.name as category_name, 
                        SUM(ds.total_sold) as quantity_sold, 
                        SUM(ds.revenue) as revenue_contribution
                 FROM DishStat ds
                 JOIN Dish d ON ds.dish_id = d.dish_id
                 JOIN Category c ON d.category_id = c.category_id
                 WHERE c.restaurant_id = ? AND ds.day BETWEEN ? AND ?
                 GROUP BY d.dish_id, d.name, c.name
                 ORDER BY quantity_sold DESC"""
        with self._get_connection() as conn:
            from models import DishStat
            rows = conn.execute(sql, restaurant_id, start_date, end_date).fetchall()
            return [DishStat(dish_name=r.dish_name, category_name=r.category_name, 
                             quantity_sold=r.quantity_sold or 0, revenue_contribution=float(r.revenue_contribution or 0)) for r in rows]

    def get_client_spending_stats(self, start_date, end_date):
        sql = """SELECT c.full_name as client_name, c.phone, SUM(cs.payment) as total_spent
                 FROM Client c
                 JOIN ClientStat cs ON c.client_id = cs.client_id
                 WHERE cs.day BETWEEN ? AND ?
                 GROUP BY c.client_id, c.full_name, c.phone
                 ORDER BY total_spent DESC"""
        with self._get_connection() as conn:
            from models import ClientStat
            rows = conn.execute(sql, start_date, end_date).fetchall()
            return [ClientStat(client_name=r.client_name, phone=r.phone or "", total_spent=float(r.total_spent or 0)) for r in rows]

    def get_hourly_customer_stats(self, restaurant_id, target_date):
        sql = """SELECT 
                    ins.period as time_frame,
                    COUNT(ins.stat_id) as guest_count,
                    COUNT(DISTINCT b.table_id) as table_count,
                    SUM(ins.revenue) as revenue
                 FROM IncomeStat ins
                 JOIN Bill b ON ins.bill_id = b.bill_id
                 JOIN Tables t ON b.table_id = t.table_id
                 WHERE t.restaurant_id = ? AND CAST(b.paid_at AS DATE) = ?
                 GROUP BY ins.period
                 ORDER BY time_frame"""
        with self._get_connection() as conn:
            from models import HourlyStat
            rows = conn.execute(sql, restaurant_id, target_date).fetchall()
            return [HourlyStat(time_frame=r.time_frame, guest_count=r.guest_count or 0, 
                               table_count=r.table_count or 0, revenue=float(r.revenue or 0)) for r in rows]
