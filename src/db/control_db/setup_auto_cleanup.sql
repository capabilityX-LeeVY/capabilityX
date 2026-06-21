-- One-time setup script: Configure 7-day automatic cleanup
-- After executing this script, MySQL will automatically clean up data older than 7 days every day
-- You only need to run this script once!

USE control_db;

-- Step 1: Check and enable event scheduler
SHOW VARIABLES LIKE 'event_scheduler';

-- If the above shows OFF, execute the line below (uncomment it)
-- SET GLOBAL event_scheduler = ON;

-- Step 2: Create automatic cleanup event (core part)
DROP EVENT IF EXISTS auto_cleanup_7days;

CREATE EVENT auto_cleanup_7days
ON SCHEDULE 
    EVERY 1 DAY 
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 HOUR  -- Start in 1 hour, then execute daily
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Auto delete data older than 7 days'
DO
BEGIN
    -- Delete data older than 7 days
    DELETE FROM ControlINFO WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    DELETE FROM ControlINFO_Release WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
END;

-- Step 3: Verify event has been created
SHOW EVENTS WHERE Name = 'auto_cleanup_7days';

-- Done! Now MySQL will automatically clean up data older than 7 days every day
-- You don't need to do anything else

-- Optional: Manual test cleanup (if you need to clean old data immediately)
-- DELETE FROM ControlINFO WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
-- DELETE FROM ControlINFO_Release WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- Event management commands (backup):
-- View event status: SHOW EVENTS;
-- Disable event: ALTER EVENT auto_cleanup_7days DISABLE;
-- Enable event: ALTER EVENT auto_cleanup_7days ENABLE;
-- Delete event: DROP EVENT auto_cleanup_7days;
