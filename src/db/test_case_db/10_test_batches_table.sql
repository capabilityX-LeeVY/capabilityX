-- Create TestBatches table to store test batch configuration information
-- This table records information from YAML files in src\test_space\test_batches\

CREATE TABLE IF NOT EXISTS TestBatches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE COMMENT 'Test batch name from YAML file',
    team VARCHAR(100) COMMENT 'Team responsible for the test batch',
    owner VARCHAR(100) COMMENT 'Owner/maintainer of the test batch',
    platform VARCHAR(50) COMMENT 'Target platform (windows, mac, linux, etc.)',
    languages JSON COMMENT 'Supported languages as JSON array',
    test_cases JSON COMMENT 'List of test cases in the batch as JSON array',
    file_path VARCHAR(500) COMMENT 'Path to the YAML file',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_team (team),
    INDEX idx_owner (owner),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Test batches configuration table';
