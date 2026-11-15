/*
    FILE: 03_audit_log_checks.sql
    PURPOSE:
        Inspect recent executions of the warehouse stored procedure.
*/

USE EcommerceDB;
GO

-- Most recent warehouse executions.
SELECT TOP 10
    audit_id,
    pipeline_name,
    start_time,
    end_time,
    source_records,
    inserted_records,
    failed_records,
    execution_status,
    error_message
FROM dw.etl_audit_log
ORDER BY audit_id DESC;
GO

-- Execute only when intentionally testing the procedure.
-- This is safe to rerun: already-loaded order IDs should not be inserted again.
-- EXEC dw.usp_load_warehouse;
