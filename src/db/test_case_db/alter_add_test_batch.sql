-- Add test_batch column to TestCaseNavigateReport table
-- This script adds the test_batch field without dropping the table

USE testcase_db;

-- Add test_batch column after test_suite
ALTER TABLE TestCaseNavigateReport 
ADD COLUMN test_batch VARCHAR(255) COMMENT 'Test batch name (newly added field)' 
AFTER test_suite;

-- Create index for test_batch
CREATE INDEX idx_tcnr_test_batch ON TestCaseNavigateReport(test_batch);

-- Verify the change
DESCRIBE TestCaseNavigateReport;

SELECT 'Successfully added test_batch column and index!' AS Result;
