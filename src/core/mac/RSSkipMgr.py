import json
import os
import locale
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH

CONFIG_NAME = "skipConfig"

class CRSSikipMgr:
    def __init__(self,dbConnection,tableName):
        self.m_configs = None
        self.dbConnection = dbConnection
        self.tableName = tableName
        self.ReadSkipConfig()

    @staticmethod
    def ReadConfig():
        config = None
        try:
            #language,_ = locale.getdefaultlocale()
            language = DynamicConfig(SETTINGS_PATH).get("language")
            filePath = os.path.join(os.path.dirname(__file__),f'''{CONFIG_NAME}_{language}.json''')
            with open(filePath, 'r') as file:
                data = file.read()
                config = json.loads(data)
        except FileNotFoundError:
            print(f"Configuration file {filePath} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from the configuration file {filePath}.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return config
    
    def ReadSkipConfig(self):
        try:
            language = DynamicConfig(SETTINGS_PATH).get("language")
            filePath = os.path.join(os.path.dirname(__file__),f'''{CONFIG_NAME}_{language}.json''')
            with open(filePath, 'r') as file:
                data = file.read()
                self.m_configs = json.loads(data)
        except FileNotFoundError:
            print(f"Configuration file {filePath} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from the configuration file {filePath}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def AddSkipFlag_Deep_ByControlNameReg(self):
        if self.m_configs is None:
            print("Configuration not loaded.")
            return
        
        settings = DynamicConfig(SETTINGS_PATH)
        workflow = settings.get("workflow")
        specialSkipItem = f'''skipControl_{workflow}'''
        regSkipedItem = []
        regSkipedItem.extend(self.m_configs.get("skipControl_common", []))
        regSkipedItem.extend(self.m_configs.get(specialSkipItem, []))
        
        self.dbConnection.Execute(f'''SET SQL_SAFE_UPDATES = 0;''')
        for item in regSkipedItem:
            sql = f'''UPDATE {self.tableName} SET `status` = 'validated skiped', `skip` = '1' WHERE (`controlName` REGEXP "{item}");'''
            self.dbConnection.Execute(sql)

    def AddSkipFlag_Deep_ByFromControl(self):
        if self.m_configs is None:
            print("Configuration not loaded.")
            return
           
        regSkipedItem = self.m_configs.get("skipByControlID", [])
        self.dbConnection.Execute(f'''SET SQL_SAFE_UPDATES = 0;''')
        for item in regSkipedItem:
            sql = f'''UPDATE {self.tableName} SET `status` = 'validated skiped', `skip` = '1' WHERE (`fromControl` = "{item[1]}");'''
            self.dbConnection.Execute(sql)

    def AddSkipFlag_Deep_ByControlNameAndLevel(self):
        if self.m_configs is None:
            print("Configuration not loaded.")
            return
        skipedItem = self.m_configs.get("skipByByControlNameAndLevel", [])
        for item in skipedItem:
            sql = f'''UPDATE {self.tableName} SET `status` = 'validated skiped', `skip` = '1' WHERE (`controlName` = '{item[0]}') and (`level` = '{item[1]}');'''
            if item[1] == -1:
                sql = f'''UPDATE {self.tableName} SET `status` = 'validated skiped', `skip` = '1' WHERE (`controlName` = '{item[0]}');'''
            self.dbConnection.Execute(sql)