/*
    FILE: 01_usp_load_warehouse.sql
    PURPOSE:
        Create the incremental warehouse-loading stored procedure.

    PROCESS:
        1. Create an audit record.
        2. Count source orders not yet present in the fact table.
        3. Insert any new dimension members.
        4. Extend the date dimension when new dates arrive.
        5. Insert only fact rows whose order_id is not already loaded.
        6. Commit and mark the audit record successful.
        7. On error, roll back the warehouse transaction and log the error.

    EXECUTION:
        EXEC dw.usp_load_warehouse;

    REQUIREMENTS:
        - Dimension and fact tables must already exist.
        - The Unknown customer (customer_id = -1) must exist.
        - dw.etl_audit_log must exist.
*/

USE EcommerceDB;
GO

CREATE OR ALTER PROCEDURE dw.usp_load_warehouse
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @StartTime DATETIME2 = SYSUTCDATETIME();
    DECLARE @EndTime DATETIME2;
    DECLARE @SourceRecords INT = 0;
    DECLARE @InsertedRecords INT = 0;
    DECLARE @AuditID BIGINT;
    DECLARE @ErrorMessage NVARCHAR(MAX);

    -- Create an audit record before starting the warehouse transaction.
    INSERT INTO dw.etl_audit_log
    (
        pipeline_name,
        start_time,
        execution_status
    )
    VALUES
    (
        'Warehouse Incremental Load',
        @StartTime,
        'Running'
    );

    SET @AuditID = SCOPE_IDENTITY();

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Count source orders that are not yet represented in the fact table.
        SELECT @SourceRecords = COUNT(*)
        FROM dbo.sales_orders AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dw.fact_sales AS f
            WHERE f.order_id = s.order_id
        );

        -- 1. Insert new customers, excluding missing customer IDs.
        INSERT INTO dw.dim_customer (customer_id)
        SELECT DISTINCT s.customer_id
        FROM dbo.sales_orders AS s
        WHERE s.customer_id IS NOT NULL
          AND NOT EXISTS
          (
              SELECT 1
              FROM dw.dim_customer AS c
              WHERE c.customer_id = s.customer_id
          );

        -- 2. Insert new products, one row per product_id.
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

        -- 3. Insert new region/country combinations.
        INSERT INTO dw.dim_geography (region, country)
        SELECT DISTINCT
            COALESCE(s.region, 'Unknown'),
            COALESCE(s.country, 'Unknown')
        FROM dbo.sales_orders AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dw.dim_geography AS g
            WHERE g.region = COALESCE(s.region, 'Unknown')
              AND g.country = COALESCE(s.country, 'Unknown')
        );

        -- 4. Insert new payment methods.
        INSERT INTO dw.dim_payment_method (payment_method)
        SELECT DISTINCT COALESCE(s.payment_method, 'Unknown')
        FROM dbo.sales_orders AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dw.dim_payment_method AS p
            WHERE p.payment_method = COALESCE(s.payment_method, 'Unknown')
        );

        -- 5. Insert new order statuses.
        INSERT INTO dw.dim_order_status (order_status)
        SELECT DISTINCT COALESCE(s.order_status, 'Unknown')
        FROM dbo.sales_orders AS s
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dw.dim_order_status AS o
            WHERE o.order_status = COALESCE(s.order_status, 'Unknown')
        );

        -- 6. Add any calendar dates missing from the date dimension.
        DECLARE @MinDate DATE;
        DECLARE @MaxDate DATE;

        SELECT
            @MinDate = MIN(order_date),
            @MaxDate = MAX(order_date)
        FROM dbo.sales_orders;

        IF @MinDate IS NOT NULL
        BEGIN
            ;WITH DateSeries AS
            (
                SELECT @MinDate AS calendar_date

                UNION ALL

                SELECT DATEADD(DAY, 1, calendar_date)
                FROM DateSeries
                WHERE calendar_date < @MaxDate
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
                FROM dw.dim_date AS existing
                WHERE existing.full_date = ds.calendar_date
            )
            OPTION (MAXRECURSION 0);
        END;

        -- 7. Insert new fact rows using the dimension surrogate keys.
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

        -- The Unknown customer row handles NULL customer IDs.
        CROSS JOIN
        (
            SELECT customer_key
            FROM dw.dim_customer
            WHERE customer_id = -1
        ) AS unknown_customer

        LEFT JOIN dw.dim_customer AS c
            ON s.customer_id = c.customer_id

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

        -- Idempotency check: do not insert an order already in the fact table.
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dw.fact_sales AS f
            WHERE f.order_id = s.order_id
        );

        SET @InsertedRecords = @@ROWCOUNT;

        COMMIT TRANSACTION;

        -- Mark the audit entry successful after the transaction commits.
        SET @EndTime = SYSUTCDATETIME();

        UPDATE dw.etl_audit_log
        SET
            end_time = @EndTime,
            source_records = @SourceRecords,
            inserted_records = @InsertedRecords,
            failed_records = 0,
            execution_status = 'Success'
        WHERE audit_id = @AuditID;
    END TRY
    BEGIN CATCH
        -- Roll back all dimension and fact changes from this execution.
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @EndTime = SYSUTCDATETIME();
        SET @ErrorMessage = ERROR_MESSAGE();

        -- Preserve the audit record and capture the SQL Server error.
        UPDATE dw.etl_audit_log
        SET
            end_time = @EndTime,
            source_records = @SourceRecords,
            inserted_records = 0,
            failed_records = @SourceRecords,
            execution_status = 'Failed',
            error_message = @ErrorMessage
        WHERE audit_id = @AuditID;

        THROW;
    END CATCH;
END;
GO

-- Optional deployment check: confirm that the procedure exists.
SELECT
    name,
    create_date,
    modify_date
FROM sys.procedures
WHERE name = 'usp_load_warehouse';
GO
