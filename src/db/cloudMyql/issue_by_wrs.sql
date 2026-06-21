-- Active: 1754884235920@@gc-hgh05-level2-lab-irc-5.cisco.com@3306@mysql

CREATE TABLE IF NOT EXISTS `issue_db`.`issue_by_wrs` (
    `jiraID` VARCHAR(64) NOT NULL PRIMARY KEY,
    `title` VARCHAR(255),
    `affectVersion` VARCHAR(64),
    `platform` VARCHAR(64),
    `description` TEXT,
    `type` VARCHAR(64),
    `status` VARCHAR(32) DEFAULT 'New',
    `hash` CHAR(64),
    `hashString` TEXT,
    `hashString_new` TEXT,
    `controlName` TEXT,
    `imgBytes` LONGBLOB,
    `imgHash` VARCHAR(64),
    `testCase` TEXT,
    `reportId` VARCHAR(64),
    `reportDate` DATETIME,
    `createDate` DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



