
DELETE FROM processesMacOS;

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        0, 'TermsAndConditions',
        1, 'Agree', 'AXButton', 'acceptButton', 'space', 6, 
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        1, 'Sign in', 'AXButton', 'sign_in', 'space', 1, 
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        2, 'Email address', 'AXTextField', 'login_email_address', 'bts_tony4@mailinator.com', 3,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        3, 'Next', 'AXButton', 'Next', 'space', 10,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        4, 'Password', 'AXTextField', '', 'P@ss1234', 2,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        5, ' Sign In ', 'AXButton', '', 'space', 15,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        2, 'Start Meeting',
        1, 'Meetings, 1 of 7', 'AXRadioButton', 'WTMeetingHubButton', 'space', 1,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        2, 'Start Meeting',
        2, 'Start a Webex meeting', 'AXButton', 'meetTab_startMeeting_button', 'space', 8,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        3, 'Accept Disclaimer',
        1, 'Accept', 'AXButton', 'Accept', 'space', 3,
        2, 'Webex Pre-meeting', 'en_US'
    )

INSERT INTO processesMacOS (
    processID, processName,
    processStep, controlName, controlType, controlIdentifier, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        4, 'Join from Pre-Meeting',
        1, 'Join meeting', 'AXButton', 'interstitial_joinMeeting_button', 'space', 10,
        2, 'Webex Pre-meeting', 'en_US'
    )