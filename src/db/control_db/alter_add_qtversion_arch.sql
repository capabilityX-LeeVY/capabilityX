-- Active: 1753952281009@@gc-hgh05-level2-lab-irc-5.cisco.com@3306@control_db
-- Add QtVersion and Arch columns to existing ControlINFO tables
-- Run this script if you need to update existing database schema

USE control_db;

-- Add columns to main ControlINFO table
ALTER TABLE ControlINFO 
ADD COLUMN QtVersion VARCHAR(10) AFTER Language,
ADD COLUMN Arch VARCHAR(20) AFTER QtVersion;

-- Add columns to ControlINFO_History table
ALTER TABLE ControlINFO_History 
ADD COLUMN QtVersion VARCHAR(10) AFTER Language,
ADD COLUMN Arch VARCHAR(20) AFTER QtVersion;

-- Add columns to ControlINFO_Release table
ALTER TABLE ControlINFO_Release 
ADD COLUMN QtVersion VARCHAR(10) AFTER Language,
ADD COLUMN Arch VARCHAR(20) AFTER QtVersion;

-- Add indexes for better query performance (optional)
ALTER TABLE ControlINFO ADD INDEX idx_qtversion_arch (QtVersion, Arch);
ALTER TABLE ControlINFO_History ADD INDEX idx_qtversion_arch_hist (QtVersion, Arch);
ALTER TABLE ControlINFO_Release ADD INDEX idx_qtversion_arch_rel (QtVersion, Arch);
