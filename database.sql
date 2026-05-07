-- Tạo database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'RestaurantDB')
BEGIN
    CREATE DATABASE RestaurantDB;
END
GO

USE RestaurantDB;
GO

-- ============================================================
-- 1. BẢNG RESTAURANT - Thông tin nhà hàng
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Restaurant' AND xtype='U')
CREATE TABLE Restaurant (
    restaurant_id   INT IDENTITY(1,1) PRIMARY KEY,
    name            NVARCHAR(200)   NOT NULL,
    address         NVARCHAR(500)   NULL,
    phone           VARCHAR(20)     NULL,
    email           VARCHAR(100)    NULL,
    open_time       TIME            NULL,
    close_time      TIME            NULL,
    created_at      DATETIME        DEFAULT GETDATE()
);
GO

-- ============================================================
-- 2. BẢNG USER - Nhân viên / Người dùng hệ thống
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
CREATE TABLE Users (
    user_id         INT IDENTITY(1,1) PRIMARY KEY,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    full_name       NVARCHAR(100)   NOT NULL,
    position        VARCHAR(20)     NOT NULL 
                    CHECK (position IN ('manager','receptionist','waiter','chef')),
    phone           VARCHAR(20)     NULL,
    is_active       BIT             DEFAULT 1,
    created_at      DATETIME        DEFAULT GETDATE()
);
GO

-- ============================================================
-- 3. BẢNG TABLE - Bàn ăn
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tables' AND xtype='U')
CREATE TABLE Tables (
    table_id        INT IDENTITY(1,1) PRIMARY KEY,
    restaurant_id   INT             NOT NULL,
    table_number    INT             NOT NULL,
    capacity        INT             NOT NULL DEFAULT 4,
    area            NVARCHAR(50)    NULL,       -- Khu vực: Tầng 1, VIP, Sân vườn...
    status          VARCHAR(20)     DEFAULT 'available'
                    CHECK (status IN ('available','occupied','reserved','maintenance')),
    CONSTRAINT FK_Tables_Restaurant FOREIGN KEY (restaurant_id) 
        REFERENCES Restaurant(restaurant_id),
    CONSTRAINT UQ_Table_Number UNIQUE (restaurant_id, table_number)
);
GO

-- ============================================================
-- 4. BẢNG CATEGORY - Danh mục món ăn
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Category' AND xtype='U')
CREATE TABLE Category (
    category_id     INT IDENTITY(1,1) PRIMARY KEY,
    restaurant_id   INT             NOT NULL,
    name            NVARCHAR(100)   NOT NULL,
    description     NVARCHAR(500)   NULL,
    display_order   INT             DEFAULT 0,
    is_active       BIT             DEFAULT 1,
    CONSTRAINT FK_Category_Restaurant FOREIGN KEY (restaurant_id) 
        REFERENCES Restaurant(restaurant_id)
);
GO

-- ============================================================
-- 5. BẢNG DISH - Món ăn
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Dish' AND xtype='U')
CREATE TABLE Dish (
    dish_id         INT IDENTITY(1,1) PRIMARY KEY,
    category_id     INT             NOT NULL,
    name            NVARCHAR(200)   NOT NULL,
    description     NVARCHAR(500)   NULL,
    price           DECIMAL(12,2)   NOT NULL CHECK (price >= 0),
    image_url       VARCHAR(500)    NULL,
    is_available    BIT             DEFAULT 1,
    created_at      DATETIME        DEFAULT GETDATE(),
    CONSTRAINT FK_Dish_Category FOREIGN KEY (category_id) 
        REFERENCES Category(category_id)
);
GO

-- ============================================================
-- 6. BẢNG CLIENT - Khách hàng (thành viên)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Client' AND xtype='U')
CREATE TABLE Client (
    client_id       INT IDENTITY(1,1) PRIMARY KEY,
    full_name       NVARCHAR(100)   NOT NULL,
    phone           VARCHAR(20)     NULL,
    email           VARCHAR(100)    NULL,
    loyalty_points  INT             DEFAULT 0,
    created_at      DATETIME        DEFAULT GETDATE()
);
GO

-- ============================================================
-- 7. BẢNG BOOKING - Đặt bàn
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Booking' AND xtype='U')
CREATE TABLE Booking (
    booking_id      INT IDENTITY(1,1) PRIMARY KEY,
    table_id        INT             NOT NULL,
    client_id       INT             NULL,
    user_id         INT             NOT NULL,       -- Nhân viên lễ tân tạo
    guest_name      NVARCHAR(100)   NOT NULL,
    guest_phone     VARCHAR(20)     NULL,
    guest_count     INT             NOT NULL DEFAULT 1,
    booking_date    DATE            NOT NULL,
    booking_time    TIME            NOT NULL,
    note            NVARCHAR(500)   NULL,
    discount_percent DECIMAL(5,2)   DEFAULT 0,
    booking_code    VARCHAR(20)     NULL,
    status          VARCHAR(20)     DEFAULT 'confirmed'
                    CHECK (status IN ('confirmed','cancelled','completed','no_show')),
    created_at      DATETIME        DEFAULT GETDATE(),
    CONSTRAINT FK_Booking_Table FOREIGN KEY (table_id) 
        REFERENCES Tables(table_id),
    CONSTRAINT FK_Booking_Client FOREIGN KEY (client_id) 
        REFERENCES Client(client_id),
    CONSTRAINT FK_Booking_User FOREIGN KEY (user_id) 
        REFERENCES Users(user_id)
);
GO

-- ============================================================
-- 8. BẢNG BILL - Hóa đơn thanh toán (tạo trước Orders vì Orders.bill_id FK tới Bill)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Bill' AND xtype='U')
CREATE TABLE Bill (
    bill_id         INT IDENTITY(1,1) PRIMARY KEY,
    table_id        INT             NOT NULL,
    user_id         INT             NOT NULL,       -- Thu ngân xử lý
    client_id       INT             NULL,
    subtotal        DECIMAL(14,2)   NOT NULL DEFAULT 0,
    discount_percent DECIMAL(5,2)   DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discount_amount DECIMAL(14,2)   DEFAULT 0,
    tax_percent     DECIMAL(5,2)    DEFAULT 10,     -- VAT 10%
    tax_amount      DECIMAL(14,2)   DEFAULT 0,
    total_amount    DECIMAL(14,2)   NOT NULL DEFAULT 0,
    payment_method  VARCHAR(20)     DEFAULT 'cash'
                    CHECK (payment_method IN ('cash','card','transfer','e_wallet')),
    status          VARCHAR(20)     DEFAULT 'unpaid'
                    CHECK (status IN ('unpaid','paid','cancelled')),
    note            NVARCHAR(500)   NULL,
    created_at      DATETIME        DEFAULT GETDATE(),
    paid_at         DATETIME        NULL,
    CONSTRAINT FK_Bill_Table FOREIGN KEY (table_id) 
        REFERENCES Tables(table_id),
    CONSTRAINT FK_Bill_User FOREIGN KEY (user_id) 
        REFERENCES Users(user_id),
    CONSTRAINT FK_Bill_Client FOREIGN KEY (client_id) 
        REFERENCES Client(client_id)
);
GO

-- ============================================================
-- 9. BẢNG ORDER - Phiếu gọi món (gắn với bàn, thuộc về 1 Bill)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Orders' AND xtype='U')
CREATE TABLE Orders (
    order_id        INT IDENTITY(1,1) PRIMARY KEY,
    bill_id         INT             NULL,           -- FK tới Bill (NULL khi chưa thanh toán)
    table_id        INT             NOT NULL,
    user_id         INT             NOT NULL,       -- Nhân viên phục vụ tạo
    order_time      DATETIME        DEFAULT GETDATE(),
    status          VARCHAR(20)     DEFAULT 'active'
                    CHECK (status IN ('active','completed','cancelled')),
    note            NVARCHAR(500)   NULL,
    CONSTRAINT FK_Order_Bill FOREIGN KEY (bill_id)
        REFERENCES Bill(bill_id),
    CONSTRAINT FK_Order_Table FOREIGN KEY (table_id) 
        REFERENCES Tables(table_id),
    CONSTRAINT FK_Order_User FOREIGN KEY (user_id) 
        REFERENCES Users(user_id)
);
GO

-- ============================================================
-- 10. BẢNG ORDERED_DISH - Chi tiết món đã gọi
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='OrderedDish' AND xtype='U')
CREATE TABLE OrderedDish (
    ordered_dish_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT             NOT NULL,
    dish_id         INT             NOT NULL,
    quantity        INT             NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price      DECIMAL(12,2)   NOT NULL,       -- Giá tại thời điểm gọi
    note            NVARCHAR(200)   NULL,            -- Ghi chú: ít cay, không hành...
    cook_status     VARCHAR(20)     DEFAULT 'pending'
                    CHECK (cook_status IN ('pending','cooking','done','cancelled')),
    created_at      DATETIME        DEFAULT GETDATE(),
    CONSTRAINT FK_OD_Order FOREIGN KEY (order_id) 
        REFERENCES Orders(order_id),
    CONSTRAINT FK_OD_Dish FOREIGN KEY (dish_id) 
        REFERENCES Dish(dish_id)
);
GO

-- ============================================================
-- DỮ LIỆU MẪU (SEED DATA)
-- ============================================================

-- Nhà hàng mẫu
SET IDENTITY_INSERT Restaurant ON;
INSERT INTO Restaurant (restaurant_id, name, address, phone, email, open_time, close_time)
VALUES (1, N'Epstein''s Restaurant', N'123 Nguyễn Huệ, Quận 1, TP.HCM', 
        '0901234567', 'contact@phongvi.vn', '08:00', '22:00');
SET IDENTITY_INSERT Restaurant OFF;
GO

-- Người dùng mẫu (password: 123456 -> hash đơn giản cho demo)
SET IDENTITY_INSERT Users ON;
INSERT INTO Users (user_id, username, password_hash, full_name, position, phone) VALUES
(1, 'admin',     'e10adc3949ba59abbe56e057f20f883e', N'Nguyễn Văn Quản Lý',   'manager',      '0900000001'),
(2, 'letan01',   'e10adc3949ba59abbe56e057f20f883e', N'Trần Thị Lễ Tân',      'receptionist', '0900000002'),
(3, 'waiter01',  'e10adc3949ba59abbe56e057f20f883e', N'Lê Văn Phục Vụ',       'waiter',       '0900000003'),
(4, 'chef01',    'e10adc3949ba59abbe56e057f20f883e', N'Phạm Văn Bếp Trưởng',  'chef',         '0900000004'),
(5, 'cashier01', 'e10adc3949ba59abbe56e057f20f883e', N'Hoàng Thị Thu Ngân',   'receptionist',      '0900000005');
SET IDENTITY_INSERT Users OFF;
GO

-- Bàn ăn mẫu (15 bàn)
SET IDENTITY_INSERT Tables ON;
INSERT INTO Tables (table_id, restaurant_id, table_number, capacity, area, status) VALUES
(1,  1, 1,  2, N'Tầng 1',     'available'),
(2,  1, 2,  2, N'Tầng 1',     'available'),
(3,  1, 3,  4, N'Tầng 1',     'available'),
(4,  1, 4,  4, N'Tầng 1',     'available'),
(5,  1, 5,  4, N'Tầng 1',     'available'),
(6,  1, 6,  6, N'Tầng 1',     'available'),
(7,  1, 7,  6, N'Tầng 2',     'available'),
(8,  1, 8,  4, N'Tầng 2',     'available'),
(9,  1, 9,  4, N'Tầng 2',     'available'),
(10, 1, 10, 8, N'Tầng 2',     'available'),
(11, 1, 11, 4, N'VIP',        'available'),
(12, 1, 12, 6, N'VIP',        'available'),
(13, 1, 13, 8, N'VIP',        'available'),
(14, 1, 14, 10, N'Sân vườn',  'available'),
(15, 1, 15, 12, N'Sân vườn',  'available');
SET IDENTITY_INSERT Tables OFF;
GO

-- Danh mục món ăn
SET IDENTITY_INSERT Category ON;
INSERT INTO Category (category_id, restaurant_id, name, description, display_order) VALUES
(1, 1, N'Khai vị',       N'Các món khai vị',          1),
(2, 1, N'Món chính',     N'Các món ăn chính',         2),
(3, 1, N'Hải sản',       N'Các món hải sản tươi sống', 3),
(4, 1, N'Lẩu',           N'Các loại lẩu',             4),
(5, 1, N'Tráng miệng',   N'Các món tráng miệng',      5),
(6, 1, N'Đồ uống',       N'Nước giải khát và đồ uống', 6);
SET IDENTITY_INSERT Category OFF;
GO

-- Món ăn mẫu
SET IDENTITY_INSERT Dish ON;
INSERT INTO Dish (dish_id, category_id, name, price, description) VALUES
-- Khai vị
(1,  1, N'Gỏi cuốn tôm thịt',       55000,  N'6 cuốn, kèm nước chấm đặc biệt'),
(2,  1, N'Chả giò truyền thống',      65000,  N'6 cuốn chả giò giòn rụm'),
(3,  1, N'Salad trộn dầu giấm',       45000,  N'Rau tươi trộn sốt dầu giấm'),
-- Món chính
(4,  2, N'Cơm chiên Dương Châu',      75000,  N'Cơm chiên với tôm, lạp xưởng, trứng'),
(5,  2, N'Bò lúc lắc khoai tây',      125000, N'Thịt bò Úc xào khoai tây chiên'),
(6,  2, N'Sườn non nướng mật ong',    135000, N'Sườn heo non ướp mật ong nướng than'),
(7,  2, N'Gà nướng muối ớt',          155000, N'Nửa con gà nướng muối ớt xanh'),
-- Hải sản
(8,  3, N'Tôm sú nướng muối ớt',      185000, N'Tôm sú size lớn nướng'),
(9,  3, N'Cua rang me',               250000, N'Cua biển rang sốt me chua ngọt'),
(10, 3, N'Mực chiên giòn',            120000, N'Mực ống chiên bột giòn'),
-- Lẩu
(11, 4, N'Lẩu Thái Tom Yum',          280000, N'Lẩu chua cay kiểu Thái, phần 2-3 người'),
(12, 4, N'Lẩu nấm hải sản',           320000, N'Lẩu nấm với hải sản tổng hợp'),
-- Tráng miệng
(13, 5, N'Chè khúc bạch',             35000,  N'Chè khúc bạch mát lạnh'),
(14, 5, N'Kem dừa tươi',              40000,  N'Kem dừa tươi trong trái dừa'),
-- Đồ uống
(15, 6, N'Trà đào cam sả',            35000,  N'Trà đào cam sả tươi mát'),
(16, 6, N'Cà phê sữa đá',            29000,  N'Cà phê phin truyền thống'),
(17, 6, N'Nước ép cam tươi',          39000,  N'Cam vắt tươi 100%'),
(18, 6, N'Bia Tiger (chai)',          25000,  N'Bia Tiger 330ml'),
(19, 6, N'Coca-Cola',                 15000,  N'Coca-Cola lon 330ml'),
(20, 6, N'Nước suối',                 10000,  N'Nước suối đóng chai 500ml');
SET IDENTITY_INSERT Dish OFF;
GO

-- Khách hàng mẫu
SET IDENTITY_INSERT Client ON;
INSERT INTO Client (client_id, full_name, phone, email, loyalty_points) VALUES
(1, N'Nguyễn Văn An',    '0911111111', 'an.nguyen@gmail.com',   150),
(2, N'Trần Bình An',    '0922222222', 'binh.tran.an@gmail.com',   80),
(3, N'Lê Văn Cường',   '0933333333', 'cuong.le@gmail.com',    200);
SET IDENTITY_INSERT Client OFF;
GO

PRINT N'=== Database RestaurantDB đã được tạo thành công! ===';
GO

-- ============================================================
-- 12. CÁC BẢNG THỐNG KÊ (STATISTICS) - CẬP NHẬT THEO ERD
-- ============================================================

-- Thống kê nhà hàng theo ngày
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RestaurantStat' AND xtype='U')
CREATE TABLE RestaurantStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    restaurant_id   INT             NOT NULL,
    day             DATE            NOT NULL,
    revenue         DECIMAL(14,2)   DEFAULT 0,
    fill_rate       FLOAT           DEFAULT 0, -- Tỷ lệ lấp đầy bàn
    total_bills     INT             DEFAULT 0,
    CONSTRAINT FK_RestStat_Rest FOREIGN KEY (restaurant_id) REFERENCES Restaurant(restaurant_id)
);
GO

-- Thống kê theo bàn
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TableStat' AND xtype='U')
CREATE TABLE TableStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    table_id        INT             NOT NULL,
    day             DATE            NOT NULL,
    income          DECIMAL(14,2)   DEFAULT 0,
    total_guests    INT             DEFAULT 0,
    CONSTRAINT FK_TblStat_Tbl FOREIGN KEY (table_id) REFERENCES Tables(table_id)
);
GO

-- Thống kê theo khách hàng
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ClientStat' AND xtype='U')
CREATE TABLE ClientStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    client_id       INT             NOT NULL,
    day             DATE            NOT NULL,
    payment         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_CliStat_Cli FOREIGN KEY (client_id) REFERENCES Client(client_id)
);
GO

-- Thống kê món ăn bán chạy
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DishStat' AND xtype='U')
CREATE TABLE DishStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    dish_id         INT             NOT NULL,
    day             DATE            NOT NULL,
    total_sold      INT             DEFAULT 0,
    revenue         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_DishStat_Dish FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
);
GO

-- Thống kê chi tiết thu nhập (IncomeStat)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='IncomeStat' AND xtype='U')
CREATE TABLE IncomeStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    bill_id         INT             NOT NULL,
    period          VARCHAR(20)     NULL, -- Sáng/Chiều/Tối hoặc Giờ
    revenue         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_IncStat_Bill FOREIGN KEY (bill_id) REFERENCES Bill(bill_id)
);
GO


USE RestaurantDB;
GO

-- Thống kê nhà hàng theo ngày
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RestaurantStat' AND xtype='U')
CREATE TABLE RestaurantStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    restaurant_id   INT             NOT NULL,
    day             DATE            NOT NULL,
    revenue         DECIMAL(14,2)   DEFAULT 0,
    fill_rate       FLOAT           DEFAULT 0,
    total_bills     INT             DEFAULT 0,
    CONSTRAINT FK_RestStat_Rest FOREIGN KEY (restaurant_id) REFERENCES Restaurant(restaurant_id)
);
GO

-- Thống kê theo bàn
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TableStat' AND xtype='U')
CREATE TABLE TableStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    table_id        INT             NOT NULL,
    day             DATE            NOT NULL,
    income          DECIMAL(14,2)   DEFAULT 0,
    total_guests    INT             DEFAULT 0,
    CONSTRAINT FK_TblStat_Tbl FOREIGN KEY (table_id) REFERENCES Tables(table_id)
);
GO

-- Thống kê theo khách hàng
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ClientStat' AND xtype='U')
CREATE TABLE ClientStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    client_id       INT             NOT NULL,
    day             DATE            NOT NULL,
    payment         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_CliStat_Cli FOREIGN KEY (client_id) REFERENCES Client(client_id)
);
GO

-- Thống kê món ăn bán chạy
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DishStat' AND xtype='U')
CREATE TABLE DishStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    dish_id         INT             NOT NULL,
    day             DATE            NOT NULL,
    total_sold      INT             DEFAULT 0,
    revenue         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_DishStat_Dish FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
);
GO

-- Thống kê chi tiết thu nhập
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='IncomeStat' AND xtype='U')
CREATE TABLE IncomeStat (
    stat_id         INT IDENTITY(1,1) PRIMARY KEY,
    bill_id         INT             NOT NULL,
    period          VARCHAR(20)     NULL,
    revenue         DECIMAL(14,2)   DEFAULT 0,
    CONSTRAINT FK_IncStat_Bill FOREIGN KEY (bill_id) REFERENCES Bill(bill_id)
);
GO

-- ============================================================
-- 13. PROCEDURE: Lấy báo cáo doanh thu theo ngày
-- ============================================================
GO
CREATE PROCEDURE sp_GetDailyRevenueSummary
    @QueryDate DATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Lấy tổng doanh thu và số lượng hóa đơn
    SELECT 
        COUNT(bill_id) AS TotalBills,
        ISNULL(SUM(total_amount), 0) AS TotalRevenue,
        ISNULL(SUM(discount_amount), 0) AS TotalDiscount
    FROM Bill
    WHERE CAST(paid_at AS DATE) = @QueryDate 
      AND status = 'paid';

    -- Lấy danh sách các món ăn bán chạy trong ngày
    SELECT 
        d.name AS DishName,
        SUM(od.quantity) AS TotalQuantitySold,
        SUM(od.quantity * od.unit_price) AS TotalDishRevenue
    FROM Bill b
    JOIN Orders o ON b.bill_id = o.bill_id
    JOIN OrderedDish od ON o.order_id = od.order_id
    JOIN Dish d ON od.dish_id = d.dish_id
    WHERE CAST(b.paid_at AS DATE) = @QueryDate 
      AND b.status = 'paid'
    GROUP BY d.name
    ORDER BY TotalQuantitySold DESC;
END;
GO

-- ============================================================
-- 14. TRIGGER: Ghi log khi trạng thái hóa đơn (Bill) thay đổi
-- ============================================================
-- Tạo bảng Audit_BillLog trước để lưu trữ lịch sử
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Audit_BillLog' AND xtype='U')
CREATE TABLE Audit_BillLog (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    bill_id INT,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_at DATETIME DEFAULT GETDATE(),
    changed_by NVARCHAR(100) DEFAULT SYSTEM_USER
);
GO

CREATE TRIGGER trg_AuditBillStatusChanges
ON Bill
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Kiểm tra nếu cột status có sự thay đổi
    IF UPDATE(status)
    BEGIN
        INSERT INTO Audit_BillLog (bill_id, old_status, new_status)
        SELECT 
            i.bill_id,
            d.status AS old_status,
            i.status AS new_status
        FROM inserted i
        JOIN deleted d ON i.bill_id = d.bill_id
        WHERE i.status <> d.status; -- Chỉ ghi log nếu trạng thái thực sự khác biệt
    END
END;
GO

-- ============================================================
-- 15. TRANSACTION: Xóa/Hủy một đặt bàn (Booking) an toàn
-- ============================================================
GO
CREATE PROCEDURE sp_CancelBookingTransaction
    @BookingID INT,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @TableID INT;
        DECLARE @CurrentStatus VARCHAR(20);

        -- Lấy thông tin Booking
        SELECT @TableID = table_id, @CurrentStatus = status 
        FROM Booking 
        WHERE booking_id = @BookingID;

        -- Kiểm tra nếu Booking tồn tại và chưa bị hủy
        IF @CurrentStatus = 'confirmed'
        BEGIN
            -- 1. Cập nhật trạng thái Booking thành 'cancelled'
            UPDATE Booking
            SET status = 'cancelled',
                note = ISNULL(note, '') + N' (Đã hủy bởi UserID: ' + CAST(@UserID AS NVARCHAR) + ')'
            WHERE booking_id = @BookingID;

            -- 2. Giải phóng Bàn (cập nhật status thành 'available')
            UPDATE Tables
            SET status = 'available'
            WHERE table_id = @TableID AND status = 'reserved';
        END
        ELSE
        BEGIN
            -- Nếu đã hủy hoặc trạng thái khác, ném lỗi để rollback
            THROW 50000, N'Booking không ở trạng thái có thể hủy.', 1;
        END

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        -- Nếu có bất kỳ lỗi nào xảy ra trong quá trình thực thi, hoàn tác tất cả
        IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRANSACTION;
        END

        -- Ném lỗi ra bên ngoài
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR (@ErrorMessage, 16, 1);
    END CATCH
END;
GO