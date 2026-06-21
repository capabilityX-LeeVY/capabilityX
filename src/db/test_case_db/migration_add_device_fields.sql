-- Migration script: Add device_name and device_ip fields to TestCasePerformanceReport and ScreenReaderReport tables
-- Created on: 2025-08-07

USE testcase_db;

-- 1. Add device_name and device_ip to TestCasePerformanceReport table
ALTER TABLE TestCasePerformanceReport 
ADD COLUMN device_name VARCHAR(255) COMMENT 'Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)' AFTER app_version,
ADD COLUMN device_ip VARCHAR(45) COMMENT 'Device IP address (supports both IPv4 and IPv6)' AFTER device_name;

-- 2. Add device_name, device_ip, and test_suite to ScreenReaderReport table
ALTER TABLE ScreenReaderReport 
ADD COLUMN test_suite VARCHAR(255) COMMENT 'Test suite name' AFTER test_case,
ADD COLUMN device_name VARCHAR(255) COMMENT 'Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)' AFTER wcag_level,
ADD COLUMN device_ip VARCHAR(45) COMMENT 'Device IP address (supports both IPv4 and IPv6)' AFTER device_name;

-- 3. Add indexes for the new columns
CREATE INDEX idx_tcpr_device_name ON TestCasePerformanceReport(device_name);
CREATE INDEX idx_sr_device_name ON ScreenReaderReport(device_name);
CREATE INDEX idx_sr_test_suite ON ScreenReaderReport(test_suite);

-- 4. Verification queries
SELECT 'Migration completed successfully' as status;

-- Show the updated table structures
DESCRIBE TestCasePerformanceReport;
DESCRIBE ScreenReaderReport;

-- Show indexes
SHOW INDEX FROM TestCasePerformanceReport WHERE Key_name LIKE '%device%';
SHOW INDEX FROM ScreenReaderReport WHERE Key_name LIKE '%device%';


ALTER TABLE TestCaseNavigateReport
ADD COLUMN report_type VARCHAR(100) DEFAULT 'Keyboard Navigation' COMMENT 'Report type, default value';