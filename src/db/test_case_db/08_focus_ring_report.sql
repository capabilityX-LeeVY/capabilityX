-- Focus ring report table
-- Stores AI analysis results for focus ring accessibility compliance

USE testcase_db;

DROP TABLE IF EXISTS FocusRingReport;

CREATE TABLE FocusRingReport (
    id INT AUTO_INCREMENT PRIMARY KEY,                   -- Unique identifier for each record
    report_id VARCHAR(255) NOT NULL,                     -- Test execution batch ID, links to TestCaseNavigateReport
    step_order INT NOT NULL,                             -- Step order (control sequence number)
    test_case VARCHAR(255) NOT NULL,                     -- Test case name
    test_suite VARCHAR(255),                             -- Test suite name
    test_steps TEXT,                                     -- Test step description
    description TEXT,                                    -- Control description from focus ring analysis
    compliance VARCHAR(50) NOT NULL,                     -- Compliance status (Compliant/Non-compliant/Partial/Unknown)
    device_name VARCHAR(255),                            -- Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)
    device_ip VARCHAR(45),                               -- Device IP address (supports both IPv4 and IPv6)
    platform VARCHAR(50) DEFAULT 'Windows',             -- Platform, default Windows
    report_type VARCHAR(100) DEFAULT 'Focus Ring',      -- Report type, default value
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for optimization (separate statements after table creation)
CREATE INDEX idx_fr_step_order ON FocusRingReport(step_order);
CREATE INDEX idx_fr_report_id ON FocusRingReport(report_id);
CREATE INDEX idx_fr_test_case ON FocusRingReport(test_case);
CREATE INDEX idx_fr_test_suite ON FocusRingReport(test_suite);
CREATE INDEX idx_fr_compliance ON FocusRingReport(compliance);
CREATE INDEX idx_fr_device_name ON FocusRingReport(device_name);
CREATE INDEX idx_fr_created_at ON FocusRingReport(created_at);
CREATE INDEX idx_fr_report_step ON FocusRingReport(report_id, step_order);
CREATE INDEX idx_fr_case_compliance ON FocusRingReport(test_case, compliance);
CREATE INDEX idx_fr_report_case ON FocusRingReport(report_id, test_case);
