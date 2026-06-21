import os 
import tools.webexApp.appHandler as wbxinstaller
from common.handler import reportHandler
from config.paths import SETTINGS_PATH, FEATURE_TOGGLE_CONFIG_PATH
from config.settingsInitializer import initSettings
from common.utils.featureToggle import FeatureToggle  
from common.utils.logger import LOGGER_INFO
from tools.Jira.screenReaderReport import CScreenReaderReportParser
from common.handler.settingsHandler import DynamicConfig


def webexInitialize():
    wbxinstaller.installWebex()                                                                                                    

def main():
    LOGGER_INFO("start to file screen reader bugs ....")
    initSettings(SETTINGS_PATH)
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)

    if FeatureToggle.isEnabled('installer'):
        webexInitialize()
    
    reportHandler.setBasicInfo()

    screenReaderFileName = DynamicConfig(SETTINGS_PATH).get("screenReaderFileName")

    ScreenReaderReportPath =  os.path.join(os.path.dirname(__file__),"report","screen_reader",screenReaderFileName)
    LOGGER_INFO(f'''ScreenReaderReportPath:{ScreenReaderReportPath}''')
    parser = CScreenReaderReportParser(ScreenReaderReportPath)
    parser.ParserReportAndFileBugs()

if __name__ == '__main__': 
    main()
