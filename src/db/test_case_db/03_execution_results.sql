-- Test case execution results
-- Contains execution status and basic results

USE testcase_db;

CREATE TABLE TestCaseExecutionResult (
    id INT AUTO_INCREMENT PRIMARY KEY,
    testcase_id INT,
    execution_start_time DATETIME,
    execution_end_time DATETIME,
    execution_duration_seconds DECIMAL(10,3),
    execution_status ENUM('PASS', 'FAIL', 'SKIP', 'ERROR') NOT NULL,
    FOREIGN KEY (testcase_id) REFERENCES TestCase(id) ON DELETE CASCADE,
    INDEX idx_testcase_id (testcase_id),
    INDEX idx_execution_time (execution_start_time),
    INDEX idx_status (execution_status)
);
