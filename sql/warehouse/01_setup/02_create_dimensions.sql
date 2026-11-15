/*
    FILE: 02_create_dimensions.sql
    PURPOSE:
        Create the six dimension tables used by the ecommerce star schema.

    IMPORTANT:
        This is a setup script. Do not run it against a database where these
        tables already exist. It is provided to make the project reproducible.
*/

USE EcommerceDB;
GO

-- Customer dimension: one row per customer ID.
IF OBJECT_ID('dw.dim_customer', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_customer
    (
        customer_key INT IDENTITY(1,1) PRIMARY KEY,
        customer_id BIGINT NOT NULL UNIQUE
    );
END;
GO

-- Product dimension: one row per product ID.
IF OBJECT_ID('dw.dim_product', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_product
    (
        product_key INT IDENTITY(1,1) PRIMARY KEY,
        product_id BIGINT NOT NULL UNIQUE,
        product_name NVARCHAR(255),
        product_category NVARCHAR(100)
    );
END;
GO

-- Date dimension: date_key uses YYYYMMDD format.
IF OBJECT_ID('dw.dim_date', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_date
    (
        date_key INT PRIMARY KEY,
        full_date DATE NOT NULL UNIQUE,
        day_number INT,
        day_name NVARCHAR(20),
        month_number INT,
        month_name NVARCHAR(20),
        quarter_number INT,
        year_number INT,
        week_number INT
    );
END;
GO

-- Geography dimension: one row per region/country combination.
IF OBJECT_ID('dw.dim_geography', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_geography
    (
        geography_key INT IDENTITY(1,1) PRIMARY KEY,
        region NVARCHAR(100),
        country NVARCHAR(100)
    );
END;
GO

-- Payment method dimension.
IF OBJECT_ID('dw.dim_payment_method', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_payment_method
    (
        payment_method_key INT IDENTITY(1,1) PRIMARY KEY,
        payment_method NVARCHAR(100) NOT NULL UNIQUE
    );
END;
GO

-- Order status dimension.
IF OBJECT_ID('dw.dim_order_status', 'U') IS NULL
BEGIN
    CREATE TABLE dw.dim_order_status
    (
        order_status_key INT IDENTITY(1,1) PRIMARY KEY,
        order_status NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO
