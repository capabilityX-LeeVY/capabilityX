import time

from common.startup.startup_initializer import StartupInitializer
from core.mac.RSApplication import CRSApplication
from config.paths import SETTINGS_PATH, FEATURE_TOGGLE_CONFIG_PATH,LOG_PATH,DB_CONFIG_PATH
from common.utils.featureToggle import FeatureToggle
from rs_sdk.utils.control_db import ControlDB
from tools.webexApp import appHandler
from core.mac import presetProcess
from core.mac.WBXTraversalMgr import CWBXTraversalMgr
from navigationJiraReporter_mac import CNavigationJiraReporter
from config.mysql import ConnectToDB
from datetime import datetime
import pytz
from common.handler.settingsHandler import DynamicConfig
from db.cloudMySQL import accData
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
import subprocess

from core.mac.RSSkipMgr import CRSSikipMgr
import psutil
from core.mac.GTManager import GTManager
import os

def webexInitialize():
    appHandler.installWebex()       
 
def runPresetProcesses():       
    if FeatureToggle.isDisabled("installer"):
        appHandler.initWebex()
    presetProcess.handleProcesses() 

def Naviagtion():           
    #CWBXTraversalMgr.TraversalTheMeeting(isDeep=False)
    CWBXTraversalMgr.TraversalTheWebex_HighLayer()
                     

def _isContinueMode():
    settings = DynamicConfig(SETTINGS_PATH)
    continue_mode = settings.get("continueRun")
    return continue_mode

def CleanWebexData():
     if _isContinueMode() == False:
        cmd = "rm -rf ~/Library/Logs/SparkMacDesktop/*"
        subprocess.run(cmd, shell=True)

def PackageWebexLogs():
     tar_filename = f"{LOG_PATH}/WebexLogs_{time.strftime('%Y%m%d_%H%M%S')}.tar.gz"
     subprocess.run(f'tar -zcvf {tar_filename} ~/Library/Logs/SparkMacDesktop/', shell=True, check=True)

def CreateNavigationDB(name = "InMeeting"):
    dbConnection = ConnectToDB()
    settings = DynamicConfig(SETTINGS_PATH)
    app_version = str(settings.get('appVersion')).split('.')
    version = f'''{app_version[0]}.{app_version[1]}'''
    language = settings.get("language")
    env = settings.get('environment')
    #schema = DynamicConfig(DB_CONFIG_PATH).get("dbConfig")[env]['dbName']
    newSchema = f'''RegressShield_Navigation_Mac_Deep_{version}'''
    results, _  = dbConnection.Query('''show databases;''')
    datebaseNames = [f[0] for f in results]
    if newSchema not in datebaseNames:
        dbConnection.Execute(f'''CREATE DATABASE IF NOT EXISTS `{newSchema}`;''')
        dbConnection.Execute(f'''USE `{newSchema}`;''')

    tableName = f'''`{newSchema}`.`{language}_{name}`'''
    if _isContinueMode() == True:
        sql = [
            "SET SQL_SAFE_UPDATES = 0;",
            f'''UPDATE {tableName} SET `status` = '' WHERE (`status` = 'validate failed') and (`level` = 1)'''
        ] 
        for query in sql:
            dbConnection.Execute(query) 

        return tableName
    
    sql = f'''DROP TABLE IF EXISTS {tableName};'''
    dbConnection.Execute(sql)

    sql = f'''
CREATE TABLE {tableName} (
  `controlID` varchar(255) NOT NULL,
  `product` varchar(45) NOT NULL,
  `processID` varchar(45) NOT NULL,
  `order` int NOT NULL,
  `level` int DEFAULT NULL,
  `date` varchar(45) NOT NULL,
  `timestamp` varchar(255) DEFAULT NULL,
  `controlName` text,
  `status` varchar(45) DEFAULT NULL,
  `pathInfo_Names` text,
  `label` text,
  `title` text,
  `value` text,
  `help` text,
  `otherInfo` text,
  `otherInfoType` text,
  `enable` varchar(45) DEFAULT NULL,
  `selected` varchar(45) DEFAULT NULL,
  `identifier` text,
  `frame` text,
  `postion` text,
  `role` text,
  `roleDescription` text,
  `subRole` text,
  `action` varchar(45) DEFAULT NULL,
  `parent` varchar(128) NOT NULL,
  `parentRole` text,
  `partString` text,
  `fromControl` varchar(128) NOT NULL,
  `windowName` text,
  `memory` text,
  `error` text,
  `isDeep` tinyint DEFAULT '0',
  `needValidate` tinyint DEFAULT NULL,
  `pathInfo` text,
  `pathHash` text,
  `skip` tinyint DEFAULT '0',
  PRIMARY KEY (`controlID`,`product`,`processID`,`order`,`date`,`parent`,`fromControl`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
'''
    dbConnection.Execute(sql)

    settings.set("macOSnavigationTableName", tableName)
    return tableName    

def runPresetProcessesEx(processIDs: list):
    language_code = DynamicConfig(SETTINGS_PATH).get("language")
    results = accData.selectProcessSteps(language_code=language_code,processIDs = processIDs)
    processesNavigator = presetProcess.ProcessesNavigation()
    if results is not None:
        for _, row in results.iterrows():
            processesNavigator.navigateByTabForProcesses(row['controlName'], row['controlType'], row['controlIdentifier'], row['controlAction'], row['processName'], row['processID'], row['projectID'], row['controlActionWaitTime'])

def Naviagtion_Deep_InMeeting():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   
     
    tableName = CreateNavigationDB(name = "InMeeting")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")

    if _isContinueMode() == False:
        gt_yaml_file = "travel/navigation_to_meeting.yaml"
        GTManager.run_by_file(gt_yaml_file , language)

    #runPresetProcessesEx(processIDs=[0,1,2,3,4,5])
    CWBXTraversalMgr.TraversalTheMeeting(isDeep=True,tableName=tableName, continueMode=_isContinueMode(),productName="InMeeting")
    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)
    return tableName    
    

def Naviagtion_Deep_Login():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   

    tableName = CreateNavigationDB("Login")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_sign_in.yaml"
    GTManager.run_by_file(gt_yaml_file , language)
    #runPresetProcessesEx(processIDs=[0,])  # Run preset processes for login
    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="Login")
    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName, bundleID="Cisco-Systems.Spark", windowNameReg="^Webex.*$")
    return tableName

def Naviagtion_Deep_ISPage():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   
 
    tableName = CreateNavigationDB("IsPage")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_is_page.yaml"
    GTManager.run_by_file(gt_yaml_file , language)
    #runPresetProcessesEx(processIDs=[0,1,2,3,4])  # Run preset processes for isPage 
    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="IsPage") 
    config = CRSSikipMgr.ReadConfig()
    sql = [
         "SET SQL_SAFE_UPDATES = 0;",
        f'''UPDATE {tableName} SET `status` = 'validated skiped' WHERE (`controlName` = '{config["specialNames"]["StartMeeting"]}')'''
    ] 
    dbconnection = ConnectToDB()
    for query in sql:
        dbconnection.Execute(query)                
    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)  
    return tableName

def Naviagtion_Deep_Schedule():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   

    tableName = CreateNavigationDB("Schedule")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_schedule.yaml"
    GTManager.run_by_file(gt_yaml_file , language)

    #runPresetProcessesEx(processIDs=[0,1,2,6])  # Run preset processes for schedule
    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName, productName="Schedule") 
    config = CRSSikipMgr.ReadConfig()
    sql = [
         "SET SQL_SAFE_UPDATES = 0;",
         f'''UPDATE {tableName} SET `status` = 'validated skiped' WHERE (`controlName` = '{config["specialNames"]["Schedule"]}')''',
         f'''UPDATE {tableName} SET `status` = 'validated skiped' WHERE (`controlName` = '{config["specialNames"]["Cancel"]}')'''
    ] 
    dbconnection = ConnectToDB()
    for query in sql:
        dbconnection.Execute(query)

    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)
    return tableName

def Naviagtion_Deep_AppCore():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   

    tableName = CreateNavigationDB("AppCore")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_app_core.yaml"
    GTManager.run_by_file(gt_yaml_file , language)

    #runPresetProcessesEx(processIDs=[0,7])  # Run preset processes for login
    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="AppCore")

    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName, bundleID="Cisco-Systems.Spark", windowNameReg="^Webex.*$")
    return tableName

def Naviagtion_Deep_AIAssistant():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   
 
    tableName = CreateNavigationDB("AIAssistant")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_AIAssistant.yaml"
    GTManager.run_by_file(gt_yaml_file , language)

    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="AIAssistant")           
    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)  
    return tableName

def Naviagtion_Deep_Settings():
    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   
 
    tableName = CreateNavigationDB("Settings")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_audio_settings.yaml"
    GTManager.run_by_file(gt_yaml_file , language)

    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="Settings")           
    CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)  
    return tableName

def CallToAnswerTheCall():
    import requests
    api_endpoint = "http://10.224.118.137:9909/api/run_calling_functions"

    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(api_endpoint, headers=headers)
    if response.status_code == 200:
        print("Call answered successfully.")
        return True
    else:
        print("Failed to answer the call.")
        return False


def InitCall():
    import requests
    api_endpoint = "http://10.224.118.137:9909/api/run_init_app_functions"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(api_endpoint, headers=headers)
    if response.status_code == 200:
        print("InitCall successfully.")
        return True
    else:
        print("Failed to InitCall.")
        return False
      
def Naviagtion_Deep_Calling():
    from core.mac.RSKeyboard import CRSKeyboard
    InitCall()

    if FeatureToggle.isEnabled("installer"):
        webexInitialize()   

    tableName = CreateNavigationDB("Calling")
    settings = DynamicConfig(SETTINGS_PATH)
    language = settings.get("language")
    gt_yaml_file = "travel/navigation_to_calling.yaml"
    GTManager.run_by_file(gt_yaml_file , language)

    #runPresetProcessesEx(processIDs=[0,7,8,9]) 
    CRSKeyboard.EnterPressed()
    
    #//call API to answer the call
    if CallToAnswerTheCall() == False:
        raise Exception("Failed to answer the call via API")
    
    CWBXTraversalMgr.TraversalThePreMeeting(isDeep=True,tableName=tableName,productName="Calling")
    app = CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName, bundleID="Cisco-Systems.Spark", windowNameReg="^(?!Webex).*$")
    config = CRSSikipMgr.ReadConfig()
    CWBXTraversalMgr.FindControlByNameAndPress(name=config["specialNames"]["EndCall"], app=app)
    return tableName

def FireNavigationBugs():                                    
    dbConnection = ConnectToDB() 
    reporter = CNavigationJiraReporter(dbConnection)
    reporter.ReporterAboutNavigationJira()  

def GT_MetaData_Main():
    #from core.mac.L18nConfigConverter import L18nConfigConverter
    from core.mac.GTMetaData import GTMetaDataMgr

    dbconnection = ConnectToDB()
    #GTMetaDataMgr.LoadAndSaveGTMetaData(dbconnection,save_to_db=False)
    GTMetaDataMgr.getL18NMetadataByName("Agree","zh_CN")

    # converter = L18nConfigConverter()
    # converter.convert()

def Test(): 
    #path = "/Volumes/Data/Code/WebexRegressSheild/"
    # for root, dirs, files in os.walk(path):
    #     for file in files:
    #         if root.find(".git") != -1:
    #             continue
    #         full_path = os.path.join(root, file)
    #         print(full_path)
    #StartupInitializer()
    # if FeatureToggle.isEnabled("installer"):
    #     webexInitialize()     

    #tableName = "navigation_mac_deep_DailyRun_en_US"
    #tableName = "navigation_mac_deep_DailyRun_zh_CN"
    #runPresetProcessesEx(processIDs=[2,3,4,5])
    #tableName = CreateNavigationDB(name = "test") 
    # tableName = "`RegressShield`.`navigation_mac_deep_DailyRun_en_US_test`"                          
    # CWBXTraversalMgr.TraversalTheMeeting(isDeep=True,tableName=tableName)
    CWBXTraversalMgr.TestFocusedUI()
    
                      
    #CWBXTraversalMgr.TraversalTheWebex_Deep(tableName=tableName)     

def Main():
    LOGGER_INFO("Webex Regress Shield Execution Handler Started")

    addrs = psutil.net_if_addrs()
    for interface, info in addrs.items():
        for snic in info:
            if snic.family.name == 'AF_INET':
                LOGGER_INFO(f"{interface}'s IP address is: {snic.address}")

    StartupInitializer()
    CleanWebexData()
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    settings = DynamicConfig(SETTINGS_PATH)
    workflow = settings.get("workflow")
    if workflow != '':
        tableName = None
        LOGGER_INFO(f"Main: workflow is: [{workflow}]")
        if workflow == "is_page":
            tableName = Naviagtion_Deep_ISPage()
        elif workflow == "guest_join_meeting":
            tableName = Naviagtion_Deep_Login()
        elif workflow == "sign_in":
            tableName = Naviagtion_Deep_Login()
        elif workflow == "sign_up":
            tableName = Naviagtion_Deep_Login()
        elif workflow == "schedule":
            tableName = Naviagtion_Deep_Schedule()
        elif workflow == "full_meeting":
            tableName = Naviagtion_Deep_InMeeting()
        elif workflow == "app_core":
            tableName = Naviagtion_Deep_AppCore()
        elif workflow == "calling":
            tableName = Naviagtion_Deep_Calling()
        elif workflow == "settings":
            tableName = Naviagtion_Deep_Settings()
        elif workflow == "ai_assistant":
            tableName = Naviagtion_Deep_AIAssistant()
        else:
            pass
        PackageWebexLogs()
        if tableName:
            accData.getControlInfo(tableName)
    else:
        if FeatureToggle.isEnabled("installer"):
            webexInitialize()   
        
        GT_MetaData_Main()
        test_case = str(settings.get("test_case"))
        test_suite = str(settings.get("test_suite"))
        test_batch = str(settings.get("test_batch"))
        language = str(settings.get("language"))
        if test_case != '':
            if str(test_case).lower() == "all":
                GTManager.run_all_test_cases(language,None)
            else:
                GTManager.run_by_file(test_case, language)
        elif test_suite != '':
            if str(test_suite).lower() == "all":
                GTManager.run_all_test_suites(language,None)
            else:
                GTManager.run_by_file(test_suite, language,None)
        elif test_batch != '':
            if str(test_batch).lower() == "all":
                GTManager.run_all_test_case_batches(language,None)
            else:
                GTManager.run_by_file(test_batch, language,None)
        else:
            LOGGER_ERROR("No test_case, test_suite or test_batch specified in settings.")
            raise Exception("No test_case, test_suite or test_batch specified in settings.")

    from common.finalizer import output_runner
    output_runner.build_output()
    LOGGER_INFO("Webex Regress Shield Execution Handler Finished!")

def GTTest():
        # StartupInitializer()
        # CleanWebexData()
    settings = DynamicConfig(SETTINGS_PATH)
    language = str(settings.get("language"))    
    yamlPath = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_cases/"
    yamlfiles = ["navigations/basic/sign_in.yaml",
                 "navigations/basic/quit_app.yaml",
                 "navigations/basic/sign_out.yaml",
                 "meetings/actions/start_meeting.yaml"]

    file = "navigations/basic/sign_in.yaml"
    file = "navigations/basic/sign_out.yaml"
    file = "navigations/basic/quit_app.yaml"
    file = "meetings/actions/start_meeting.yaml"
    file = "meetings/actions/end_meeting.yaml"
    file = "meetings/video/vbg_dark.yaml"
    file = "meetings/video/vbg_static.yaml"
    # yamlPath = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_suites/"
    # file = "video_vbg.yaml"
    file = "navigations/navigation_sign_in.yaml"
    file = "navigations/navigation_app_core.yaml"
    file = "navigations/navigation_is_page.yaml"
    file = "navigations/navigation_schedule.yaml"
    file = "navigations/navigation_full_meeting.yaml"
    file = "navigations/navigation_calling.yaml"
    file = "navigations/navigation_audio_settings.yaml"
    file = "navigations/navigation_video_settings.yaml"
    file = "navigations/navigation_sharing_settings.yaml"
    # file = "meetings/actions/end_meeting.yaml"
    # file = "meetings/video/vbg_dark.yaml"
    # file = "meetings/video/   vbg_static.yaml"
    #yamlPath = "/Volumes/Data/Code/    Webe    xRegressSheild/src/test_space/test_suites/"
    # file = "video_vbg.yaml"   
    file = "navigations/basic/sign_out.yaml"
    file = "travel/navigation_to_app_core.yaml"
    file = "travel/navigation_to_is_page.yaml"
    file = "travel/navigation_to_schedule.yaml"
    file = "travel/navigation_to_meeting.yaml"       
    file = "travel/navigation_to_calling.yaml"
    file = "travel/navigation_to_audio_settings.yaml"
    file = "travel/navigation_to_video_settings.yaml"
    file = "travel/navigation_to_sharing_settings.yaml"

    ####
    file = "meetings/video/self_view_shown.yaml"
    file = "meetings/video/vbg executive office.yaml"
    file = "meetings/video/vbg_dark.yaml"
    file = "meetings/video/vbg_daylight.yaml"
    file = "meetings/video/vbg_dynamic.yaml"
    file = "meetings/video/vbg_fountain.yaml"
    file = "meetings/video/vbg_home_office.yaml"
    file = "meetings/video/vbg_lava.yaml"
    # file = "meetings/video/vbg_lookout.yaml"
    # file = "meetings/video/vbg_none.yaml"
    # file = "meetings/video/vbg_static.yaml"
    # file = "meetings/video/vbg_upload.yaml"   
    


    # file = "navigations/basic/sign_in.yaml"    
    # file = "meetings/actions/start_meeting.yaml"
    # file = "meetings/audio_setting/test_audio_control_complete_workflow.yaml"
    # file = "promote_blue_channel/sign_in.yaml"
    # file = "promote_blue_channel/start_meeting.yaml"
    # file = "promote_blue_channel/check_video.yaml"
    # file = "promote_blue_channel/check_audio.yaml"
    file = "promote_blue_channel/check_share.yaml"
    file = "navigations/basic/uninstall_app.yaml"
    file = "navigations/basic/re-install_app.yaml"
    file = "navigations/basic/sign_in.yaml"
    file = "meetings/share/test_basic_screen_sharing.yaml"
    file = "meetings/share/test_screen_sharing_complete.yaml"
    file = "meetings/video/vbg_dark.yaml"

    # yamlPath = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_batches/"
    # file = "promote_blue_channel.yaml"   
    GTManager.run_by_file(yamlPath + file, language)
    #GTManager.run_all_test_suites(language,None)
if __name__ == "__main__":  
    Main()
    #Test()  
    #GTTest()