# ============================================================
# app_config.py - Cấu hình kết nối SQL Server và Redis
# Hệ thống Quản lý Nhà hàng
# ============================================================

# ----------------------------------------------------------
# CẤU HÌNH SQL SERVER
# ----------------------------------------------------------
# Sử dụng ODBC Driver để kết nối Python với SQL Server.
# - DRIVER: Tên driver ODBC đã cài đặt trên máy.
# - SERVER: Tên instance SQL Server (mặc định: localhost\SQLEXPRESS).
# - DATABASE: Tên database đã tạo bằng file database.sql.
# - Trusted_Connection: 'yes' nếu dùng Windows Authentication.
# ----------------------------------------------------------

SQL_SERVER_CONFIG = {
    'DRIVER': '{ODBC Driver 17 for SQL Server}',
    'SERVER': r'localhost\CLCCSDLPTNHOM4',
    'DATABASE': 'RestaurantDB',                       # Tên database 
    'UID': '',                                   # Để trống nếu dùng Windows Auth
    'PWD': '',                                   # Để trống nếu dùng Windows Auth
    'TRUSTED_CONNECTION': 'yes' 
}

def get_sql_connection_string():
    """
    Tạo chuỗi kết nối ODBC từ cấu hình.
    Hỗ trợ cả Windows Authentication và SQL Server Authentication.
    """
    config = SQL_SERVER_CONFIG
    if config.get('TRUSTED_CONNECTION', 'yes').lower() == 'yes':
        return (
            f"DRIVER={config['DRIVER']};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    else:
        return (
            f"DRIVER={config['DRIVER']};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"UID={config['UID']};"
            f"PWD={config['PWD']};"
            f"TrustServerCertificate=yes;"
        )


# ----------------------------------------------------------
# CẤU HÌNH REDIS
# ----------------------------------------------------------
# Redis được sử dụng để cache:
# 1. Trạng thái bàn hiện tại (available/occupied/reserved)
#    -> Giảm tải query SQL Server cho các thao tác kiểm tra bàn trống.
# 2. Kết quả thống kê doanh thu
#    -> Tránh tính toán lại khi xem báo cáo nhiều lần.
# ----------------------------------------------------------

REDIS_CONFIG = {
    'HOST': 'localhost',
    'PORT': 6379,
    'DB': 0,                # Sử dụng database 0 của Redis
    'PASSWORD': None,       # Không password cho môi trường local
    'DECODE_RESPONSES': True,  # Tự động decode bytes -> str
    'SOCKET_TIMEOUT': 5,      # Timeout kết nối 5 giây
}

# ----------------------------------------------------------
# CẤU HÌNH ỨNG DỤNG
# ----------------------------------------------------------

APP_CONFIG = {
    'RESTAURANT_ID': 1,         # ID nhà hàng mặc định
    'APP_TITLE': "Hệ thống Quản lý Nhà hàng - Epstein's",
    'VERSION': '1.0.0',
    'DEFAULT_TAX_PERCENT': 10,  # VAT 10%
    'CACHE_TTL_TABLE_STATUS': 300,      # Cache trạng thái bàn: 5 phút
    'CACHE_TTL_REVENUE_REPORT': 600,    # Cache báo cáo doanh thu: 10 phút
}

# ----------------------------------------------------------
# KEY PATTERN CHO REDIS
# ----------------------------------------------------------
# Định nghĩa các mẫu key để đồng nhất cách lưu trữ trên Redis.
# ----------------------------------------------------------

REDIS_KEYS = {
    'TABLE_STATUS': 'restaurant:{rid}:table:{tid}:status',
    'ALL_TABLES': 'restaurant:{rid}:tables:all',
    'REVENUE_DAILY': 'restaurant:{rid}:revenue:daily:{date}',
    'REVENUE_MONTHLY': 'restaurant:{rid}:revenue:monthly:{month}',
    'KITCHEN_QUEUE': 'restaurant:{rid}:kitchen:queue',
    'ACTIVE_ORDERS': 'restaurant:{rid}:active_orders',
}
