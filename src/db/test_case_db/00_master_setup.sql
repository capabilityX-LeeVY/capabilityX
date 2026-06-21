-- Master execution script
-- Executes all database setup scripts in the correct order
-- Run this script to set up the complete database structure

-- 1. Initialize database
SOURCE 01_database_init.sql;

-- 2. Create core test case tables
SOURCE 02_testcase_core_tables.sql;

-- 3. Create execution results table
SOURCE 03_execution_results.sql;

-- 4. Create navigation report table
SOURCE 04_navigate_report_table.sql;

-- 5. Create indexes for navigation report
SOURCE 05_navigate_report_indexes.sql;

-- 6. Create performance report table
SOURCE 06_performance_report.sql;

-- 7. Create screen reader report table
SOURCE 07_screen_reader_report.sql;

-- 8. Apply any migrations (for existing databases)
-- SOURCE 08_database_migration.sql;

SELECT 'Database setup completed successfully!' AS status;
