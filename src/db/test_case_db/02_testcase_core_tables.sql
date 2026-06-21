-- Test case core tables
-- Contains the main test case structure and related entities

USE testcase_db;

-- Main test case table
CREATE TABLE TestCase (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    team VARCHAR(255),
    owner VARCHAR(255),
    description TEXT,
    expect_result TEXT,
    execution_duration INT,
    execution_count INT,
    module_path VARCHAR(512)
);

-- Pre-conditions for test cases
CREATE TABLE PreCondition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    testcase_id INT,
    condition_text VARCHAR(255),
    FOREIGN KEY (testcase_id) REFERENCES TestCase(id) ON DELETE CASCADE
);

-- Post-conditions for test cases
CREATE TABLE PostCondition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    testcase_id INT,
    condition_text VARCHAR(255),
    FOREIGN KEY (testcase_id) REFERENCES TestCase(id) ON DELETE CASCADE
);

-- Test case steps
CREATE TABLE Step (
    id INT AUTO_INCREMENT PRIMARY KEY,
    testcase_id INT,
    name VARCHAR(255),
    action_type VARCHAR(50),
    action_value VARCHAR(255),
    expect_state VARCHAR(255),
    step_order INT,
    FOREIGN KEY (testcase_id) REFERENCES TestCase(id) ON DELETE CASCADE
);

-- AI checks for steps
CREATE TABLE AICheck (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_id INT,
    prompt TEXT,
    reference VARCHAR(255),
    FOREIGN KEY (step_id) REFERENCES Step(id) ON DELETE CASCADE
);

-- Check points for test cases
CREATE TABLE CheckPoint (
    id INT AUTO_INCREMENT PRIMARY KEY,
    testcase_id INT,
    point VARCHAR(255),
    FOREIGN KEY (testcase_id) REFERENCES TestCase(id) ON DELETE CASCADE
);
