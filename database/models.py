# ============================================================
# models.py - Lớp Entity (Thực thể)
# Hệ thống Quản lý Nhà hàng
# ============================================================
# Mỗi class đại diện cho một bảng trong CSDL.
# Thuộc tính class tương ứng với cột trong bảng.
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List


@dataclass
class Restaurant:
    """Thực thể Nhà hàng - chứa thông tin cơ bản của nhà hàng."""
    restaurant_id: int = 0
    name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    created_at: Optional[datetime] = None


@dataclass
class User:
    """
    Thực thể Người dùng - đại diện cho nhân viên nhà hàng.
    Positions: manager, receptionist, waiter, chef
    """
    user_id: int = 0
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    position: str = ""      # manager | receptionist | waiter | chef
    phone: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Table:
    """
    Thực thể Bàn ăn.
    Status: available (trống) | occupied (đang dùng) | reserved (đã đặt) | maintenance (bảo trì)
    """
    table_id: int = 0
    restaurant_id: int = 0
    table_number: int = 0
    capacity: int = 4
    area: str = ""
    status: str = "available"


@dataclass
class Category:
    """Thực thể Danh mục món ăn."""
    category_id: int = 0
    restaurant_id: int = 0
    name: str = ""
    description: str = ""
    display_order: int = 0
    is_active: bool = True


@dataclass
class Dish:
    """Thực thể Món ăn."""
    dish_id: int = 0
    category_id: int = 0
    name: str = ""
    description: str = ""
    price: float = 0.0
    image_url: str = ""
    is_available: bool = True
    created_at: Optional[datetime] = None
    # Trường phụ trợ (không lưu DB) - tên danh mục để hiển thị
    category_name: str = ""


@dataclass
class Client:
    """Thực thể Khách hàng (thành viên)."""
    client_id: int = 0
    full_name: str = ""
    phone: str = ""
    email: str = ""
    loyalty_points: int = 0
    created_at: Optional[datetime] = None


@dataclass
class Booking:
    """
    Thực thể Đặt bàn.
    Status: confirmed | cancelled | completed | no_show
    """
    booking_id: int = 0
    table_id: int = 0
    client_id: Optional[int] = None
    user_id: int = 0
    guest_name: str = ""
    guest_phone: str = ""
    guest_count: int = 1
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    note: str = ""
    status: str = "confirmed"
    discount_percent: float = 0.0
    booking_code: str = ""
    created_at: Optional[datetime] = None
    # Trường phụ trợ
    table_number: int = 0
    table_area: str = ""
    user_name: str = ""     # Tên nhân viên lễ tân tạo đặt bàn


@dataclass
class Order:
    """
    Thực thể Phiếu gọi món (gắn với bàn, thuộc về 1 Bill).
    Status: active | completed | cancelled
    """
    order_id: int = 0
    bill_id: Optional[int] = None   # FK tới Bill (NULL khi chưa tạo hóa đơn)
    table_id: int = 0
    user_id: int = 0
    order_time: Optional[datetime] = None
    status: str = "active"
    note: str = ""
    # Trường phụ trợ
    table_number: int = 0
    waiter_name: str = ""
    items: List = field(default_factory=list)  # Danh sách OrderedDish


@dataclass
class OrderedDish:
    """
    Thực thể Chi tiết món đã gọi.
    cook_status: pending (Chờ CB) | cooking (Đang CB) | done (Hoàn thành) | cancelled (Hủy)
    """
    ordered_dish_id: int = 0
    order_id: int = 0
    dish_id: int = 0
    quantity: int = 1
    unit_price: float = 0.0
    note: str = ""
    cook_status: str = "pending"
    created_at: Optional[datetime] = None
    # Trường phụ trợ
    dish_name: str = ""
    table_number: int = 0


@dataclass
class Bill:
    """
    Thực thể Hóa đơn thanh toán (cha của nhiều Order).
    Status: unpaid | paid | cancelled
    payment_method: cash | card | transfer | e_wallet
    """
    bill_id: int = 0
    table_id: int = 0
    user_id: int = 0
    client_id: Optional[int] = None
    subtotal: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    tax_percent: float = 10.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    payment_method: str = "cash"
    status: str = "unpaid"
    note: str = ""
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    # Trường phụ trợ
    table_number: int = 0
    cashier_name: str = ""


@dataclass
class TableStat:
    """Thực thể Thống kê Doanh thu Bàn."""
    table_number: str = ""
    area: str = ""
    total_guests: int = 0
    total_revenue: float = 0.0

@dataclass
class DishStat:
    """Thực thể Thống kê Món ăn bán chạy."""
    dish_name: str = ""
    category_name: str = ""
    quantity_sold: int = 0
    revenue_contribution: float = 0.0

@dataclass
class ClientStat:
    """Thực thể Thống kê Khách hàng."""
    client_name: str = ""
    phone: str = ""
    total_spent: float = 0.0

@dataclass
class HourlyStat:
    """Thực thể Thống kê Khách theo khung giờ."""
    time_frame: str = ""
    guest_count: int = 0
    table_count: int = 0
    revenue: float = 0.0
