-- Active: 1725846508072@@127.0.0.1@3306
-- Active: 1724378630371@@127.0.0.1@3306
DELETE FROM "Processes";

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        0, 'TermsAndConditions',
        1, 'Agree', '50000', NULL, '{SPACE}', 1, 
        0, 'Installer'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        1, 'Login',
        1, ' Sign in', '50000', NULL, '{SPACE}', 1, 
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        1, 'Login',
        2, 'Sign inStart by entering your email address.', '50004', NULL, 'bts_tony1@mailinator.com', 1,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        1, 'Login',
        3, ' Next', '50000', NULL, '{SPACE}', 5,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        1, 'Login',
        4, 'Password ', '50004', NULL, 'P@ss1234', 1,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        1, 'Login',
        5, 'Sign In', '50000', NULL, '{SPACE}', 10,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        2, 'Start Meeting',
        1, 'Primary navigation menu, Messaging tab, selected, 1 of 7, to activate press SPACEBAR', '50025', NULL, '{Down}', 2,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        2, 'Start Meeting',
        2, 'Meetings tab, , 2 of 7, to activate press SPACEBAR', '50025', NULL, '{SPACE}', 1,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        2, 'Start Meeting',
        3, 'Start meeting. Meet in my personal room', '50000', NULL, '{SPACE}', 5,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        3, 'Accept Disclaimer',
        1, 'Accept', '50000', NULL, '{SPACE}', 3,
        1, 'Webex APP'
    )

insert into
    "Processes" (
        "ProcessID", "ProcessName",
        "ProcessStep", "ControlName", "ControlType", "ControlAutomationID", "ControlAction", "ControlActionWaitTime",
        "ProjectID", "ProjectName"
    )
VALUES (
        4, 'Join from Pre-Meeting',
        1, 'Join meeting, , Computer audio, Unmuted, Video on.', '50000', NULL, '{SPACE}', 10,
        1, 'Webex APP'
    )