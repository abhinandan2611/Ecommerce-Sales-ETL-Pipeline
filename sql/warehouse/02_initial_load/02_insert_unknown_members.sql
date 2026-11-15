/*
    FILE: 02_insert_unknown_members.sql
    PURPOSE:
        Add special dimension members used when a source value is missing.

    NOTE:
        The unknown customer is identified by customer_id = -1.
        Geography uses the ('Unknown', 'Unknown') combination.
        The incremental procedure expects the unknown customer to exist.
*/

USE EcommerceDB;
GO

-- Unknown customer member.
IF NOT EXISTS
(
    SELECT 1
    FROM dw.dim_customer
    WHERE customer_id = -1
)
BEGIN
    INSERT INTO dw.dim_customer (customer_id)
    VALUES (-1);
END;

-- Unknown geography combination.
IF NOT EXISTS
(
    SELECT 1
    FROM dw.dim_geography
    WHERE region = 'Unknown'
      AND country = 'Unknown'
)
BEGIN
    INSERT INTO dw.dim_geography (region, country)
    VALUES ('Unknown', 'Unknown');
END;

-- Ensure the payment and status dimensions have an Unknown member.
IF NOT EXISTS
(
    SELECT 1 FROM dw.dim_payment_method
    WHERE payment_method = 'Unknown'
)
BEGIN
    INSERT INTO dw.dim_payment_method (payment_method)
    VALUES ('Unknown');
END;

IF NOT EXISTS
(
    SELECT 1 FROM dw.dim_order_status
    WHERE order_status = 'Unknown'
)
BEGIN
    INSERT INTO dw.dim_order_status (order_status)
    VALUES ('Unknown');
END;
GO

-- Review the special members.
SELECT * FROM dw.dim_customer WHERE customer_id = -1;
SELECT * FROM dw.dim_geography
WHERE region = 'Unknown' AND country = 'Unknown';
SELECT * FROM dw.dim_payment_method WHERE payment_method = 'Unknown';
SELECT * FROM dw.dim_order_status WHERE order_status = 'Unknown';
