-- Table: accepted_control_sr
-- Stores accepted (whitelisted) screen reader descriptions for controls
-- that are intentionally non-standard but acceptable.

USE control_db;

CREATE TABLE IF NOT EXISTS accepted_control_sr (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    control_name    VARCHAR(500)    NOT NULL,
    expected_sr_text TEXT           DEFAULT NULL   COMMENT 'The accepted screen reader text for this control',
    platform        VARCHAR(64)    DEFAULT 'Windows',
    app_version     VARCHAR(32)    DEFAULT NULL,
    language        VARCHAR(16)    DEFAULT 'en_US',
    added_by        VARCHAR(255)   DEFAULT 'wrs',
    added_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_control_name (control_name(255)),
    INDEX idx_platform_lang (platform, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
