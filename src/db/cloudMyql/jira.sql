-- Active: 1751105278661@@gc-hgh05-level2-lab-irc-5.cisco.com@3306@testcase_db
-- Create report_issue table for tracking JIRA issues
CREATE TABLE report_issue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jira_id VARCHAR(50),
    title TEXT,
    affect_version VARCHAR(100),
    platform VARCHAR(50),
    hash VARCHAR(255),
    hash_string TEXT,
    status VARCHAR(50),
    report_id VARCHAR(255),
    test_case VARCHAR(255),
    label VARCHAR(255),
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for optimization
CREATE INDEX idx_ri_jira_id ON report_issue(jira_id);
CREATE INDEX idx_ri_report_id ON report_issue(report_id);
CREATE INDEX idx_ri_test_case ON report_issue(test_case);
CREATE INDEX idx_ri_platform ON report_issue(platform);
CREATE INDEX idx_ri_status ON report_issue(status);
CREATE INDEX idx_ri_hash ON report_issue(hash);
CREATE INDEX idx_ri_create_date ON report_issue(create_date);
CREATE INDEX idx_ri_report_case ON report_issue(report_id, test_case);
CREATE INDEX idx_ri_platform_version ON report_issue(platform, affect_version);

-- Create unique constraint to prevent duplicate issues
CREATE UNIQUE INDEX uk_hash_report ON report_issue(hash, report_id);
