# ============================================================
# redis_cache.py - Lớp Cache với Redis
# ============================================================
# Mục đích: Lưu trữ trạng thái bàn và kết quả thống kê vào Redis
# để giảm tải query SQL Server, cập nhật tức thì cho các bộ phận.
# ============================================================
import json
import redis
from app_config import REDIS_CONFIG, REDIS_KEYS, APP_CONFIG


class RedisCache:
    """
    Quản lý cache Redis cho hệ thống nhà hàng.
    - Trạng thái bàn: cache để lễ tân/waiter/thu ngân xem nhanh.
    - Doanh thu: cache kết quả thống kê tránh tính toán lại.
    """

    def __init__(self):
        self.enabled = True
        try:
            # Khởi tạo kết nối Redis
            self.client = redis.Redis(
                host=REDIS_CONFIG['HOST'],
                port=REDIS_CONFIG['PORT'],
                db=REDIS_CONFIG['DB'],
                password=REDIS_CONFIG['PASSWORD'],
                decode_responses=REDIS_CONFIG['DECODE_RESPONSES'],
                socket_timeout=REDIS_CONFIG['SOCKET_TIMEOUT']
            )
            # Kiểm tra kết nối
            self.client.ping()
            print("[Redis] Kết nối Redis thành công!")
        except redis.ConnectionError:
            # Nếu Redis không chạy, hệ thống vẫn hoạt động bình thường
            # chỉ không có cache -> query trực tiếp SQL Server
            print("[Redis] Không thể kết nối Redis. Hệ thống sẽ chạy không cache.")
            self.enabled = False

    def is_available(self):
        """Kiểm tra Redis có sẵn không."""
        return self.enabled

    # ==========================================================
    # CACHE TRẠNG THÁI BÀN
    # ==========================================================
    # Lưu trạng thái từng bàn vào Redis với key pattern:
    # restaurant:{rid}:table:{tid}:status -> "available" | "occupied" | ...
    # TTL: 5 phút (300s) - tự hết hạn nếu không refresh.
    # ==========================================================

    def set_table_status(self, restaurant_id, table_id, status):
        """
        Cập nhật trạng thái bàn vào Redis.
        Được gọi mỗi khi trạng thái bàn thay đổi (đặt bàn, mở bàn, thanh toán).
        """
        if not self.enabled:
            return
        key = REDIS_KEYS['TABLE_STATUS'].format(rid=restaurant_id, tid=table_id)
        ttl = APP_CONFIG['CACHE_TTL_TABLE_STATUS']
        # Lưu trạng thái với TTL để tự động hết hạn
        self.client.setex(key, ttl, status)

    def get_table_status(self, restaurant_id, table_id):
        """
        Đọc trạng thái bàn từ Redis (nhanh hơn query SQL Server).
        Trả về None nếu cache miss -> cần query SQL Server.
        """
        if not self.enabled:
            return None
        key = REDIS_KEYS['TABLE_STATUS'].format(rid=restaurant_id, tid=table_id)
        return self.client.get(key)

    def set_all_tables(self, restaurant_id, tables_data):
        """
        Cache toàn bộ danh sách bàn (dạng JSON).
        Gọi khi khởi động app hoặc khi có thay đổi lớn.
        tables_data: list of dict [{table_id, table_number, status, ...}, ...]
        """
        if not self.enabled:
            return
        key = REDIS_KEYS['ALL_TABLES'].format(rid=restaurant_id)
        ttl = APP_CONFIG['CACHE_TTL_TABLE_STATUS']
        self.client.setex(key, ttl, json.dumps(tables_data, ensure_ascii=False))

    def get_all_tables(self, restaurant_id):
        """
        Lấy danh sách bàn từ cache.
        Trả về list of dict hoặc None nếu cache miss.
        """
        if not self.enabled:
            return None
        key = REDIS_KEYS['ALL_TABLES'].format(rid=restaurant_id)
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def invalidate_tables(self, restaurant_id):
        """Xóa cache bàn khi có thay đổi (buộc query lại SQL Server)."""
        if not self.enabled:
            return
        key = REDIS_KEYS['ALL_TABLES'].format(rid=restaurant_id)
        self.client.delete(key)

    # ==========================================================
    # CACHE DOANH THU
    # ==========================================================
    # Kết quả thống kê doanh thu được cache với TTL 10 phút.
    # Khi thu ngân thanh toán hóa đơn, cache doanh thu ngày đó bị xóa
    # để lần xem tiếp theo sẽ tính toán lại cho chính xác.
    # ==========================================================

    def set_revenue_daily(self, restaurant_id, date_str, data):
        """Cache kết quả doanh thu ngày."""
        if not self.enabled:
            return
        key = REDIS_KEYS['REVENUE_DAILY'].format(rid=restaurant_id, date=date_str)
        ttl = APP_CONFIG['CACHE_TTL_REVENUE_REPORT']
        self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))

    def get_revenue_daily(self, restaurant_id, date_str):
        """Lấy doanh thu ngày từ cache. None nếu miss."""
        if not self.enabled:
            return None
        key = REDIS_KEYS['REVENUE_DAILY'].format(rid=restaurant_id, date=date_str)
        data = self.client.get(key)
        return json.loads(data) if data else None

    def invalidate_revenue(self, restaurant_id, date_str):
        """Xóa cache doanh thu khi có thanh toán mới."""
        if not self.enabled:
            return
        key = REDIS_KEYS['REVENUE_DAILY'].format(rid=restaurant_id, date=date_str)
        self.client.delete(key)

    def set_revenue_monthly(self, restaurant_id, month_str, data):
        """Cache kết quả doanh thu tháng."""
        if not self.enabled:
            return
        key = REDIS_KEYS['REVENUE_MONTHLY'].format(rid=restaurant_id, month=month_str)
        ttl = APP_CONFIG['CACHE_TTL_REVENUE_REPORT']
        self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))

    def get_revenue_monthly(self, restaurant_id, month_str):
        """Lấy doanh thu tháng từ cache."""
        if not self.enabled:
            return None
        key = REDIS_KEYS['REVENUE_MONTHLY'].format(rid=restaurant_id, month=month_str)
        data = self.client.get(key)
        return json.loads(data) if data else None

    # ==========================================================
    # CACHE KITCHEN QUEUE
    # ==========================================================

    def set_kitchen_queue(self, restaurant_id, queue_data):
        """Cache danh sách món chờ chế biến."""
        if not self.enabled:
            return
        key = REDIS_KEYS['KITCHEN_QUEUE'].format(rid=restaurant_id)
        self.client.setex(key, 60, json.dumps(queue_data, ensure_ascii=False))

    def get_kitchen_queue(self, restaurant_id):
        """Lấy danh sách món chờ chế biến từ cache."""
        if not self.enabled:
            return None
        key = REDIS_KEYS['KITCHEN_QUEUE'].format(rid=restaurant_id)
        data = self.client.get(key)
        return json.loads(data) if data else None

    def invalidate_kitchen(self, restaurant_id):
        """Xóa cache bếp khi có thay đổi trạng thái món."""
        if not self.enabled:
            return
        key = REDIS_KEYS['KITCHEN_QUEUE'].format(rid=restaurant_id)
        self.client.delete(key)

    # ==========================================================
    # CACHE THỐNG KÊ (GENERAL STATS)
    # ==========================================================
    def set_report_stats(self, restaurant_id, stat_type, params, data):
        """
        Cache kết quả báo cáo thống kê bất kỳ.
        stat_type: string (e.g., 'table_revenue', 'best_sellers')
        params: dict (chứa ngày từ/đến để tạo key duy nhất)
        """
        if not self.enabled: return
        # Tạo key duy nhất dựa trên tham số
        param_str = "-".join([f"{k}:{v}" for k, v in sorted(params.items())])
        key = f"restaurant:{restaurant_id}:report:{stat_type}:{param_str}"
        ttl = 600 # 10 phút
        self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))

    def get_report_stats(self, restaurant_id, stat_type, params):
        """Lấy báo cáo từ cache."""
        if not self.enabled: return None
        param_str = "-".join([f"{k}:{v}" for k, v in sorted(params.items())])
        key = f"restaurant:{restaurant_id}:report:{stat_type}:{param_str}"
        data = self.client.get(key)
        return json.loads(data) if data else None

    def invalidate_reports(self, restaurant_id):
        """Xóa tất cả cache báo cáo của nhà hàng khi có thay đổi dữ liệu (thanh toán)."""
        if not self.enabled: return
        pattern = f"restaurant:{restaurant_id}:report:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
