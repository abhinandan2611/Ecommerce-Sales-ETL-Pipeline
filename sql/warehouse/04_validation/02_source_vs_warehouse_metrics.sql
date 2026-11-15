/*
    FILE: 02_source_vs_warehouse_metrics.sql
    PURPOSE:
        Compare high-level business metrics between the source table
        and the warehouse fact table.

    NOTE:
        The query uses quantity * unit_price as revenue, matching the
        calculation used in the project's earlier validation.
*/

USE EcommerceDB;
GO

-- Source metrics.
SELECT
    'Source' AS Data_Source,
    COUNT(DISTINCT order_id) AS Total_Orders,
    SUM(quantity) AS Total_Units,
    SUM(quantity * unit_price) AS Total_Revenue,
    SUM(shipping_cost) AS Total_Shipping
FROM dbo.sales_orders

UNION ALL

-- Warehouse metrics.
SELECT
    'Warehouse' AS Data_Source,
    COUNT(DISTINCT order_id),
    SUM(quantity),
    SUM(quantity * unit_price),
    SUM(shipping_cost)
FROM dw.fact_sales;
GO
