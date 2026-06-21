-- Indexes for TestCaseNavigateReport table
-- Optimizes query performance for common search patterns

USE testcase_db;

-- Create composite indexes and other indexes (including the new test_suite field)
CREATE INDEX idx_tcnr_report_id ON TestCaseNavigateReport(report_id);
CREATE INDEX idx_tcnr_test_case ON TestCaseNavigateReport(test_case);
CREATE INDEX idx_tcnr_test_suite ON TestCaseNavigateReport(test_suite);                    -- New: test_suite index
CREATE INDEX idx_tcnr_test_suite_case ON TestCaseNavigateReport(test_suite, test_case);    -- New: composite index
CREATE INDEX idx_tcnr_test_case_report ON TestCaseNavigateReport(test_case, report_id);
CREATE INDEX idx_tcnr_report_step ON TestCaseNavigateReport(report_id, step_order);
CREATE INDEX idx_tcnr_navigate_result ON TestCaseNavigateReport(navigate_result);
CREATE INDEX idx_tcnr_step_start_time ON TestCaseNavigateReport(step_start_time);
CREATE INDEX idx_tcnr_suite_time ON TestCaseNavigateReport(test_suite, step_start_time);   -- New: composite index by suite and time

-- Indexes for platform and language fields
CREATE INDEX idx_tcnr_language ON TestCaseNavigateReport(language);                       -- Language index
CREATE INDEX idx_tcnr_platform ON TestCaseNavigateReport(platform);                      -- Platform index

-- Indexes for device fields
CREATE INDEX idx_tcnr_device_name ON TestCaseNavigateReport(device_name);                 -- Device name index
CREATE INDEX idx_tcnr_device_ip ON TestCaseNavigateReport(device_ip);                     -- Device IP index

-- Indexes for control metadata fields
CREATE INDEX idx_tcnr_control_type ON TestCaseNavigateReport(control_type);
CREATE INDEX idx_tcnr_window_level1 ON TestCaseNavigateReport(window_level1);
CREATE INDEX idx_tcnr_parent ON TestCaseNavigateReport(parent);
CREATE INDEX idx_tcnr_parent_type ON TestCaseNavigateReport(parent_type);
CREATE INDEX idx_tcnr_default_action ON TestCaseNavigateReport(default_action);
CREATE INDEX idx_tcnr_legacy_role ON TestCaseNavigateReport(legacy_role);
