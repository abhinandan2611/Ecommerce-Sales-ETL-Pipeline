/*
    FILE: 01_create_dw_schema.sql
    PURPOSE:
        Create the Data Warehouse schema if it does not already exist.

    RUN:
        Once, before creating the warehouse tables.
*/

USE EcommerceDB;
GO

IF SCHEMA_ID('dw') IS NULL
BEGIN
    EXEC('CREATE SCHEMA dw');
END;
GO
