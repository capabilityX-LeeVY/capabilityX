-- MySQL Event Scheduler: Comprehensive automatic cleanup for all test report tables
-- Automatically delete data older than 7 days from TestCaseNavigateReport, TestCasePerformanceReport, and ScreenReaderReport
-- Requires event scheduler to be enabled

USE testcase_db;

-- 1. Check and enable event scheduler
-- Check event scheduler status
SHOW VARIABLES LIKE 'event_scheduler';

-- If it shows OFF, need to enable event scheduler
-- SET GLOBAL event_scheduler = ON;

-- 2. Create comprehensive cleanup event for all tables
DROP EVENT IF EXISTS cleanup_all_test_reports;

CREATE EVENT cleanup_all_test_reports
ON SCHEDULE 
    EVERY 1 DAY 
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 HOUR  -- Start execution 1 hour from now
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Automatically delete data older than 7 days from all test report tables'
DO
BEGIN
    DECLARE navigate_deleted INT DEFAULT 0;
    DECLARE performance_deleted INT DEFAULT 0;
    DECLARE screen_reader_deleted INT DEFAULT 0;
    DECLARE cleanup_start_time DATETIME DEFAULT NOW();
    
    -- 1. Clean up TestCaseNavigateReport
    DELETE FROM TestCaseNavigateReport 
    WHERE step_start_time < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET navigate_deleted = ROW_COUNT();
    
    -- 2. Clean up TestCasePerformanceReport
    DELETE FROM TestCasePerformanceReport 
    WHERE test_time < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET performance_deleted = ROW_COUNT();
    
    -- 3. Clean up ScreenReaderReport
    DELETE FROM ScreenReaderReport 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET screen_reader_deleted = ROW_COUNT();
    
    -- Log cleanup results
    SELECT 
        cleanup_start_time as 'Cleanup Started',
        NOW() as 'Cleanup Completed',
        TIMESTAMPDIFF(SECOND, cleanup_start_time, NOW()) as 'Duration (seconds)',
        navigate_deleted as 'NavigateReport Deleted',
        performance_deleted as 'PerformanceReport Deleted',
        screen_reader_deleted as 'ScreenReaderReport Deleted',
        (navigate_deleted + performance_deleted + screen_reader_deleted) as 'Total Deleted',
        'All test reports cleanup completed' as 'Status';
        
END;

-- 3. View created event
SHOW EVENTS WHERE Name = 'cleanup_all_test_reports';

-- 4. Manual verification queries (optional - for testing only)
-- Check records count in all tables
-- SELECT 'TestCaseNavigateReport' as table_name, COUNT(*) as total_records, 
--        COUNT(CASE WHEN step_start_time < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as old_records
-- FROM TestCaseNavigateReport
-- UNION ALL
-- SELECT 'TestCasePerformanceReport' as table_name, COUNT(*) as total_records,
--        COUNT(CASE WHEN test_time < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as old_records
-- FROM TestCasePerformanceReport
-- UNION ALL
-- SELECT 'ScreenReaderReport' as table_name, COUNT(*) as total_records,
--        COUNT(CASE WHEN created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as old_records
-- FROM ScreenReaderReport;

-- 5. Manual cleanup procedure (optional)
DROP PROCEDURE IF EXISTS ManualCleanupAllReports;

DELIMITER //
CREATE PROCEDURE ManualCleanupAllReports()
BEGIN
    DECLARE navigate_deleted INT DEFAULT 0;
    DECLARE performance_deleted INT DEFAULT 0;
    DECLARE screen_reader_deleted INT DEFAULT 0;
    DECLARE cleanup_start_time DATETIME DEFAULT NOW();
    
    -- Clean up all tables
    DELETE FROM TestCaseNavigateReport WHERE step_start_time < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET navigate_deleted = ROW_COUNT();
    
    DELETE FROM TestCasePerformanceReport WHERE test_time < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET performance_deleted = ROW_COUNT();
    
    DELETE FROM ScreenReaderReport WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET screen_reader_deleted = ROW_COUNT();
    
    -- Return results
    SELECT 
        cleanup_start_time as 'Cleanup Started',
        NOW() as 'Cleanup Completed',
        TIMESTAMPDIFF(SECOND, cleanup_start_time, NOW()) as 'Duration (seconds)',
        navigate_deleted as 'NavigateReport Deleted',
        performance_deleted as 'PerformanceReport Deleted',
        screen_reader_deleted as 'ScreenReaderReport Deleted',
        (navigate_deleted + performance_deleted + screen_reader_deleted) as 'Total Deleted';
        
END //
DELIMITER ;

-- 6. Execute manual cleanup if needed (optional)
-- CALL ManualCleanupAllReports();

-- 7. Event management commands (optional)
-- To disable the event: ALTER EVENT cleanup_all_test_reports DISABLE;
-- To enable the event: ALTER EVENT cleanup_all_test_reports ENABLE;
-- To drop the event: DROP EVENT IF EXISTS cleanup_all_test_reports;
