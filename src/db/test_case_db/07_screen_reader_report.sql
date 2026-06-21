-- Screen reader report table
-- Stores AI analysis results for accessibility compliance

USE testcase_db;

DROP TABLE IF EXISTS ScreenReaderReport;

CREATE TABLE ScreenReaderReport (
    id INT AUTO_INCREMENT PRIMARY KEY,                   -- Unique identifier for each record
    report_id VARCHAR(255) NOT NULL,                     -- Test execution batch ID, links to TestCaseNavigateReport
    step_order INT NOT NULL,                             -- Step order (control sequence number)
    test_case VARCHAR(255) NOT NULL,                     -- Test case name
    test_suite VARCHAR(255),                             -- Test suite name
    test_batch VARCHAR(255),                             -- Test batch name (newly added field)
    test_steps TEXT,                                     -- Test step description
    description TEXT,                                    -- Control description from screen reader
    compliance VARCHAR(50) NOT NULL,                     -- Compliance status (Compliant/Non-compliant/Partial/Unknown)
    suggestions TEXT,                                    -- AI suggestions for improvement
    suggested_revision TEXT,                             -- Specific revision recommendations
    wcag_level VARCHAR(20) DEFAULT NULL,                 -- WCAG compliance level (Level A, AA, AAA)
    device_name VARCHAR(255),                            -- Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)
    device_ip VARCHAR(45),                               -- Device IP address (supports both IPv4 and IPv6)
    `references` TEXT,                                   -- WCAG reference guidelines (using backticks as 'references' is a reserved word)
    platform VARCHAR(50) DEFAULT 'Windows',                        -- Platform, default Windows
    report_type VARCHAR(100) DEFAULT 'Screen Reader',              -- Report type, default value
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for optimization (separate statements after table creation)
CREATE INDEX idx_sr_step_order ON ScreenReaderReport(step_order);
CREATE INDEX idx_sr_report_id ON ScreenReaderReport(report_id);
CREATE INDEX idx_sr_test_case ON ScreenReaderReport(test_case);
CREATE INDEX idx_sr_test_suite ON ScreenReaderReport(test_suite);
CREATE INDEX idx_sr_compliance ON ScreenReaderReport(compliance);
CREATE INDEX idx_sr_wcag_level ON ScreenReaderReport(wcag_level);
CREATE INDEX idx_sr_device_name ON ScreenReaderReport(device_name);
CREATE INDEX idx_sr_created_at ON ScreenReaderReport(created_at);
CREATE INDEX idx_sr_report_step ON ScreenReaderReport(report_id, step_order);
CREATE INDEX idx_sr_case_compliance ON ScreenReaderReport(test_case, compliance);
CREATE INDEX idx_sr_report_case ON ScreenReaderReport(report_id, test_case);

ALTER TABLE ScreenReaderReport
ADD COLUMN platform VARCHAR(50) DEFAULT 'Windows' COMMENT 'Platform, default Windows',
ADD COLUMN report_type VARCHAR(100) DEFAULT 'Screen Reader' COMMENT 'Report type, default value';