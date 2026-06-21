-- Active: 1727685703845@@wrs-sm.qa.webex.com@3306@RegressShield

DROP TABLE IF EXISTS windowsControls;

CREATE TABLE windowsControls (
    navigationID INT AUTO_INCREMENT PRIMARY KEY,
    controlName TEXT,
    controlType TEXT,
    controlAutomationID TEXT,
    controlFullDescription TEXT,
    controlBoundingRectangle TEXT,
    controlNativeWindowHandle TEXT,
    currentControl TEXT,
    entryControl TEXT,
    preControl TEXT,
    fromAction TEXT,
    isLocationChanged INTEGER DEFAULT 0,
    controlFocusRing LONGBLOB,
    preControlFocusRing LONGBLOB,
    isProcessed INTEGER DEFAULT 1
);


-- WITH RECURSIVE control_flow AS (
--     SELECT *
--     FROM windowsControls
--     WHERE isProcessed = 0
--     UNION ALL
--     SELECT c.*
--     FROM windowsControls c
--     INNER JOIN control_flow cf
--     ON cf.entryControl = c.currentControl
--     )
-- SELECT * FROM control_flow ORDER BY navigationID;
