-- Create the e-commerce database if it does not already exist.

IF DB_ID('EcommerceDB') IS NULL
BEGIN
    CREATE DATABASE EcommerceDB;
    PRINT 'EcommerceDB created successfully.';
END
ELSE
BEGIN
    PRINT 'EcommerceDB already exists.';
END;
