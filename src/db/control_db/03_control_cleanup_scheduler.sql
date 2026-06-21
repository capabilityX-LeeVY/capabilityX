-- Simplified MySQL Event Scheduler: Direct cleanup without history preservation
-- Directly delete data older than 7 days from ControlINFO and ControlINFO_Release
-- This approach does NOT preserve history - use only if historical data is not needed
-- NOTE: If using this approach, consider dropping the existing trigger

USE control_db;

-- 1. Check and enable event scheduler
SHOW VARIABLES LIKE 'event_scheduler';
-- If it shows OFF, enable it: SET GLOBAL event_scheduler = ON;

-- 2. Drop existing trigger if you decide not to use history
-- IMPORTANT: Uncomment the following lines only if you want to remove history functionality
-- DROP TRIGGER IF EXISTS tr_controlinfo_before_delete;

-- 3. Create simplified cleanup event - no history preservation
DROP EVENT IF EXISTS simplified_cleanup_control_info;

CREATE EVENT simplified_cleanup_control_info
ON SCHEDULE 
    EVERY 1 DAY 
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 HOUR
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Direct cleanup - no history preservation'
DO
BEGIN
    DECLARE control_info_deleted INT DEFAULT 0;
    DECLARE control_release_deleted INT DEFAULT 0;
    DECLARE cleanup_start_time DATETIME DEFAULT NOW();
    
    -- Direct cleanup without history preservation
    DELETE FROM ControlINFO 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_info_deleted = ROW_COUNT();
    
    -- Clean up release table
    DELETE FROM ControlINFO_Release 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_release_deleted = ROW_COUNT();
    
    -- Log cleanup results
    SELECT 
        cleanup_start_time as 'Cleanup Started',
        NOW() as 'Cleanup Completed',
        TIMESTAMPDIFF(SECOND, cleanup_start_time, NOW()) as 'Duration (seconds)',
        control_info_deleted as 'ControlINFO Deleted',
        control_release_deleted as 'ControlINFO_Release Deleted',
        (control_info_deleted + control_release_deleted) as 'Total Deleted',
        'Simplified cleanup completed - No history preserved' as 'Status';
        
END;

-- 4. Manual cleanup procedure - simplified version
DROP PROCEDURE IF EXISTS SimplifiedManualCleanup;

DELIMITER //
CREATE PROCEDURE SimplifiedManualCleanup()
BEGIN
    DECLARE control_info_deleted INT DEFAULT 0;
    DECLARE control_release_deleted INT DEFAULT 0;
    DECLARE cleanup_start_time DATETIME DEFAULT NOW();
    
    -- Direct deletion
    DELETE FROM ControlINFO WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_info_deleted = ROW_COUNT();
    
    DELETE FROM ControlINFO_Release WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_release_deleted = ROW_COUNT();
    
    -- Return results
    SELECT 
        cleanup_start_time as 'Cleanup Started',
        NOW() as 'Cleanup Completed',
        TIMESTAMPDIFF(SECOND, cleanup_start_time, NOW()) as 'Duration (seconds)',
        control_info_deleted as 'ControlINFO Deleted',
        control_release_deleted as 'ControlINFO_Release Deleted',
        (control_info_deleted + control_release_deleted) as 'Total Deleted';
        
END //
DELIMITER ;

-- 5. Cleanup by specific criteria - simplified
DROP PROCEDURE IF EXISTS SimplifiedCleanupByJob;

DELIMITER //
CREATE PROCEDURE SimplifiedCleanupByJob(IN jenkins_job_name VARCHAR(255))
BEGIN
    DECLARE control_info_deleted INT DEFAULT 0;
    DECLARE control_release_deleted INT DEFAULT 0;
    DECLARE cleanup_start_time DATETIME DEFAULT NOW();
    
    -- Direct deletion by job
    DELETE FROM ControlINFO 
    WHERE JenkinsJob = jenkins_job_name 
    AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_info_deleted = ROW_COUNT();
    
    DELETE FROM ControlINFO_Release 
    WHERE JenkinsJob = jenkins_job_name 
    AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    SET control_release_deleted = ROW_COUNT();
    
    SELECT 
        jenkins_job_name as 'Jenkins Job',
        cleanup_start_time as 'Cleanup Started',
        NOW() as 'Cleanup Completed',
        control_info_deleted as 'ControlINFO Deleted',
        control_release_deleted as 'ControlINFO_Release Deleted',
        (control_info_deleted + control_release_deleted) as 'Total Deleted';
        
END //
DELIMITER ;

-- 6. Optional: Clean up existing history table if not needed anymore
-- DANGER: This will delete ALL historical data permanently
-- Uncomment only if you're sure you don't need historical data

-- DROP PROCEDURE IF EXISTS CleanupAllHistory;
-- 
-- DELIMITER //
-- CREATE PROCEDURE CleanupAllHistory()
-- BEGIN
--     DECLARE history_deleted INT DEFAULT 0;
--     
--     DELETE FROM ControlINFO_History;
--     SET history_deleted = ROW_COUNT();
--     
--     SELECT 
--         'All historical data deleted' as 'Action',
--         history_deleted as 'Records Deleted',
--         NOW() as 'Completed At';
--         
-- END //
-- DELIMITER ;

-- 7. Event management
-- View events: SHOW EVENTS WHERE Name = 'simplified_cleanup_control_info';
-- Disable: ALTER EVENT simplified_cleanup_control_info DISABLE;
-- Enable: ALTER EVENT simplified_cleanup_control_info ENABLE;
-- Drop: DROP EVENT IF EXISTS simplified_cleanup_control_info;

-- 8. Complete migration guide and usage instructions
-- 
-- MIGRATION STEPS:
-- 1. Execute the migration script: 05_migration_to_simplified.sql
-- 2. Or manually execute the following in order:
--    a) ALTER EVENT cleanup_all_control_info DISABLE;
--    b) DROP TRIGGER IF EXISTS tr_controlinfo_before_delete;
--    c) Execute this entire script
--    d) DROP EVENT IF EXISTS cleanup_all_control_info;
--
-- USAGE EXAMPLES:
-- Manual cleanup: CALL SimplifiedManualCleanup();
-- Cleanup by job: CALL SimplifiedCleanupByJob('specific_jenkins_job');
-- Cleanup by workflow: CALL SimplifiedCleanupByWorkflow('sign_in', 'en-US');
--
-- EVENT MANAGEMENT:
-- View events: SHOW EVENTS WHERE Name = 'simplified_cleanup_control_info';
-- Disable: ALTER EVENT simplified_cleanup_control_info DISABLE;
-- Enable: ALTER EVENT simplified_cleanup_control_info ENABLE;
-- Drop: DROP EVENT IF EXISTS simplified_cleanup_control_info;
--
-- BENEFITS OF SIMPLIFIED APPROACH:
-- ✓ Better performance (no trigger overhead)
-- ✓ Reduced storage requirements
-- ✓ Simpler maintenance
-- ✓ Direct and predictable cleanup behavior
-- ✓ No complex history management logic
