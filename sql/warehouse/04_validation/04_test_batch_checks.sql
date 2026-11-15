/*
    FILE: 04_test_batch_checks.sql
    PURPOSE:
        Validate a known test batch by its order_id range.

    USAGE:
        Change the two order_id values to match the test batch being checked.
*/

USE EcommerceDB;
GO

DECLARE @FirstOrderID BIGINT = 930001;
DECLARE @LastOrderID BIGINT = 930020;

-- Count accepted source records.
SELECT COUNT(*) AS New_Valid_Records
FROM dbo.sales_orders
WHERE order_id BETWEEN @FirstOrderID AND @LastOrderID;

-- Count quarantined source records.
SELECT COUNT(*) AS Quarantined_Records
FROM dbo.quarantined_sales_orders
WHERE order_id BETWEEN @FirstOrderID AND @LastOrderID;

-- Count corresponding warehouse fact records.
SELECT COUNT(*) AS New_Fact_Records
FROM dw.fact_sales
WHERE order_id BETWEEN @FirstOrderID AND @LastOrderID;

-- Review audit history after the test run.
SELECT TOP 5
    audit_id,
    source_records,
    inserted_records,
    failed_records,
    execution_status,
    start_time,
    end_time
FROM dw.etl_audit_log
ORDER BY audit_id DESC;
GO
