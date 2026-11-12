SELECT
    'Valid Records' AS table_name,
    COUNT(*) AS total_records
FROM dbo.sales_orders

UNION ALL

SELECT
    'Quarantined Records',
    COUNT(*)
FROM dbo.quarantined_sales_orders;