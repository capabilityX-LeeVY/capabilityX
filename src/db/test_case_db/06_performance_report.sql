-- Performance report table
-- Contains CPU and memory usage data during test execution

USE testcase_db;

DROP TABLE IF EXISTS TestCasePerformanceReport;

CREATE TABLE TestCasePerformanceReport (
    id INT AUTO_INCREMENT PRIMARY KEY,                   -- Auto-increment primary key
    report_id VARCHAR(255) NOT NULL,                      -- Test execution batch ID, links to TestCaseNavigateReport
    test_case VARCHAR(255) NOT NULL,
    test_suite VARCHAR(255),                              -- Test suite name (e.g., smoke, regression)
    test_batch VARCHAR(255),                              -- Test batch name (newly added field)
    control_name VARCHAR(500),
    main_cpu DECIMAL(5,2),
    main_mem DECIMAL(10,2),
    media_cpu DECIMAL(5,2),
    media_mem DECIMAL(10,2),
    app_version VARCHAR(100),
    device_name VARCHAR(255),                             -- Device name (e.g., test-machine-01, iPhone-12-Pro, etc.)
    device_ip VARCHAR(45),                                -- Device IP address (supports both IPv4 and IPv6)
    test_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for performance table
CREATE INDEX idx_tcpr_report_id ON TestCasePerformanceReport(report_id);
CREATE INDEX idx_tcpr_test_case ON TestCasePerformanceReport(test_case);
CREATE INDEX idx_tcpr_test_suite ON TestCasePerformanceReport(test_suite);
CREATE INDEX idx_tcpr_test_batch ON TestCasePerformanceReport(test_batch);
CREATE INDEX idx_tcpr_test_time ON TestCasePerformanceReport(test_time);
CREATE INDEX idx_tcpr_device_name ON TestCasePerformanceReport(device_name);
