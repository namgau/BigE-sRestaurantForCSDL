"""
setup_database.py - Tự động tạo database RestaurantDB
=====================================================
Chạy script này một lần duy nhất để:
  1. Tạo database RestaurantDB (nếu chưa có)
  2. Tạo tất cả bảng, seed data, triggers, stored procedures

Cách dùng:
    python setup_database.py

Yêu cầu:
  - SQL Server đang chạy
  - Cấu hình server/instance đúng trong app_config.py
"""

import pyodbc
import os
import sys
import io

# Fix encoding tiếng Việt trên Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



def get_master_connection_string():
    """
    Tạo chuỗi kết nối tới database 'master' (không phải RestaurantDB).
    Cần kết nối vào master trước để có thể tạo database mới.
    """
    from app_config import SQL_SERVER_CONFIG
    cfg = SQL_SERVER_CONFIG

    if cfg.get('TRUSTED_CONNECTION', 'yes').lower() == 'yes':
        return (
            f"DRIVER={cfg['DRIVER']};"
            f"SERVER={cfg['SERVER']};"
            f"DATABASE=master;"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    else:
        return (
            f"DRIVER={cfg['DRIVER']};"
            f"SERVER={cfg['SERVER']};"
            f"DATABASE=master;"
            f"UID={cfg['UID']};"
            f"PWD={cfg['PWD']};"
            f"TrustServerCertificate=yes;"
        )


def run_sql_file(conn_str, sql_file_path):
    """
    Đọc file .sql và thực thi từng batch (phân tách bằng GO).
    pyodbc không hiểu từ khoá GO nên phải tách thủ công.
    """
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Tách theo GO (không phân biệt hoa thường, GO đứng riêng một dòng)
    import re
    batches = re.split(r'^\s*GO\s*$', sql_content, flags=re.IGNORECASE | re.MULTILINE)

    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()

    success_count = 0
    for i, batch in enumerate(batches):
        batch = batch.strip()
        if not batch:
            continue
        try:
            cursor.execute(batch)
            success_count += 1
        except pyodbc.Error as e:
            # Bỏ qua lỗi "object already exists" (chạy lại an toàn)
            error_code = e.args[0] if e.args else ''
            msg = str(e)
            if any(code in msg for code in ['2714', '1913', '2759', '2627', '2601']):
                # 2714: object already exists
                # 1913: constraint already exists
                # 2759: step already exists
                success_count += 1
                continue
            print(f"\n[!] Lỗi tại batch {i+1}:\n{batch[:120]}...\nError: {e}\n")

    conn.close()
    return success_count


def main():
    print("=" * 55)
    print("   Setup Database - Hệ thống Quản lý Nhà hàng")
    print("=" * 55)

    sql_file = os.path.join(os.path.dirname(__file__), 'database.sql')
    if not os.path.exists(sql_file):
        print(f"[✗] Không tìm thấy file: {sql_file}")
        sys.exit(1)

    # Bước 1: Kết nối thử
    try:
        from app_config import SQL_SERVER_CONFIG
        conn_str = get_master_connection_string()
        print(f"[→] Kết nối tới: {SQL_SERVER_CONFIG['SERVER']}")
        test_conn = pyodbc.connect(conn_str, timeout=5)
        test_conn.close()
        print("[✓] Kết nối SQL Server thành công!")
    except pyodbc.Error as e:
        print(f"[✗] Không thể kết nối SQL Server: {e}")
        print("\nKiểm tra lại:")
        print("  - SQL Server có đang chạy không?")
        print("  - Tên SERVER trong app_config.py có đúng không?")
        sys.exit(1)

    # Bước 2: Chạy database.sql
    print(f"[→] Đang chạy {os.path.basename(sql_file)} ...")
    count = run_sql_file(conn_str, sql_file)
    print(f"[✓] Hoàn tất! Đã thực thi {count} batch thành công.")

    # Bước 3: Kiểm tra kết quả
    try:
        from app_config import get_sql_connection_string
        conn = pyodbc.connect(get_sql_connection_string())
        tables = conn.execute(
            "SELECT name FROM sys.tables ORDER BY name"
        ).fetchall()
        triggers = conn.execute(
            "SELECT name FROM sys.triggers ORDER BY name"
        ).fetchall()
        procs = conn.execute(
            "SELECT name FROM sys.procedures WHERE name LIKE 'sp_%' ORDER BY name"
        ).fetchall()
        conn.close()

        print(f"\n[✓] Database 'RestaurantDB' đã sẵn sàng:")
        print(f"    • {len(tables)} bảng: {', '.join(r[0] for r in tables)}")
        print(f"    • {len(triggers)} trigger: {', '.join(r[0] for r in triggers)}")
        print(f"    • {len(procs)} stored procedure: {', '.join(r[0] for r in procs)}")
    except Exception as e:
        print(f"[!] Không thể kiểm tra kết quả: {e}")

    print("\n[✓] Chạy ứng dụng: python main_gui.py")
    print("=" * 55)


if __name__ == '__main__':
    main()
