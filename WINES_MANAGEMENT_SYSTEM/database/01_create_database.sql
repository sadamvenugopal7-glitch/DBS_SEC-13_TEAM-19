-- =====================================================================
-- WINES MANAGEMENT SYSTEM
-- Database Systems Engineering Project
-- Database: wines_management_db
-- File: 01_create_database.sql
-- =====================================================================

DROP DATABASE IF EXISTS wines_management_db;

CREATE DATABASE wines_management_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE wines_management_db;

SELECT 'Database wines_management_db created successfully!' AS status;
