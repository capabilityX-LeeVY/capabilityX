

DROP TABLE IF EXISTS processesWindows;

CREATE TABLE IF NOT EXISTS processesWindows (
    processID INTEGER,
    processName TEXT,
    processStep INTEGER,
    controlName TEXT,
    controlType TEXT,
    controlAutomationID TEXT,
    controlAction TEXT,
    controlActionWaitTime INTEGER DEFAULT 1,
    projectID INTEGER,
    projectName TEXT,
    languageCode TEXT,
    UNIQUE(processName(255), controlName(255))
);


DROP TABLE IF EXISTS processesMacOS;

CREATE TABLE IF NOT EXISTS processesMacOS (
    processID INTEGER,
    processName TEXT,
    processStep INTEGER,
    controlName TEXT,
    controlType TEXT,
    controlIdentifier TEXT,
    controlAction TEXT,
    controlActionWaitTime INTEGER DEFAULT 1,
    projectID INTEGER,
    projectName TEXT,
    languageCode TEXT,
    UNIQUE(controlName(255), controlType(255), controlIdentifier(255))
);