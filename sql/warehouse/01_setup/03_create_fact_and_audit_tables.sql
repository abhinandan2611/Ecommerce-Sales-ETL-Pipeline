/*
    FILE: 03_create_fact_and_audit_tables.sql
    PURPOSE:
        Create the sales fact table and warehouse ETL audit table.

    IMPORTANT:
        Run after the dimension tables have been created.
        This script does not populate either table.
*/

USE EcommerceDB;
GO

-- Fact table: one row per sales order.
IF OBJECT_ID('dw.fact_sales', 'U') IS NULL
BEGIN
    CREATE TABLE dw.fact_sales
    (
        sales_key BIGINT IDENTITY(1,1) PRIMARY KEY,
        order_id BIGINT NOT NULL UNIQUE,

        customer_key INT NOT NULL,
        product_key INT NOT NULL,
        date_key INT NOT NULL,
        geography_key INT NOT NULL,
        payment_method_key INT NOT NULL,
        order_status_key INT NOT NULL,

        quantity INT NOT NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        discount DECIMAL(5,4),
        shipping_cost DECIMAL(10,2),

        CONSTRAINT FK_fact_sales_customer
            FOREIGN KEY (customer_key)
            REFERENCES dw.dim_customer(customer_key),

        CONSTRAINT FK_fact_sales_product
            FOREIGN KEY (product_key)
            REFERENCES dw.dim_product(product_key),

        CONSTRAINT FK_fact_sales_date
            FOREIGN KEY (date_key)
            REFERENCES dw.dim_date(date_key),

        CONSTRAINT FK_fact_sales_geography
            FOREIGN KEY (geography_key)
            REFERENCES dw.dim_geography(geography_key),

        CONSTRAINT FK_fact_sales_payment_method
            FOREIGN KEY (payment_method_key)
            REFERENCES dw.dim_payment_method(payment_method_key),

        CONSTRAINT FK_fact_sales_order_status
            FOREIGN KEY (order_status_key)
            REFERENCES dw.dim_order_status(order_status_key)
    );
END;
GO

-- Audit table: one row per stored-procedure execution.
IF OBJECT_ID('dw.etl_audit_log', 'U') IS NULL
BEGIN
    CREATE TABLE dw.etl_audit_log
    (
        audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        pipeline_name NVARCHAR(100) NOT NULL,
        start_time DATETIME2 NOT NULL,
        end_time DATETIME2 NULL,
        source_records INT DEFAULT 0,
        inserted_records INT DEFAULT 0,
        failed_records INT DEFAULT 0,
        execution_status NVARCHAR(30) NOT NULL,
        error_message NVARCHAR(MAX) NULL
    );
END;
GO
