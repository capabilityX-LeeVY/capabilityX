-- Create TestSuites table to store test suite configuration information
-- This table records information from YAML files in src\test_space\test_suites\

CREATE TABLE IF NOT EXISTS TestSuites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT 'Test suite name from YAML file',
    team VARCHAR(100) COMMENT 'Team responsible for the test suite',
    owner VARCHAR(100) COMMENT 'Owner/maintainer of the test suite',
    platform VARCHAR(50) COMMENT 'Target platform (windows, mac, linux, etc.)',
    languages JSON COMMENT 'Supported languages as JSON array',
    test_cases JSON COMMENT 'List of test cases in the suite as JSON array',
    file_path VARCHAR(500) COMMENT 'Path to the YAML file',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_team (team),
    INDEX idx_owner (owner),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Test suites configuration table';

