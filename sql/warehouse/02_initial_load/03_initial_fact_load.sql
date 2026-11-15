/*
    FILE: 03_initial_fact_load.sql
    PURPOSE:
        Load the initial set of sales records into dw.fact_sales.

    IMPORTANT:
        This file is for the first warehouse population only.
        Your existing fact table already contains 18,386 records.
        Do not run this file again as a refresh. Use the stored procedure
        in 03_procedures/01_usp_load_warehouse.sql for incremental loads.

    GRAIN:
        One fact row per order_id.
*/

USE EcommerceDB;
GO

INSERT INTO dw.fact_sales
(
    order_id,
    customer_key,
    product_key,
    date_key,
    geography_key,
    payment_method_key,
    order_status_key,
    quantity,
    unit_price,
    discount,
    shipping_cost
)
SELECT
    s.order_id,
    COALESCE(c.customer_key, unknown_customer.customer_key),
    p.product_key,
    d.date_key,
    g.geography_key,
    pm.payment_method_key,
    os.order_status_key,
    s.quantity,
    s.unit_price,
    s.discount,
    s.shipping_cost
FROM dbo.sales_orders AS s

-- Match a known customer when present.
LEFT JOIN dw.dim_customer AS c
    ON s.customer_id = c.customer_id

-- Provide the single Unknown customer key for missing customer IDs.
CROSS JOIN
(
    SELECT customer_key
    FROM dw.dim_customer
    WHERE customer_id = -1
) AS unknown_customer

INNER JOIN dw.dim_product AS p
    ON s.product_id = p.product_id

INNER JOIN dw.dim_date AS d
    ON s.order_date = d.full_date

INNER JOIN dw.dim_geography AS g
    ON COALESCE(s.region, 'Unknown') = g.region
   AND COALESCE(s.country, 'Unknown') = g.country

INNER JOIN dw.dim_payment_method AS pm
    ON COALESCE(s.payment_method, 'Unknown') = pm.payment_method

INNER JOIN dw.dim_order_status AS os
    ON COALESCE(s.order_status, 'Unknown') = os.order_status

-- Protect against rerunning this initial-load statement.
WHERE NOT EXISTS
(
    SELECT 1
    FROM dw.fact_sales AS f
    WHERE f.order_id = s.order_id
);
GO
