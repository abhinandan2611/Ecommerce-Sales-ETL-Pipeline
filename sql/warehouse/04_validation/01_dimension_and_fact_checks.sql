/*
    FILE: 01_dimension_and_fact_checks.sql
    PURPOSE:
        Review dimension and fact table row counts and inspect sample rows.
*/

USE EcommerceDB;
GO

-- Dimension row counts.
SELECT 'Customers' AS Dimension, COUNT(*) AS Total_Records
FROM dw.dim_customer
UNION ALL
SELECT 'Products', COUNT(*) FROM dw.dim_product
UNION ALL
SELECT 'Geography', COUNT(*) FROM dw.dim_geography
UNION ALL
SELECT 'Payment Methods', COUNT(*) FROM dw.dim_payment_method
UNION ALL
SELECT 'Order Status', COUNT(*) FROM dw.dim_order_status
UNION ALL
SELECT 'Dates', COUNT(*) FROM dw.dim_date;

-- Fact table row count.
SELECT COUNT(*) AS Total_Fact_Records
FROM dw.fact_sales;

-- Check for duplicate order IDs. Expected: no rows.
SELECT
    order_id,
    COUNT(*) AS Occurrences
FROM dw.fact_sales
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Check for missing dimension keys. Expected: 0.
SELECT COUNT(*) AS Invalid_Dimension_Keys
FROM dw.fact_sales
WHERE customer_key IS NULL
   OR product_key IS NULL
   OR date_key IS NULL
   OR geography_key IS NULL
   OR payment_method_key IS NULL
   OR order_status_key IS NULL;

-- Compare source and warehouse row counts.
SELECT
    (SELECT COUNT(*) FROM dbo.sales_orders) AS Source_Records,
    (SELECT COUNT(*) FROM dw.fact_sales) AS Warehouse_Records;
GO
