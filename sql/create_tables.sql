
USE EcommerceDB;
GO

-- Create the main sales table
IF OBJECT_ID('dbo.sales_orders', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.sales_orders
    (
        order_id BIGINT NOT NULL PRIMARY KEY,
        customer_id BIGINT NULL,
        product_id BIGINT NOT NULL,
        order_date DATE NOT NULL,
        product_category NVARCHAR(100) NULL,
        product_name NVARCHAR(255) NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(12, 2) NOT NULL,
        discount DECIMAL(5, 4) NULL,
        shipping_cost DECIMAL(10, 2) NULL,
        region NVARCHAR(100) NULL,
        country NVARCHAR(100) NULL,
        payment_method NVARCHAR(100) NULL,
        order_status NVARCHAR(50) NULL
    );
END;
GO

-- Create a separate table for quarantined records
IF OBJECT_ID('dbo.quarantined_sales_orders', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.quarantined_sales_orders
    (
        order_id BIGINT NOT NULL,
        customer_id BIGINT NULL,
        product_id BIGINT NOT NULL,
        order_date DATE NOT NULL,
        product_category NVARCHAR(100) NULL,
        product_name NVARCHAR(255) NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(12, 2) NULL,
        discount DECIMAL(5, 4) NULL,
        shipping_cost DECIMAL(10, 2) NULL,
        region NVARCHAR(100) NULL,
        country NVARCHAR(100) NULL,
        payment_method NVARCHAR(100) NULL,
        order_status NVARCHAR(50) NULL,
        quarantine_reason NVARCHAR(500) NULL
    );
END;
GO
