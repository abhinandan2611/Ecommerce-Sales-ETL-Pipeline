/*
    FILE: 01_load_dimensions_once.sql
    PURPOSE:
        Perform the initial population of the dimension tables from
        dbo.sales_orders.

    IMPORTANT:
        This is an initial-load script, not the incremental process.
        Your live warehouse is already populated. Do not run this file
        again against the existing populated dimensions.

    DATA RULES:
        - NULL descriptive values are represented as 'Unknown'.
        - Product consistency by product_id was checked in the source data.
        - One product row is selected per product_id.
*/

USE EcommerceDB;
GO

-- 1. Customer dimension: exclude NULL customer IDs.
INSERT INTO dw.dim_customer (customer_id)
SELECT DISTINCT s.customer_id
FROM dbo.sales_orders AS s
WHERE s.customer_id IS NOT NULL
  AND NOT EXISTS
  (
      SELECT 1
      FROM dw.dim_customer AS d
      WHERE d.customer_id = s.customer_id
  );

-- 2. Product dimension: create one row per product_id.
-- MAX() selects the product attributes after consistency was checked.
WITH ProductData AS
(
    SELECT
        product_id,
        MAX(product_name) AS product_name,
        MAX(product_category) AS product_category
    FROM dbo.sales_orders
    GROUP BY product_id
)
INSERT INTO dw.dim_product
(
    product_id,
    product_name,
    product_category
)
SELECT
    p.product_id,
    p.product_name,
    p.product_category
FROM ProductData AS p
WHERE NOT EXISTS
(
    SELECT 1
    FROM dw.dim_product AS d
    WHERE d.product_id = p.product_id
);

-- 3. Geography dimension: retain region/country combinations.
INSERT INTO dw.dim_geography (region, country)
SELECT DISTINCT
    COALESCE(s.region, 'Unknown'),
    COALESCE(s.country, 'Unknown')
FROM dbo.sales_orders AS s
WHERE NOT EXISTS
(
    SELECT 1
    FROM dw.dim_geography AS d
    WHERE d.region = COALESCE(s.region, 'Unknown')
      AND d.country = COALESCE(s.country, 'Unknown')
);

-- 4. Payment method dimension.
INSERT INTO dw.dim_payment_method (payment_method)
SELECT DISTINCT COALESCE(s.payment_method, 'Unknown')
FROM dbo.sales_orders AS s
WHERE NOT EXISTS
(
    SELECT 1
    FROM dw.dim_payment_method AS d
    WHERE d.payment_method = COALESCE(s.payment_method, 'Unknown')
);

-- 5. Order status dimension.
INSERT INTO dw.dim_order_status (order_status)
SELECT DISTINCT COALESCE(s.order_status, 'Unknown')
FROM dbo.sales_orders AS s
WHERE NOT EXISTS
(
    SELECT 1
    FROM dw.dim_order_status AS d
    WHERE d.order_status = COALESCE(s.order_status, 'Unknown')
);

-- 6. Date dimension: create every calendar date between source min/max.
DECLARE @StartDate DATE;
DECLARE @EndDate DATE;

SELECT
    @StartDate = MIN(order_date),
    @EndDate = MAX(order_date)
FROM dbo.sales_orders;

IF @StartDate IS NOT NULL
BEGIN
    ;WITH DateSeries AS
    (
        SELECT @StartDate AS calendar_date

        UNION ALL

        SELECT DATEADD(DAY, 1, calendar_date)
        FROM DateSeries
        WHERE calendar_date < @EndDate
    )
    INSERT INTO dw.dim_date
    (
        date_key,
        full_date,
        day_number,
        day_name,
        month_number,
        month_name,
        quarter_number,
        year_number,
        week_number
    )
    SELECT
        CONVERT(INT, CONVERT(CHAR(8), calendar_date, 112)),
        calendar_date,
        DAY(calendar_date),
        DATENAME(WEEKDAY, calendar_date),
        MONTH(calendar_date),
        DATENAME(MONTH, calendar_date),
        DATEPART(QUARTER, calendar_date),
        YEAR(calendar_date),
        DATEPART(ISO_WEEK, calendar_date)
    FROM DateSeries AS ds
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dw.dim_date AS d
        WHERE d.full_date = ds.calendar_date
    )
    OPTION (MAXRECURSION 0);
END;
GO
