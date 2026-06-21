from typing import Dict, List, Any
from config.paths import SETTINGS_PATH
from common.startup.startup_initializer import StartupInitializer
from common.handler.settingsHandler import DynamicConfig
# This file is part of the Workflow project.
# number means the index of the control in the workflow.
# These controls should be skipped in the workflow.

StartupInitializer()
settings = DynamicConfig(SETTINGS_PATH)

workflow_value = settings.get('workflow')
WORKFLOW_MODE: str = (settings.get('workflow') or '').strip() or 'in_meeting'
install_options = settings.get('installOptions') or {}
arch = install_options.get('arch', 'x64')
if arch == 'arm64':
    VERSION: str = "6.8"
else:
    VERSION: str = str(install_options.get('qtversion', '6')).strip()

WORKFLOW_OPERATOR_FLAG = True

def get_workflow_config(workflow_name: str, version: str = "6"):
    wf = WORKFLOW.get(workflow_name, {})
    skip = wf.get("SKIP", {}).get(version, [])
    input_values = wf.get("INPUT_VALUES", {}).get(version, {})
    end = wf.get("END", {}).get(version, [])
    force_validate = wf.get("FORCE_VALIDATE", {}).get(version, [])
    return {
        "SKIP": skip,
        "INPUT_VALUES": input_values,
        "END": end,
        "FORCE_VALIDATE": force_validate
    }

WORKFLOW: Dict[str, Dict[str, Any]]  = {
    "guest_join_meeting": {
        "SKIP": {
            "6": [
                "x"
            ],
            "6.8": [
                "y"
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.userInput.UTTextField.textInput": "binbiwan.cisco@webex.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.userInput.UTTextField.textInput":"binbiwan.cisco@webex.com",
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nameInput.UTTextField.textInput": "bts_tony2",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nameInput.UTTextField.textInput":"bts_tony2",
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.emailInput.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.emailInput.UTTextField.textInput":"bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.userInput.UTTextField.textInput":"binbiwan.cisco@webex.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.nameInput.UTTextField.textInput":"bts_tony2",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.emailInput.UTTextField.textInput":"bts_tony2@mailinator.com"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.userInput.UTTextField.textInput": "binbiwan.cisco@webex.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.userInput.UTTextField.textInput":"binbiwan.cisco@webex.com",
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nameInput.UTTextField.textInput": "bts_tony2",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nameInput.UTTextField.textInput":"bts_tony2",
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.emailInput.UTTextField.textInput": "bts_tony2@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.emailInput.UTTextField.textInput":"bts_tony2@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.userInput.UTTextField.textInput":"binbiwan.cisco@webex.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.nameInput.UTTextField.textInput":"bts_tony2",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.emailInput.UTTextField.textInput":"bts_tony2@mailinator.com"
            }
        },
        "END": {
            "6": [
                "Main_CallStripButton_Audio_Right",
                "audioControlItem.buttonRowLayout.dualComboButtonLeftCell"
            ],
            "6.8": [
                "SparkApp.CallControlBar.Main_CallStripButton_Audio_Right",
                "SparkApp.audioControlItem.buttonRowLayout.dualComboButtonLeftCell"
            ]
        }
    },

    "in_meeting": {
        "SKIP": {
            "6": [
                "Connect your calendar See and manage all your meetings here Connect",
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
            ],
            "6.8": [
                "Connect your calendar See and manage all your meetings here Connect",
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony2@mailinator.com",
                "IDToken2": "P@ss1234",
                "username": "allianz5",
                "password": "Happy123!@#"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony3@mailinator.com",                
                "IDToken2": "P@ss1234",
                "username": "allianz5",
                "password": "Happy123!@#"
            }
        },
        "END": {
            "6": [
                "audioButtonLeftCell"
            ],
            "6.8": [
                "SparkApp.CallTitleBar.userDevicePillButton"
            ]
        }
    },

    "calling": {
        "SKIP": {
            "6": [
                "Connect your calendar See and manage all your meetings here Connect",
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "remoteControlButton",
                "shareSomethingElseButton",
                "okButton",
                "CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.CallPanelTitleView.EscalationInviteAndMeetWidget.meetBtn",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton"
            ],
            "6.8": [
                "Connect your calendar See and manage all your meetings here Connect",
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "remoteControlButton",
                "shareSomethingElseButton",
                "okButton",
                "SparkApp.CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.CallPanelTitleView.EscalationInviteAndMeetWidget.meetBtn",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton"
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony2@mailinator.com",
                "IDToken2": "P@ss1234"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony2@mailinator.com",
                "IDToken2": "P@ss1234"
            }
        },
        "END": {
            "6": [],
            "6.8": []
        }
    },

    "schedule":{
        "SKIP": {
            "6": [
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "meetingTabHeader.startButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeStartButton",
                "narrowModeStartMenuButton"
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleMenuButton",
            ],
            "6.8": [
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "SparkApp.MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.titleFrame.meetingTypeWidget.meetingTypeInfoButton",
                "SparkApp.MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.stackedWidget.schedulingOptionsWidget.schedulingOptionsScrollArea.qt_scrollarea_viewport.schedulingOptionsContents.cohostOptionWidget.cohostInfoButton",
                "SparkApp.MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.stackedWidget.schedulingOptionsWidget.schedulingOptionsScrollArea.qt_scrollarea_viewport.schedulingOptionsContents.meetingOptionsWidget.meetingOptionsInfoButton",
                "SparkApp.MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.stackedWidget.schedulingOptionsWidget.schedulingOptionsScrollArea.qt_scrollarea_viewport.schedulingOptionsContents.meetingOptionsWidget.meetingOptionsButton",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "meetingTabHeader.startButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeStartButton",
                "narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleMenuButton",
            ]
        },
        "FORCE_VALIDATE":{
            "6":[
                "MeetingScheduleDialog.cancelMeetingMessageBox.topContainer.messageContainerWidget.okButton"
            ],
            "6.8":[
                "SparkApp.cancelMeetingMessageBox.topContainer.messageContainerWidget.okButton",
                "SparkApp.MeetingScheduleDialog.cancelMeetingMessageBox.topContainer.messageContainerWidget.okButton"
            ]
        },

        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony2@mailinator.com",
                "IDToken2": "P@ss1234"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony3@mailinator.com",                
                "IDToken2": "P@ss1234",
            }
        },
        "END": {
            "6": [
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton"
            ],
            "6.8": [
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton"
            ]
        }
    },

    "is_page": {
        "SKIP": {
            "6": [
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "animatedJoinButtonItem",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "scheduleItems.scheduleMeetingButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
            ],
            "6.8": [
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.animatedJoinButtonItem",
                "SparkApp.MeetingInterstitialPageView.MeetingInterstitialPageForVdi.meetingBodyViewItem.animatedJoinButtonItem",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "SparkApp.PopupDeviceConnectionFrame.PopupDeviceSearch.openSettingsButton",
                "SparkApp.SparkMessageBox.Can't start your camera.okButton",
                "scheduleItems.scheduleMeetingButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony2@mailinator.com",
                "IDToken2": "P@ss1234"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony3@mailinator.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bts_tony3@mailinator.com",
                "IDToken2": "P@ss1234"
            }
        },
        "END": {
            "6": [
                "audioControlItem.buttonRowLayout.dualComboButtonRightCell"
            ],
            "6.8": [
                "audioControlItem.buttonRowLayout.dualComboButtonRightCell"
            ]
        }
    },
    "app_core": {
        "SKIP": {
            "6": [
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.pmrButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.emailButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.audioButtonLayout.startAudioCallButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.videoButtonLayout.startVideoCallButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.VoicemailView.leftHandSideContainer.leftHandSide.voicemailTabWidget.utContextualHeaderWidget.contextualControlsWidget.callVoicemailBtn",
                "MainWindow.PopupWidget.CentralWidget.CallPreferencesPopupWidget.openButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.KeyboardShortcuts",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HealthChecker",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HelpCentre",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.WhatsNew",
                "MainWindow.CustomContactDialog.footButtonWidget.cancelButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "Copy link",
                "open settings",
                "Link kopieren",
                "actionButton_0",
                "actionButton_1",
                "actionButton_2",
                "avatar",
                "VoicemailSummaryDialog.summaryView.voicemailDetails.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.frame.callArea.audioCallButton",
                "VoicemailSummaryDialog.summaryView.voicemailDetails.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.frame.moreButtonLayout.moreButton",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "scheduleItems.scheduleMeetingButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
                "narrowModeStartButton",
                "meetingTabHeader.startButton",
                "meetingTabHeader.startMeetingButton",
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleButton",
                "meetingTabHeader.narrowModeScheduleMenuButton"
            ],
            "6.8": [
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.pmrButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.emailButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.audioButtonLayout.startAudioCallButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.videoButtonLayout.startVideoCallButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.VoicemailView.leftHandSideContainer.leftHandSide.voicemailTabWidget.utContextualHeaderWidget.contextualControlsWidget.callVoicemailBtn",
                "SparkApp.MainWindow.PopupWidget.CentralWidget.CallPreferencesPopupWidget.openButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.KeyboardShortcuts",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HealthChecker",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HelpCentre",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.WhatsNew",
                "SparkApp.MainWindow.CustomContactDialog.footButtonWidget.cancelButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton",
                "Copy link",
                "open settings",
                "Link kopieren",
                "actionButton_0",
                "actionButton_1",
                "actionButton_2",
                "avatar",
                "SparkApp.VoicemailSummaryDialog.summaryView.voicemailDetails.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.frame.callArea.audioCallButton",
                "SparkApp.VoicemailSummaryDialog.summaryView.voicemailDetails.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.frame.moreButtonLayout.moreButton",
                "SparkApp.PopupWidget.CentralWidget.CallPreferencesPopupWidget.openButton",
                "SparkApp.globalMenu.menuButtonScheduleMeeting",
                "SparkApp.globalMenu.menuButtonStartMeeting",
                "SparkApp.CustomContactDialog.mainArea.qt_scrollarea_viewport.displayWidget.updateAvatarButton",
                "SparkApp.PopupWidget.CentralWidget.ContactCardView.email",
                "callHistoryView.listView.callHistoryItem_0.QQuickRowLayout.avatar",
                "callHistoryView.listView.callHistoryItem_0.QQuickRowLayout.actionButton_2",
                "callHistoryView.listView.callHistoryItem_0.QQuickRowLayout.actionButton_1",
                "callHistoryView.listView.callHistoryItem_0.QQuickRowLayout.actionButton_0",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "scheduleItems.scheduleMeetingButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
                "narrowModeStartButton",
                "meetingTabHeader.startButton",
                "meetingTabHeader.startMeetingButton",
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleButton",
                "meetingTabHeader.narrowModeScheduleMenuButton",
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "pilan@allianzci.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "pilan@allianzci.com",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"pilan@allianzci.com",
                "IDToken2": "Happy123!@#",
                "username": "pilan",
                "password": "Happy123!@#"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "juntong@allianzci.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "juntong@allianzci.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"juntong@allianzci.com",
                "IDToken2": "Happy123!@#",
                "username": "juntong",
                "password": "Happy123!@#"
            }
        },
        "FORCE_VALIDATE": {
            "6": [
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.callsTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.whiteboardHubTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.contactTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.dialpadTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.UTBadgeTab_More",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.voicemailTabSelector",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton"
            ],
            "6.8": [
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.callsTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.whiteboardHubTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.contactTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.dialpadTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.meetTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.UTBadgeTab_More",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.voicemailTabSelector",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
            ]
        },
        "END": {
            "6": [
                "svgButton"
            ],
            "6.8": [
                "svgButton"
            ]
        }
    },

    "settings": {
        "SKIP": {
            "6": [
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.pmrButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.emailButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.audioButtonLayout.startAudioCallButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.videoButtonLayout.startVideoCallButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.VoicemailView.leftHandSideContainer.leftHandSide.voicemailTabWidget.utContextualHeaderWidget.contextualControlsWidget.callVoicemailBtn",
                "MainWindow.PopupWidget.CentralWidget.CallPreferencesPopupWidget.openButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.KeyboardShortcuts",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HealthChecker",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HelpCentre",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.WhatsNew",
                "MainWindow.CustomContactDialog.footButtonWidget.cancelButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.utContextualHeaderWidget.contextualControlsWidget.plusButtonWidget.plusButton",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "scheduleItems.scheduleMeetingButton",  
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
                "narrowModeStartButton",
                "meetingTabHeader.startButton",
                "meetingTabHeader.startMeetingButton",
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleButton",
                "meetingTabHeader.narrowModeScheduleMenuButton",
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsDropdown"
            ],
            "6.8": [
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.joinMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.pmrButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.emailButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.audioButtonLayout.startAudioCallButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.dialpadView.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.controlsContainerWidget.videoButtonLayout.startVideoCallButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.VoicemailView.leftHandSideContainer.leftHandSide.voicemailTabWidget.utContextualHeaderWidget.contextualControlsWidget.callVoicemailBtn",
                "SparkApp.MainWindow.PopupWidget.CentralWidget.CallPreferencesPopupWidget.openButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.KeyboardShortcuts",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HealthChecker",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.HelpCentre",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton.helpMenu.WhatsNew",
                "SparkApp.MainWindow.CustomContactDialog.footButtonWidget.cancelButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.utContextualHeaderWidget.contextualControlsWidget.plusButtonWidget.plusButton",
                "startMeetingItems.startMeetingButton",
                "meetingTabHeader.joinMeetingButton",
                "scheduleItems.scheduleMeetingButton",
                "buttonLayout.narrowModeJoinButton",
                "narrowModeScheduleButton",
                "narrowModeStartButton",
                "meetingTabHeader.startButton",
                "meetingTabHeader.startMeetingButton",
                "meetingTabHeader.narrowModeStartButton",
                "meetingTabHeader.narrowModeStartMenuButton",
                "meetingTabHeader.narrowModeJoinButton",
                "meetingTabHeader.narrowModeScheduleButton",
                "meetingTabHeader.narrowModeScheduleMenuButton",
                "meetingTabHeader.scheduleMeetingButton",
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsDropdown"
            ]
        },
        "INPUT_VALUES": {
            "6": {
                "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "allianz31@yopmail.net",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "allianz31@yopmail.net",
                "MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"allianz31@yopmail.net",
                "IDToken2": "Happy123!@#",
                "username": "allianz7",
                "password": "Happy123!@#"
            },
            "6.8": {
                "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bwc.sha+136@gmail.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bwc.sha+136@gmail.com",
                "SparkApp.MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.enterEmailField.UTTextField.textInput":"bwc.sha+136@gmail.com",
                "IDToken2": "Cisco!2345",
                "username": "allianz7",
                "password": "Happy123!@#"
            }
        },
        "FORCE_VALIDATE": {
            "6": [
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton"
            ],
            "6.8": [
                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.settingsButton"
            ]
        },
        "END": {
            "6": [
                "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton"
            ],
            "6.8": [
                # "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton"
            ]
        }
    }
}