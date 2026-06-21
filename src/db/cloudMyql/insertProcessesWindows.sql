

DELETE FROM processesWindows;

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        0, 'TermsAndConditions',
        1, ' Agree', '50000', 'EulaAgreementWindow.cancelButton', 'SPACE', 1, 
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        1, ' Sign in', '50000', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.nextButton', 'SPACE', 1, 
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        2, 'Sign inStart by entering your email address.', '50004', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.textInput', 'bts_tony2@mailinator.com', 1,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        3, ' Next', '50000', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.nextButton', 'SPACE', 10,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        4, 'Password ', '50004', 'IDToken2', 'P@ss1234', 1,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        1, 'Login',
        5, ' Sign In ', '50000', 'Button1', 'SPACE', 10,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        2, 'Start Meeting',
        1, 'Close', '50000', '', 'SPACE', 1,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        2, 'Start Meeting',
        2, ' Meetings tab, , 2 of 8, to activate press SPACEBAR', '50025', 'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector', 'SPACE', 1,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        2, 'Start Meeting',
        3, ' Start meeting. Meet in my personal room', '50000', 'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton', 'SPACE', 8,
        1, 'Webex APP', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        3, 'Accept Disclaimer',
        1, 'Accept', '50000', 'DisclaimerWidget.acceptBtn', 'SPACE', 3,
        2, 'Webex Pre-meeting', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        4, 'Join from Pre-Meeting',
        1, 'Join meeting, , Computer audio, Unmuted, Video on.', '50000', 'animatedJoinButtonItem', 'SPACE', 10,
        2, 'Webex Pre-meeting', 'en_US'
    )

INSERT INTO processesWindows (
    processID, processName,
    processStep, controlName, controlType, controlAutomationID, controlAction, controlActionWaitTime,
    projectID, projectName, languageCode
)
VALUES (
        4, 'Start Meeting',
        1, 'Start meeting, , Computer audio, Unmuted, Video on.|', '50000', 'animatedJoinButtonItem', 'SPACE', 10,
        2, 'Webex Pre-meeting', 'en_US'
    )