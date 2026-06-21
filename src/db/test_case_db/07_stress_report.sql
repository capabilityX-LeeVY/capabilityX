-- Stress testing report table
-- Contains CPU, memory and health status data during stress testing

USE testcase_db;

DROP TABLE IF EXISTS TestCaseStressReport;

CREATE TABLE TestCaseStressReport (
    id INT AUTO_INCREMENT PRIMARY KEY,                   -- Auto-increment primary key
    report_id VARCHAR(255) NOT NULL,                      -- Test execution batch ID, links to TestCaseNavigateReport
    test_case VARCHAR(255) NOT NULL,
    test_suite VARCHAR(255),                              -- Test suite name (e.g., stress, load_test)
    control_name VARCHAR(500),
    main_cpu DECIMAL(5,2),
    main_mem DECIMAL(10,2),
    media_cpu DECIMAL(5,2),
    media_mem DECIMAL(10,2),
    cpu_check VARCHAR(10),                                -- PASS/FAIL
    memory_check VARCHAR(10),                             -- PASS/FAIL
    process_count INT,                                    -- Number of processes
    process_types TEXT,                                   -- Process type descriptions
    window_response_time INT,                             -- Window response time in ms
    process_status VARCHAR(20),                           -- HEALTHY/WARNING/UNHEALTHY/CRITICAL
    warnings TEXT,                                        -- Warning messages
    log_archive_path VARCHAR(500),                        -- Path to log archive
    app_version VARCHAR(100),
    device_name VARCHAR(255),                             -- Device name (e.g., test-machine-01)
    device_ip VARCHAR(45),                                -- Device IP address (supports both IPv4 and IPv6)
    test_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for stress testing table
CREATE INDEX idx_tcsr_report_id ON TestCaseStressReport(report_id);
CREATE INDEX idx_tcsr_test_case ON TestCaseStressReport(test_case);
CREATE INDEX idx_tcsr_test_suite ON TestCaseStressReport(test_suite);
CREATE INDEX idx_tcsr_test_time ON TestCaseStressReport(test_time);
CREATE INDEX idx_tcsr_device_name ON TestCaseStressReport(device_name);
CREATE INDEX idx_tcsr_process_status ON TestCaseStressReport(process_status);
CREATE INDEX idx_tcsr_suite_status ON TestCaseStressReport(test_suite, process_status);
CREATE INDEX idx_tcsr_created_at ON TestCaseStressReport(created_at);
