import os
import platform


# Webex RegressShield Configurations
MODE_TOGGLE = 'PROD' # DEV or PROD

# TERMINATION_CONTROL = 'efbe2ccd0e7cb9c5265b510f36f8cef89ae85844ca8c34755a948c8b2cf10201' # Termination control path hash for End meeting
DB_TOGGLE = "ControlINFO" # Benchmark(ControlINFOBenchmark) or Current(ControlINFO)
TEST_CASE_DB = "testcase_db"
TC_DB = "test_case_db"
CONTROL_DB = "control_db"
ISSUE_DB = "issue_db"

# DB_PATHS = {
#     "ControlINFOBenchmark": r"src\db\ControlINFOBenchmark.db",
#     "ControlINFO": r"src\db\ControlINFO.db"
# }
# DB_PATH=DB_PATHS[DB_TOGGLE]
RECORD_FULL_CONTROL = True

# Application Initialization Controls
# Define possible initialization controls to check in order of priority
INITIALIZATION_CONTROLS = [
    'Sign in',
    ' Sign in'         # Main sign in control (note: has leading space to match dataset)
]

# Exact Match Controls
# Controls that require exact matching instead of partial matching (case-insensitive)
# Used to prevent false positives when locating sensitive controls like passwords
EXACT_MATCH_CONTROLS = [
    'Agree',
    'password',         # Password input fields
    'sign in',          # Sign in buttons/forms
    'sign out',         # Sign out buttons
    'login',            # Login buttons/forms
    'logout',           # Logout buttons
    'username',         # Username input fields
    'email',            # Email input fields
]
# Partial Match Controls
PARTIAL_MATCH_CONTROLS = [
    'close', 
]


NO_LOCATE_CONTROLS = ["Quit","Close AI FTE window",
                      "Focus on calling window","call agent","agent initWebex","Connect Webex Main Window","Place call",
                      "Direct Arrow Down Key Press","Direct Enter Key Press",
                      "Direct Arrow Up Key Press","Direct Arrow Left Key Press","Direct Arrow Right Key Press",
                      "Direct Space Key Press","Direct Tab Key Press","Direct Escape Key Press",
                      "Direct Tab key", "Direct Shift+Tab key"]
NO_LOCATE_CONTROLS_ACTION_TYPE = ["function", "api", "shortcut", "direct_key", "direct_input", "acc_sequence", "mouse"]


NO_RECORD_CONTROLS_ID = ["DisclaimerWidget.contentContainer.DisclaimerContentView.textWidget", 'SparkApp.DisclaimerWidget.contentContainer.DisclaimerContentView.textWidget']
NO_LOGGING_CONTROLS = [
    'DisclaimerWidget.contentContainer.DisclaimerContentView.textWidget',
    'SparkApp.DisclaimerWidget.contentContainer.DisclaimerContentView.textWidget'
]
OPTIMIZED_LOCATE_ININ_CONTROLS = ['OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.VideoBackgroundSettingWidget.virtualbackground_12_selected']
KNOWN_ISSUES_CONTROLS = []
KNOWN_ISSUES_CONTROL_CLASSNAME = ["UTListHeader","WRectangle_QMLTYPE"]
KNOWN_ISSUES_CONTROLS_ID = ['Grid','Raster','グリッド']
KNOWN_ISSUES_GROUP_BUTTON_ID = ["SparkApp.E911PopoutBrowser.bottomContainer.e911OkButton", "SparkApp.DisclaimerWidget.titlebar.closeButton", "SparkApp.DisclaimerWidget.titlebar.minButton"]
KNOWN_ISSUES_CONTROLS_TREE_ID = ['OptionsDialog.settingsTree', 'CallWindowDialog.OptionsDialog.settingsTree', 'MainWindow.OptionsDialog.settingsTree']
KNOWN_ISSUES_SAME_CONTROLS_DIFFERENT_RUNTIME_ID = ['Main_CallStripButton_AiAssistant']
KNOWN_ISSUES_NAVIGATOR_CONTROLS_ID = ['EulaAgreementWindow', 'EulaAgreementWindow.licenceText']
KNOWN_ISSUES_SKIP_CONTROLS_ID = ['MeetingGeneralTabWidget.connectToCalendar.chooseCalendarWidget.chooseCalendar', 'AuxiliaryDevicesOptionsWidget.DeviceTabPage.myDevicesContainer.activationCodePushButton','SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.AuxiliaryDevicesOptionsWidget.DeviceTabPage.myDevicesContainer.activationCodePushButton']
KNOWN_ISSUES_EMPTY_CONTROLS_ID_HASH = ['9fa28312ed668ce524a613c5464d1c949fed8304291602833fd31bdd6e7b1284', '8c4a2af002ca5eb48196f663449f49b9af7989d32264a0ad04635cb6e9c7c8ad']
KNOWN_ISSUES_SKIP_CONTROLS = ['General section,expanded, Use up and down arrow keys to navigate,use left arrow key to collapse and use right arrow key to expand,1 of 119']
KNOWN_ISSUES_CONTROLS_ID_TAB = ['MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0',
                                'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1',
                                'SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0',
                                'SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1',
                                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                                "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1"] 
KNOWN_ISSUES_PARENT_ID = ["MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingsStackedWidget.meetingContentWidget",
                          "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingsStackedWidget.meetingContentWidget", 
                          "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingsStackedWidget.calendarWidget.meetingListView",
                          "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingsStackedWidget.calendarWidget.meetingListView"]
CUSTOM_CONTROLS_SHORTCUT_ID = ['focusAnchorItem']
CUSTOM_CONTROLS_MENU_ID = ['MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton']
CONTROLS_NOTIFICATION_ID = ['notificationText']
SAME_CONTROLS = ['More sharing options', 'Was my name mentioned?', 'What are the action items?', 'Stop summary', ' More options Menu Button.', ' More options Menu Button.']
# DIFFERENT_CONTROLS = ['', 'More options']
SHORTCUT_BACK_CONTROLS = ['Stop annotation']

# WORKFLOW_CONTROLS = ['2', '3', '5', '6', '1.2', '1.3', '1.4', '1.1.1.5', '1.1.1.2.1.2', '1.1.1.2.1.3', '1.1.1.2.1.4', '1.1.1.2.1.5', '1.1.1.2.1.6']

SKIP_CLOSE_WINDOW = ['Control bar', 'Video and content', 'Header']
SKIP_CLOSE_WINDOW_BY_ID =["CallWindowDialogWindow.CallControlBar","CallWindowDialogWindow.MeetingContentView","CallWindowDialogWindow.CallTitleBar"]
SKIP_CONTROLS_ID = [
                    # Webex APP
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.bannerButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.bannerButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationFooterView.leftWidget.ucConnectionStatusView.statusWidget.actionA",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHe",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.collapseButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.utContextualHeaderWidget.contextualControlsWidget.discoverableFilterWidget.roundFilterButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.utContextualHeaderWidget.contextualControlsWidget.plusButtonWidget.plusButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_0",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_1",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_2",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_3",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.spaceWidget.CreateSpaceWidget.closeCreateSpaceButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.expandTabContainer.expandButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.collapseButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.userStatusButton",
                    "InputBoxContainer.SearchWidget.searchInputWidget.searchModifierInputWidget",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightMenuWidget.mainMenuActionsButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.aiAssistantButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.recentsTabSelector",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.previousDateButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.currentDateButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.nextDateButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.todayButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.bannerButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.VideoBackgroundSettingWidget._uploadButton",
                    "OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.backgroundScrollAreaContents.VideoBackgroundSettingWidget.backgroundScrollArea.qt_scrollarea_viewport.backgroundItemsFlowWidget._uploadButton",
                    "MainWindow.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.backgroundScrollAreaContents.VideoBackgroundSettingWidget.backgroundScrollArea.qt_scrollarea_viewport.backgroundItemsFlowWidget._uploadButton",
                    "MainWindow.AddContactDialog.selectGroupComboBox",
                    "MainWindow.OnboardingView.backButton",
                    "infoLayout.collapseButton",
                    "startMeetingItems.subStartMenuButton",
                    "scheduleItems.subScheduleButton",
                    "narrowModeScheduleMenuButton",
                    "narrowModeStartMenuButton",
                    "infoLayout.infoButton",
                    "meetingTabHeader.collapseButton",
                    "meetingTabHeader.subStartMenuButton",
                    "meetingTabHeader.subScheduleButton",

                    # settings
                    "GeneralTabWidget.defaultFileLocationFrame.changeDefaultFileLocationButton",
                    "GeneralTabWidget.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "CallWindowDialog.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.VideoBackgroundSettingWidget._uploadButton",
                    "OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.ScrollAreaWidget._uploadButton",
                    "MainWindow.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.VideoBackgroundSettingWidget._uploadButton",
                    'OptionsDialog.contentsContainer.AppearanceTabWidget.ThemeSelectorWidget.scrollArea.qt_scrollarea_viewport.scrollThemesWidget.ThemeButton',
                    'OptionsDialog.contentsContainer.NotificationsMessageTabWidget.resetMessageNotificationsButton',
                    'MainWindow.OptionsDialog.contentsContainer.AppearanceTabWidget.ThemeSelectorWidget.scrollArea.qt_scrollarea_viewport.scrollThemesWidget.ThemeButton',
                    'MainWindow.OptionsDialog.contentsContainer.NotificationsMessageTabWidget.resetMessageNotificationsButton',
                    "MessagingTabWidget.customDownloadWidget.changePathButton",
                    "MeetingJoinOptionsTabWidget.callbackNumbersWidget.managePhoneNumberButton",
                    "MeetingGeneralTabWidget.siteUrlFrame.Widget.editDefaultSiteUrlButton",
                    "MeetingGeneralTabWidget.siteUrlFrame.advancedSettingsButton", 
                    "MeetingGeneralTabWidget.personalRoomFrame.webEditPmrWidget.webEditPushButton",
                    "lobbyEditButton",
                    "MeetingGeneralTabWidget.connectToCalendar.chooseCalendarWidget.chooseCalendar",
                    "OptionsDialog.contentsContainer.GeneralTabWidget.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "MainWindow.OptionsDialog.contentsContainer.GeneralTabWidget.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "CallWindowDialog.OptionsDialog.contentsContainer.GeneralTabWidget.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "CallWindowDialog.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.ScrollAreaWidget.virtualbackground_3_uploadButton",
                    "MainWindow.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.ScrollAreaWidget.virtualbackground_3_uploadButton",
                    "OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.ScrollAreaWidget.virtualbackground_3_uploadButton",
                    
                    # in meeting
                    "DisclaimerWidget.declineBtn",
                    "portionButton",
                    "Main_CallStripButton_End",
                    "cancelButton",
                    "MoreMenu.EnableBreakoutSession",
                    "MoreMenu.StartSignInterpretation",
                    "MorePanelsMenu.Polling",
                    "MorePanelsMenu.ClosedCaptionPanel",
                    "discardMessageBox.messageContainerWidget.cancelButton",
                    "sharedSourceLink",
                    "downloadButton",
                    "newWhiteboardButton",
                    "CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "DiagnosticDetailsWidget.ExportDataDialog.messageContainerWidget.exportButton",
                    "CallWindowDialog.PopupWidget.CentralWidget.GiphyIntegrationWidget.giphyImageLayout.viewTermsButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.infoButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.infoButton",
                    "DisclaimerWidget.titlebar.minButton",
                    "DisclaimerWidget.titlebar.closeButton",
                    "CallWindowDialog.PopupDeviceConnectionFrame.PopupDeviceSearch.backButton",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.recents",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.smiley",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.people",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.foods",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.places",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.nature",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.symbols",
                    "CallWindowDialog.PopupWidget.CentralWidget.emojiPickerWidget.category.flags",
                    "CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.inputBoxSendButton",
                    "newWhiteboardButton",
                    "openforallButton",
                    "CallReactionWidget.HandGestureContainer.HandGestureAnchorButton",
                    "recordingMenu_saveOptions",
                    "annotateButton",
                    "PopUpPanel.PopupWidget.CentralWidget.GiphyIntegrationWidget.giphyImageLayout.viewTermsButton",
                    "ReportAnIssueNativeDialog.reportAnIssue.stackedWidget.ReportAnIssueDetailsWidget.dataStackedWidget.dataWidget.sendButton",
                    "shareSomethingElseButton",
                    "0.centralWidget.viewButton",
                    "previewButton",
                    "GeneralTabWidget.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "recordingMenu_recordingButton",
                    "MoreMenu.StepAway",
                    "MoreMenu.AddGuestToWebexMeeting",
                    "SourceButton_2_0",
                    "addFilesButton",
                    "discardMessageBox.topContainer.messageContainerWidget.cancelButton",
                    "LocalShareControlBar.previewButton",

                    # is page
                    "speakerAndMicrophoneView.speakerAndMicrophoneTextView.testButton",

                    #schedule
                    "MeetingScheduleDialog.scheduleViewContainer.scheduleView.basicWidget.scrollAreaUp.qt_scrollarea_viewport.scrollAreaWidgetContents.basicSettingWidget.topicWidget.topicEdit.clearInputButton",
                    "MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.webexSiteButton",
                    "MeetingScheduleDialog.StartTimeSelectPopupWidget.CentralWidget.ScheduleViewStartTimeListWidget.qt_scrollarea_viewport.ScheduleViewStartTimeItem",
                    "MeetingScheduleDialog.EndTimeSelectPopupWidget.CentralWidget.ScheduleViewEndTimeListWidget.qt_scrollarea_viewport.ScheduleViewEndTimeItem",
                     # emoji
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.recents",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.smiley",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.people",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.foods",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.places",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.nature",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.symbols",
                    "PopupWidget.CentralWidget.emojiPickerWidget.category.flags",

                    # app core
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.menuButtonWidget.navigateSpaceBackButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.settingsAction",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.helpSubMenu.askCommunityAction",
                    "MainWindow.PopupHealthCheck.healthCheckScrollArea.qt_scrollarea_viewport.healthCheckInfoHolder.dbHealthWidget.resetDatabase",
                    "MainWindow.PopupHealthCheck.healthCheckScrollArea.qt_scrollarea_viewport.healthCheckInfoHolder.dbHealthWidget.detailsButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.signOutAction",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.exitAction",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.PopupDeviceConnectionFrame.PopupDeviceSearch.openSettingsButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.PopupDeviceConnectionFrame.PairedDevicePopoverWidget.openSettingsButton",
                    "MainWindow.ConversationsForm.LastNewShareWidget.contentWidget.selectTableBar.goToPreferenceButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.MeetingViewPickerControls.nextDateButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.MeetingViewPickerControls.previousDateButton",
                    "MainWindow.CustomContactDialog.mainArea.qt_scrollarea_viewport.displayWidget.updateAvatarButton",
                    "ContactsTabProfileDialog.contactProfile.CustomContactDialog.mainArea.qt_scrollarea_viewport.displayWidget.updateAvatarButton",
                    "DiagnosticDetailsWidget.exportAllButton",
                    "PopupWidget.CentralWidget.ContactCardView.pmrButton",
                    "changePictureButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.availabilityMenu.manageQuietHoursMenuItem",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.helpSubMenu.generatePerformanceLogsAction",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.PopupWidget.CentralWidget.ContactCardView.email",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.VoicemailView.leftHandSideContainer.leftHandSide.voicemailTabWidget.voicemailContentWidget.voicemailListStackWidget.voicemailListPage.voicemailListWidget.qt_scrollarea_viewport.VoicemailListItem1.profileAvatarButton",
                    # calling
                    "MoreMenu.SendToVoicemail",
                    "MoreMenu.DiagnosticsStatistics",
                    "cleanModeButton",
                    "okButton",
                    "CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.CallPanelTitleView.EscalationInviteAndMeetWidget.meetBtn",


                    # temp skip
                    # "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.availabilityAction",
                    # "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.customStatusAction",
                    # "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton.applicationMenu.editProfileAction",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.mainMenuActionsButton",
                    "MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton"

                    ]
SKIP_CONTROLS_ID_QT68 = [
                    # Webex APP
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.bannerButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.bannerButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationFooterView.leftWidget.ucConnectionStatusView.statusWidget.actionA",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.joinMeetingLayoutWidget.joinMeetingButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHe",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.scheduleLayoutWidget.scheduleSubActionButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingSubActionButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.avatarButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.utContextualHeaderWidget.contextualControlsWidget.discoverableFilterWidget.roundFilterButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.utContextualHeaderWidget.contextualControlsWidget.plusButtonWidget.plusButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_0",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_1",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_2",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.roomListWidget.filterControlWidget.filterWidget.tabFilterOptions.mainConvoListTabs.tab_mainConvoListTabs_3",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.conversationSplitter.spaceWidget.CreateSpaceWidget.closeCreateSpaceButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.expandTabContainer.expandButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.helpButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_0",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.meetingsTabBar.tab_meetingsTabBar_1",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.callsTabSelector",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.collapseButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.collapseButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.userInfoWidget.userStatusButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.centerWidget.roomListTopBarWidget.topBarViews.topBarSearchWidget.WWidget.InputBoxContainer.SearchWidget.searchInputWidget.searchModifierInputWidget",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightMenuWidget.mainMenuActionsButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.rightDevicesWidget.userDeviceButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.rightWidget.aiAssistantButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.tabSelector.navigationWidget.recentsTabSelector",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.previousDateButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.currentDateButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.nextDateButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.meetingViewControls.MeetingViewPickerControls.todayButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "SparkApp.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.VideoBackgroundSettingWidget._uploadButton",
                    "SparkApp.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.backgroundScrollAreaContents.VideoBackgroundSettingWidget.backgroundScrollArea.qt_scrollarea_viewport.backgroundItemsFlowWidget._uploadButton",
                    "SparkApp.DisclaimerWidget.declineBtn",
                    'SparkApp.OptionsDialog.contentsContainer.AppearanceTabWidget.ThemeSelectorWidget.scrollArea.qt_scrollarea_viewport.scrollThemesWidget.ThemeButton','SparkApp.OptionsDialog.contentsContainer.NotificationsMessageTabWidget.resetMessageNotificationsButton',
                    'SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingGeneralTabWidget.siteUrlFrame.advancedSettingsButton',
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MessagingTabWidget.customDownloadWidget.changePathButton",
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingJoinOptionsTabWidget.callbackNumbersWidget.managePhoneNumberButton",
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingGeneralTabWidget.siteUrlFrame.Widget.editDefaultSiteUrlButton",
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingGeneralTabWidget.personalRoomFrame.webEditPmrWidget.webEditPushButton",
                    "SparkApp.LastNewShareWidget.contentWidget.shareSourceContainer.SharingAdvancedTabWidget.portionButton",
                    "SparkApp.CallControlBar.Main_CallStripButton_End",
                    "SparkApp.SparkMessageBox.cancelButton",
                    "SparkApp.WhiteboardPickerView.WhiteboardPickerView_QMLTYPE_.cancelButton",
                    "SparkApp.MoreMenu.EnableBreakoutSession",
                    "SparkApp.MorePanelsMenu.Polling",
                    "SparkApp.MorePanelsMenu.ClosedCaptionPanel",
                    "SparkApp.LocalShareControlBar.LocalShareControlBar_QMLTYPE_.sharedSourceLink",
                    "SparkApp.WhiteboardPickerView.WhiteboardPickerView_QMLTYPE_.QQuickLoader.newWhiteboardButton",
                    "SparkApp.CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "SparkApp.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "SparkApp.ExportDataDialog.messageContainerWidget.exportButton",
                    "SparkApp.PopupWidget.CentralWidget.GiphyIntegrationWidget.giphyImageLayout.viewTermsButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.stackedWidget.calendarEnabled.newAlertBanner.dismissButtonNew",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.infoButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.infoButton",
                    "SparkApp.DisclaimerWidget.titlebar.minButton",
                    "SparkApp.DisclaimerWidget.titlebar.closeButton",
                    "SparkApp.PopupDeviceConnectionFrame.PopupDeviceSearch.backButton",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.recents",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.smiley",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.people",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.foods",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.places",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.nature",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.symbols",
                    "SparkApp.PopupWidget.CentralWidget.emojiPickerWidget.category.flags",
                    "SparkApp.callStackedWidget.callWindowWidget.callDisplayWidget.sideStackedWidget.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.inputBoxSendButton",
                    "SparkApp.WhiteboardPickerView.WhiteboardPickerView_QMLTYPE_.openforallButton",
                    "SparkApp.UTMenu.UTMenuItemContainer.CallReactionWidget.HandGestureContainer.HandGestureAnchorButton",
                    "lobbyEditButton",
                    "SparkApp.ShareControlBarMoreMenu.QQuickListView_QML_.QQuickLoader.annotateButton",
                    "SparkApp.ShareControlBarMoreMenu.QQuickListView_QML_.QQuickLoader_QML_.annotateButton",
                    "SparkApp.SIManageView.UTRoundButton_QMLTYPE_",
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.CallsTabWidget.highlightToCallContainer.highlightToCallShortcutButton",
                    "SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingGeneralTabWidget.connectToCalendar.chooseCalendarWidget.chooseCalendar",
                    "SparkApp.ShareControlBarMoreMenu.QQuickListView_QML_.QQuickFocusScope.shareSomethingElseButton",
                    "SparkApp.MainWindow.OnboardingView.backButton",
                    "meetingTabHeader.collapseButton",
                    "infoLayout.collapseButton",
                    "startMeetingItems.subStartMenuButton",
                    "meetingTabHeader.subStartMenuButton",
                    "scheduleItems.subScheduleButton",
                    "narrowModeScheduleMenuButton",
                    "narrowModeStartMenuButton",
                    "infoLayout.infoButton",
                    "meetingTabHeader.subScheduleButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.applicationHeaderView.applicationHeaderWidget.leftWidget.mainMenuActionsButton",
                    "SparkApp.CallWindowDialog.callStackedWidget.callWindowWidget.callDisplayParentWidget.callDisplayWidget.sideStackedWidget.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "SparkApp.PopUpPanel.Frame.hostStackedWidget.MeetingChatContentWidget.mainStackedWidget.chatContainerWidget.ContainerContentWidget.conversationRenderer.inputBoxWidget.messageInputActionsWidget.ContainerWidget.gif_16",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.avatarButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.buttonsContainer.CallButtonsContainer.audioCallButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.buttonsContainer.CallButtonsContainer.videoCallButton",
                    "SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.ContactsTabWidget.leftHandSide.ContactList.stackedWidget.contactListTree.qt_scrollarea_viewport.ContactItemWidget.buttonsContainer.infoButton",
                   
                    # is page
                    "SparkApp.MeetingInterstitialPageView.QQuickPopupItem.avSettingsViewLoader.audioSettingsView.virtualBackgroundSettingsView.WRectangle_QMLTYPE__QML_.UTScrollView_QMLTYPE__QML_.virtualBackgroundDelegateItem",
                   
                    # settings
                    "SparkApp.OptionsDialog.contentsContainer.BackgroundTabWidget.Widget.BackgroundScrollArea.qt_scrollarea_viewport.ScrollAreaWidget.virtualbackground_3_uploadButton",
                    "SparkApp.OptionsDialog.contentsContainer.GeneralTabWidget.scrollArea.qt_scrollarea_viewport.scrollAreaWidgetContents.defaultFileLocaltionFrame.changeDefaultFileLocationButton",
                    "SparkApp.OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.audioTabAdvancedFooter.audioTabAdvancedButton",
                    "SparkApp.OptionsDialog.contentsContainer.VideoTabWidget.VideoTabStackWidget.VideoTabPage.videoTabAdvancedFooter.videoTabAdvancedButton",                

                    # in meeting
                    "SparkApp.RecordControlPopupView.RecordControlView_QMLTYPE_.recordingMenu_saveOptions",
                    "SparkApp.RecordControlPopupView.RecordControlView_QMLTYPE_.recordingMenu_recordingButton",
                    "SparkApp.discardMessageBox.messageContainerWidget.cancelButton",
                    "SparkApp.LocalShareControlBar.previewButton",
                    "SparkApp.ShareControlBarMoreMenu.QQuickListView_QML_.QQuickLoader.cleanModeButton",
                    "SparkApp.RecordControlPopupView.recordingMenu_recordingButton",
                    "SparkApp.WhiteboardPickerView.openforallButton",
                    "SparkApp.MoreMenu.StepAway",
                    "SparkApp.shareDialog.ShareDialogBodyView_QMLTYPE_541.UTFlickable_QMLTYPE_284.ComboBox_Sort by",
                    "SparkApp.discardMessageBox.topContainer.messageContainerWidget.cancelButton",

                    # is page
                    "SparkApp.MeetingInterstitialPageView.QQuickPopupItem.avSettingsViewLoader.audioSettingsView.speakerAndMicrophoneView.speakerAndMicrophoneTextView.testButton",

                    #schedule
                    "SparkApp.MeetingScheduleDialog.scheduleViewContainer.scheduleView.basicWidget.scrollAreaUp.qt_scrollarea_viewport.scrollAreaWidgetContents.basicSettingWidget.topicWidget.topicEdit.clearInputButton",
                    "SparkApp.MeetingScheduleDialog.scheduleViewContainer.advancedSettingView.webexSiteButton",
                    "SparkApp.StartTimeSelectPopupWidget.CentralWidget.ScheduleViewStartTimeListWidget.qt_scrollarea_viewport.ScheduleViewStartTimeItem",
                    "SparkApp.EndTimeSelectPopupWidget.CentralWidget.ScheduleViewEndTimeListWidget.qt_scrollarea_viewport.ScheduleViewEndTimeItem",
                    "SparkApp.MeetingScheduleDialog.scheduleViewContainer.scheduleView.basicWidget.attendeeWidget.inviteesStackedWidget.inviteesWidget.removeAllInviteeButton",
                    "SparkApp.MeetingScheduleDialog.scheduleViewContainer.scheduleView.basicWidget.scrollAreaDown.qt_scrollarea_viewport.scrollAreaWidgetContents_2.scheduleButton",
                    ]

MORE = ['More option','Weitere Optionen','その他のオプション','Mwy o opsiynau']
# CONTROL_OPEN_STATE = ['Hide AI Assistant panel (Alt + I), selected', 'Apps panel, selected', 'Participants panel, selected', 'Hide chat, selected']
CONTROL_OPEN_STATE = ['selected', 'Hide']
CONTROL_CLOSE = ['close']

SKIP_CONTROLS_PATH_HASH = ['6afbf22a378e8d83afd189735ae5f46836aa2c1ba6c0ab5de9feddb0a46538d1']
SKIP_CONTROLS_CLASS_NAME = [
                            'UTRoundButton_QMLTYPE_48_QML_705',
                            'Button_QMLTYPE_11_QML_1286', 'UTRoundButton_QMLTYPE_83_QML_1288', 
                            'UTRoundButton_QMLTYPE_72', 'VhBttYbXVAnaFjcXVGXA1A==', 
                            'j-o1xlHvXJ4tRX7VUK0Ogg== ', 'j-o1xlHvXJ4tRX7VUK0Ogg== _51q68GCr9yFCo61HGv0pSw==', '_8WLMmEwlhrGrjvyQySCBAA==',
                            'Button_QMLTYPE_9_QML_657','i-pencil','sidebar_tab Performance',
                            'sidebar_tab Statistics','navBarItem Audio','navBarItem Video',
                            'navBarItem ShareContent'
]

SKIP_NAVIGATE_CONTROLS_LIST_ITMES = [
                            'Has meeting summary. Has transcript. To activate press enter, press SHIFT+F10 for more options,',
                            'meeting. list item.',
                            'SHIFT+F10'
]

NO_TRAVERSE_CONTROLS_ID = [
                            'OptionsDialog.contentsContainer.KeyboardShortcutsTabWidget.SparkMessageBox.messageContainerWidget.okButton',
                            'PrivacyTabWidget.BlockedContactsDialog.closeButton',
                            'OptionsDialog.contentsContainer.VideoTabWidget.VideoTabStackWidget.VideoTabPage.previewWidget.VideoPreviewWidget.widget1.mVideoRotationButton', 'indicator',
                            'MeetingGeneralTabWidget.personalRoomFrame.currentPersonalRoomWidget.personalRoomLinkContentWidget.copyPersonalRoomLinklButton', 
                            'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.infoButton',
                            'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.copyButton',
                            'OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget_3.ringerTestButton', 
                            'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.collapsedLine.copyButton',
                            'OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget_2.microphoneTestButton',
                            'OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget.speakerTestButton'
                           ]

NO_TRAVERSE_CONTROLS_ID_QT68 = ['SparkApp.OptionsDialog.contentsContainer.VideoTabWidget.VideoTabStackWidget.VideoTabPage.previewWidget.VideoPreviewWidget.widget1.mVideoRotationButton', 'SparkApp.CallTitleBar.indicator',
                           'SparkApp.OptionsDialog.contentsContainer.UTScrollArea.qt_scrollarea_viewport.WWidget.MeetingGeneralTabWidget.personalRoomFrame.currentPersonalRoomWidget.personalRoomLinkContentWidget.copyPersonalRoomLinklButton', 
                           'SparkApp.OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget_3.ringerTestButton', 
                           'SparkApp.OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget_2.microphoneTestButton',
                           'SparkApp.OptionsDialog.contentsContainer.AudioTabWidget.audioTabStackWidget.audioTabPage.scrollArea.qt_scrollarea_viewport.scrollWidgetContents.widget.speakerTestButton'
                           ]

NO_TRAVERSE_CONTROLS_CLASS_NAME = ['VideoBackgroundSettingButton', 'UTMoreInfoButton', 'UTMoreInfoButton_QMLTYPE_605']

# Different controls for handling, need to be validated 
# 1. cancel from search, 3300d7b4e4d12a58726344b5793134c76746404df6118893f79a18386cdde4dd
# 2. cancel from Report an issue, 0dcf8f764665d50c8c3adc594103e9a0c17d2ea65bc0b629f268df2ebd6054f5
# 3. Back to meeting from Step away from meeting, c670c9a87f307ab196d30e25d765e0f05f40a8fe0c76b284a4cfa6de4e87d7f5
# 4. cancel Give remote control, to remove ac7772b76f018a76eb840216e423f364ef79a3d9b3b0885f06fc393c3629ff7c
FORCE_VALIDATE_CONTROLS_PATH_HASH = ['4ce2bbe0440d4dcb2c51ba60ce44e5797e52ad6c93595292e0aa817402f33151',
                                     '3a08c92944376f09d79a4252dd71709b89de561f079b597c3dd5a0df2772896c',
                                     '02e359b67d7ed7ca64266981f3250f72293a1dcdd57c1ff4e3e2c6134379051e',
                                     '53fcb1463e1f59dc459456c1bd356129d107ecbd102ba907b02451a2fff83307',
                                     'e96abb04b3b545c1c4e818e0c448686f75f77e6d7b5194e2e2ff77962bcfd28a',
                                     '160c3ac148e3b500c43ddef09c09c07cd9a517b44e01f4225d6e3849f640564d',
                                     '05b2ba03e753b91be1b7aa4caf67cc18244f4a79299ab2d27052efc981143ca9',
                                     'c8447758da2f7b8cc873d8f4df925612be7ae5af02ffa29e6e41fcee16641a16',
                                     'aedcfa38ebccf3e37e401c246c04fb25cad74d7b93e9da23cea6cffe42c784d9',
                                     '08da684730a84822fa2048213569c17daa9cdca27f2c3ac8e6d179d3cc97b7ff',
                                     'c670c9a87f307ab196d30e25d765e0f05f40a8fe0c76b284a4cfa6de4e87d7f5', 
                                     '3300d7b4e4d12a58726344b5793134c76746404df6118893f79a18386cdde4dd', 
                                     '0dcf8f764665d50c8c3adc594103e9a0c17d2ea65bc0b629f268df2ebd6054f5',
                                     '7ef70be17552566d73901198d4626b8b594f759329a28082403c520a525f2fa4' # cy: back to meeting
                                    ]

# FORCE_VALIDATE_CONTROLS = ['Microphone is currently unmuted - click to mute', 'Audio options', 'Sending video is currently enabled - click to disable', 'Video options' ]
FORCE_VALIDATE_CONTROLS_CLASS_NAMES = ['xxxxx'] # UTBadgeTab
FORCE_VALIDATE_CONTROLS_ID = [
                              'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.nextButton',
                              'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nextButton',
                              'SparkApp.ReportAnIssueNativeDialog.reportAnIssue.stackedWidget.ReportAnIssueDetailsWidget.dataStackedWidget.dataWidget.cancelButton',
                              'ReportAnIssueNativeDialog.reportAnIssue.stackedWidget.ReportAnIssueDetailsWidget.dataStackedWidget.dataWidget.cancelButton'
                              ]
MULTI_STATE_CONTROL_FROM_CLASS_NAMES = ['UTBadgeTab']

# Webex APP SignIn Configurations
INPUT_FIELD_VALUES = {
    "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedMeetingInfoWidget.dataStackedWidget.dataWidget.userInput.UTTextField.textInput": "binbiwan.cisco@webex.com",
    "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nameInput.UTTextField.textInput": "bts tony1",
    "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.emailInput.UTTextField.textInput": "bts_tony1@mailinator.com",
    "enter-meeting-number-label": "binbiwan.cisco@webex.com",
    "react-aria2322965287-12": "bts tony1",
    "react-aria2322965287-17": "bts_tony1@mailinator.com",
    "MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.UTTextField.textInput": "bts_tony2@mailinator.com",
    "IDToken2": "P@ss1234"
}

INPUT_FIELD_VALUES_BY_NAME = {
    "Type your email address, required": "binbiwan.cisco@webex.com",
    "Type your name, required": "bts tony1",
    "Name (required), Textbox, Type in your name": "bts tony1"
}

current_os = platform.system().lower()
APP_WINDOW_LIST = {}
# Webex APP SignIn Configurations
ACCOUNT = {}


if current_os == 'windows':
    ACCOUNT = {# Webex APP SignIn Configurations
        "control_username_id": "Sign inStart by entering your email address.|50004|MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.enterEmailField.textInput",
        "control_password_id": "Password |50004|IDToken2",
        "username": "cvgatsbeta7@mailinator.com",
        "password": "Happy123!@#"
    }
elif current_os == 'darwin':
    ACCOUNT = {# Webex APP SignIn Configurations
        "control_username_id": "Sign in, Start by entering your email address.|AXTextField|login_email_address",
        "control_password_id": "Password|AXTextField|",
        "username": "cvgatsbeta7@mailinator.com",
        "password": "Happy123!@#"
    }



# Webex Troubleshooting Configurations
BEGIN_CONTROL_NUMBER = -1
END_CONTROL_NUMBER = -1
END_CONTROL_NUMBER_LEVEL = 200

# SPECIAL_BUTTONS means the buttons that need to be skipped
SPECIAL_BUTTONS = ["Open AI Assistant panel (Alt + I)","Suggestions for you, Slido, Polling and Q&A in Webex, 1 of 8, use arrow keys to navigate the apps, press enter key to open the app, use Shift + F10 for more options","Create breakout sessions","New whiteboard","Open for all","Disclaimer","Privacy policy","Developer support","Slido guidesLink, Press enter to activate it","Slido pageLink, Press enter to activate it","Open video"," Turn on Markdown","Your report and log files will be sent to Cisco to resolve technical problems and may be shared with your administrator. By sending this report, you accept the Cisco Online Privacy Statement","New whiteboard","Learn more about keyboard navigation","Disconnect"," Add mention"," Add Giphy"," Add Giphy, menu item, has popup","Step away from meeting, Button, Step away from the meeting to mute your microphone, turn off your video, and set your status to Stepped away.","Invite people","Invite and remind, Menu item, 2 of 10","Step away from meeting, Menu item, 7 of 10"," Close"," Close ","Close app panel", "Minimize", "Maximize", "Close window", " Back", " Done", "Change sharing preferences", " Back to sharing settings"]
SPECIAL_ACTIVE_BUTTONS = ["Back to meeting"," Discard", "Cancel", "Step away from meeting, Button, Step away from the meeting to mute your microphone, turn off your video, and set your status to Stepped away."]
SPECIAL_MENU = ["End meeting, Menu item","End meeting: Menu item {1,?}"]
SKIP_LOCATE = [" Thumbs up (Alt + Shift + 4)","Video and content"]
CLOSE_BUTTON = ["Close"]
STOP_BUTTON = ["Stop sharing (Ctrl + Shift + Z)"]
BACK_BUTTON = ["Back to Apps"]
Others = [" Add virtual background, For best results, use an image file or a video file with a resolution that is 480 x 360 pixels or higher but does not exceed 1920 x 1080 pixels.3 of 12, "]

# Common Action Configurations
FIRST_LAYER_CONTROLS = []
SECOND_LAYER_CONTROLS = []
CONTROLS = []
DEFAULTFROMCONTROL = "root"
VALIDATEDCONTROLS = []

FTE = False

DOWNUP = "DownUp"
LEFTRIGHT = "LeftRight"

# Webex APP Configurations
CONTROL_PATH = 'src\\config\\controls_wbx.json'
CLOSE_BUTTON_SECOND_LAYER_CONTROL = ["Close panel", "Close ", "Close", " Close", "Close app panel"]

# Webex Window Configurations
CLASS_NAME = 'MainWindow'
CALLWINDOWAUTOID = 'CallWindowDialog'
CALLCONTROLBARAUTOID = "CallWindowDialogWindow.CallControlBar"
AUDIOCONTROLAUTOID = "Main_CallStripButton_Audio"
MAINWINDOW = 'MainWindow'
MAINWINDOW_QT68 = 'SparkApp.MainWindow'
JOIN_A_MEETING_AUTOID = 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton'
JOIN_A_MEETING_AUTOID_QT68 = "SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingStartWidget.dataStackedWidget.dataWidget.joinMeetingButton"
AGREEMENT_AUTOID = 'EulaAgreementWindow.applyButton'
AGREEMENTWINDOW='EulaAgreementWindow'
START_JOIN_BUTTON = 'animatedJoinButtonItem'

# Webex Meeting Configurations
WAIT_CONTROLER_TIME = 0.1
WAIT_CONTROLER_ACTION_TIME = 1
WAIT_WINDOW_ACTION_TIME = 5
WAIT_WINDOW_ACTION_SHORT_TIME = 3
WAIT_LONG_TIME = 5
WAIT_SHORT_TIME = 3
WAIT_LOADING_TIME = 10
WAIT_LONG_TIME_BUTTONS = ["Create a new whiteboard","Auf den neuesten Stand bringen",'Share', "Join meeting Tony Wang Wang's Personal Room", "Join as a guest", "Join meeting, , Computer audio, Unmuted, Video on.", "Start meeting, , Computer audio, Unmuted, Video on.", "Join meeting Tony Wang Wang's Personal Room", "Join as a guest", "Join meeting, , Computer audio, Unmuted, Video on.", "Start meeting, , Computer audio, Unmuted, Video on.", "Slido (polling and QA), Menu item, 1 of 3, Unselected", "New whiteboard", "Apps", "Enable breakout sessions, Switch button, off, 5 of 10", 'Catch me up','Apps panel', 'Start video (Ctrl + Shift + V)', 'Enable breakout sessions, Switch button, off, 5 of 10']
WAIT_LONG_TIME_BUTTONS_ID = ['animatedJoinButtonItem', 'MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton', 'MorePanelsMenu.Polling','Main_CallStripButton_AppExtension','MoreMenu.EnableBreakoutSessions',"Main_CallStripButton_Video"]
WAIT_LONG_TIME_BUTTONS_ID_QT68 = ['SparkApp.MeetingInterstitialPageView.MeetingInterstitialPageForVdi.meetingBodyViewItem.animatedJoinButtonItem','SparkApp.MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton','SparkApp.CallControlBar.Main_CallStripButton_AppExtension','SparkApp.CallControlBar.Main_CallStripButton_Video']
WAIT_SHORT_TIME_BUTTONS = ['Catch me up', 'Was my name mentioned?', 'What are the action items?', 'Last 15 minutes, Menu Item, 1 of 2', 'From the summary start, Menu Item, 2 of 2', ' Accept', " Schedule a meeting. Share a link and meet later", " Check for updates", " Check for updates", "Statistics, Menu item, 10 of 10", "Breakout sessions", "Close whiteboard","Audio Settings..., Menu item","Stop sharing (Ctrl + Shift + Z)", 'Start', 'Disconnect', 'Stop summary', 'Back to meeting', 'Share content (Ctrl + Shift + D)', 'View', 'Stop video (Ctrl + Shift + V)', ' Change sharing preferences', "You're sharing Screen 1\nSelect to share something else."]
WAIT_SHORT_TIME_BUTTONS_ID = ["DisclaimerWidget.acceptBtn","okButton", "MoreMenu.DiagnosticsStatistics","Main_CallStripButton_BreakoutManagement","stopShare","okButton","CallWindowDialog.LastNewShareWidget.contentWidget.selectTableBar.goToPreferenceButton"]
WAIT_LONG_TIME_BUTTONS_10s = ['MainWindow.signOutMessageBox.messageContainerWidget.okButton', ' Share', ' Next', ' Sign In ', " Start meeting. Meet in my personal room. Start a personal room meeting"]
WAIT_LONG_TIME_BUTTONS_10S_ID = ['MainWindow.OnboardingView.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.nextButton.pillButton','MainWindow.ConversationsForm.topLevelStack.mainAreasWidget.sidePanelSplitter.rightSideStack.UnifiedMeetingViewWidget.splitter.mainStackedWidget.calendarMainWidget.meetingsHeadWidget.MeetingsHeadView.expandedLine.startMeetingLayoutWidget.startMeetingButton','signIn','Button1', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingConvergedGuestInfoWidget.dataStackedWidget.dataWidget.nextButton', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.nextButton', 'MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpChooserWidget.dataStackedWidget.dataWidget.nextButton', 'CallWindowDialog.LastNewShareWidget.contentWidget.footWidget.startShareButton']
WAIT_LONG_TIME_BUTTONS_10S_ID_QT68 = ["SparkApp.MainWindow.OnboardingView.onboardingScreen.stackedWidget.normalViewsPage.onboardingStackWidget.OnboardingSignInUpEmailWidget.dataStackedWidget.dataWidget.nextButton","SparkApp.LastNewShareWidget.contentWidget.footWidget.startShareButton"]
# Define ANSI color codes   
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

FOREGROUND_WINDOW_CLASS_NAME = ["WhiteboardContainerNativeDialog","AssociationCallWidget","MainWindow.UCLoginWidget"]
OUTPUT_NAME = 'wrs-output'
DATA_RETENTION_DAYS = 3

# Default Webex notification room IDs
DEFAULT_WINDOWS_ROOM = "c0af0ac0-772f-11ef-9431-6382b932281b"
DEFAULT_MAC_ROOM     = "a83fa300-818d-11f0-9d5c-fb6fa60d4c49"
PROMOTE_BLUE_ROOM    = "74988770-ca6b-11f0-b2ff-8d13d1d24d2e"

BUG_REPORT_LIMIT = 15

AI_URL = "http://wrs.qa.webex.com:9901/secret_service/get_client_secret/"

# OpenAI agent configuration (default)
AI_PARAMS = {
    "client_id": "2da4bbc8-5520-4c39-bd9a-404206511e0d",
    "client_secret": "PGxy7HnEdedhmGQOfDkGgc6T8DR3sg-shjp1GnzC1i4",
    "agent_type": "openai"
}

# Control Hub agent configuration
CONTROLHUB_PARAMS = {
    "client_id": "2da4bbc8-5520-4c39-bd9a-404206511e0d",
    "client_secret": "PGxy7HnEdedhmGQOfDkGgc6T8DR3sg-shjp1GnzC1i4",
    "agent_type": "controlhub"
}

# Agent configurations mapping
AGENT_PARAMS = {
    "openai": AI_PARAMS,
    "controlhub": CONTROLHUB_PARAMS
}