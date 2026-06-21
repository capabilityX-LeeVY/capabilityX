-- Navigation test report table
-- Contains detailed navigation test results with control information

USE testcase_db;

DROP TABLE IF EXISTS TestCaseNavigateReport;

CREATE TABLE TestCaseNavigateReport (
    id INT AUTO_INCREMENT PRIMARY KEY,                    -- Unique identifier for each record
    report_id VARCHAR(255) NOT NULL,                      -- Test execution batch ID, shared by all steps in one test run
    test_suite VARCHAR(255),                              -- Test suite name (newly added field)
    test_batch VARCHAR(255),                              -- Test batch name (newly added field)
    test_case VARCHAR(255) NOT NULL,                      -- Test case name
    step_order INT NOT NULL,                              -- Step order (which step)
    test_steps TEXT,                                      -- Test step description
    locate_control_name VARCHAR(500),                     -- Located control name
    current_control_name VARCHAR(500),                    -- Current focused control name (from full_description)
    locate_control_image TEXT,                            -- Control screenshot path
    reference_image TEXT,                                 -- Reference image path
    window_image_path TEXT,                               -- Window screenshot file path
    control_image_path TEXT,                              -- Control image file path
    llm_response TEXT,                                    -- AI model response
    expect_result VARCHAR(500),                           -- Expected result
    actual_result VARCHAR(500),                           -- Actual result
    navigate_result VARCHAR(50),                          -- Navigation result (Success/Failed/Optional)
    focus_ring_result VARCHAR(50),                        -- Focus ring detection result (✅ Success/❌ WCAG 2.4.7/N/A/Error)
    screen_reader_description TEXT,                       -- Screen reader accessibility description
    screen_reader_result VARCHAR(50),                     -- Screen reader test result (Pass/Fail/Warning/N/A)
    screen_reader_suggestions TEXT,                       -- Screen reader improvement suggestions
    screen_reader_suggested_revision TEXT,                -- Suggested revision for screen reader compatibility
    app_version VARCHAR(100),                             -- Application version
    language VARCHAR(50),                                 -- Language setting (e.g., en, zh, fr, etc.)
    platform VARCHAR(50),                                 -- Platform (e.g., Windows, Mac, Linux, iOS, Android, etc.)
    device_name VARCHAR(255),                             -- Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)
    device_ip VARCHAR(45),                                -- Device IP address (supports both IPv4 and IPv6)
    control_type VARCHAR(100),                            -- Control type (button, edit, menu item, etc.)
    full_description TEXT,                                -- Full description of the control
    accessKey VARCHAR(255),                                -- Access key for the control
    window_level1 VARCHAR(255),                           -- Window level 1 hierarchy
    window_level2 VARCHAR(255),                           -- Window level 2 hierarchy
    parent VARCHAR(500),                                  -- Parent control name
    parent_type VARCHAR(100),                             -- Parent control type
    default_action VARCHAR(255),                          -- Default action attribute
    legacy_value VARCHAR(500),                            -- Legacy value attribute
    legacy_role VARCHAR(100),                             -- Legacy role attribute
    legacy_state VARCHAR(100),                            -- Legacy state attribute
    control_pre_img LONGBLOB DEFAULT NULL,                -- Previous control image byte data for comparison
    control_img LONGBLOB DEFAULT NULL,                    -- Current control image byte data  
    window_img LONGBLOB DEFAULT NULL,                     -- Window screenshot image byte data
    step_start_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Step start time
    step_end_time DATETIME,                               -- Step end time
    step_duration_ms INT,                                 -- Step execution duration (milliseconds)
    
    -- UI Response Time Measurement Fields
    ui_response_enabled BOOLEAN DEFAULT FALSE,            -- Whether UI response measurement was enabled for this step
    ui_response_time_ms DECIMAL(10,1) DEFAULT NULL,      -- UI response time in milliseconds (time from action to expected state)
    ui_response_success BOOLEAN DEFAULT NULL,             -- Whether expected state was achieved within timeout
    ui_response_expected_state TEXT DEFAULT NULL,         -- Expected UI state for response measurement
    ui_response_actual_state TEXT DEFAULT NULL,           -- Actual final UI state when measurement completed
    ui_response_polling_count INT DEFAULT NULL,           -- Number of polling attempts made during measurement
    ui_response_timeout_occurred BOOLEAN DEFAULT FALSE,   -- Whether measurement timed out
    ui_response_error_message TEXT DEFAULT NULL,          -- Error message if UI response measurement failed
    
    -- JIRA Issue Tracking Fields
    jira_issue_id VARCHAR(255) DEFAULT NULL,              -- JIRA issue ID (e.g., WEB-12345)
    
    -- Internationalization and Process Tracking Fields
    i18n_result VARCHAR(255) DEFAULT NULL,                 -- Internationalization test result (Pass/Fail/Warning/N/A)
    pid INT DEFAULT NULL,                                  -- Process ID for tracking test execution process
        
    -- Performance Monitoring Fields
    main_cpu DECIMAL(5,2) DEFAULT NULL,                   -- Main process CPU usage percentage (0-100)
    main_mem DECIMAL(10,2) DEFAULT NULL,                  -- Main process memory usage in MB
    main_gpu DECIMAL(5,2) DEFAULT NULL,                   -- Main process GPU usage percentage (0-100)
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    report_type VARCHAR(100) DEFAULT 'Keyboard Navigation'           -- Report type, default value
);

-- Create indexes for better query performance
CREATE INDEX idx_tcnr_report_id ON TestCaseNavigateReport(report_id);
CREATE INDEX idx_tcnr_test_case ON TestCaseNavigateReport(test_case);
CREATE INDEX idx_tcnr_test_suite ON TestCaseNavigateReport(test_suite);
CREATE INDEX idx_tcnr_test_batch ON TestCaseNavigateReport(test_batch);
CREATE INDEX idx_tcnr_step_start_time ON TestCaseNavigateReport(step_start_time);
CREATE INDEX idx_tcnr_navigate_result ON TestCaseNavigateReport(navigate_result);
CREATE INDEX idx_tcnr_focus_ring_result ON TestCaseNavigateReport(focus_ring_result);
CREATE INDEX idx_tcnr_screen_reader_result ON TestCaseNavigateReport(screen_reader_result);
CREATE INDEX idx_tcnr_device_name ON TestCaseNavigateReport(device_name);

-- UI Response Time specific indexes
CREATE INDEX idx_tcnr_ui_response_enabled ON TestCaseNavigateReport(ui_response_enabled);
CREATE INDEX idx_tcnr_ui_response_success ON TestCaseNavigateReport(ui_response_success);
CREATE INDEX idx_tcnr_ui_response_time ON TestCaseNavigateReport(ui_response_time_ms);

-- Composite index for UI response analysis
CREATE INDEX idx_tcnr_ui_response_analysis ON TestCaseNavigateReport(ui_response_enabled, ui_response_success, ui_response_time_ms);

-- JIRA Issue tracking indexes
CREATE INDEX idx_tcnr_jira_issue_id ON TestCaseNavigateReport(jira_issue_id);

-- Internationalization and Process tracking indexes
CREATE INDEX idx_tcnr_i18n_result ON TestCaseNavigateReport(i18n_result);
CREATE INDEX idx_tcnr_pid ON TestCaseNavigateReport(pid);

-- Performance monitoring indexes
CREATE INDEX idx_tcnr_main_cpu ON TestCaseNavigateReport(main_cpu);
CREATE INDEX idx_tcnr_main_mem ON TestCaseNavigateReport(main_mem);
CREATE INDEX idx_tcnr_main_gpu ON TestCaseNavigateReport(main_gpu);

-- Composite index for performance analysis
CREATE INDEX idx_tcnr_performance_analysis ON TestCaseNavigateReport(main_cpu, main_mem, main_gpu);
