import pandas  as pd
import hashlib
from common.utils.logger import LOGGER_INFO
from datetime import datetime
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH 

class CNavigationJiraReporter(object):
    def __init__(self,dbConnection) -> None:
        self.dbConnection = dbConnection
        self.releaseVersion = None
        self.osInfo = None

    def _readConfigs(self):
        settings = DynamicConfig(SETTINGS_PATH)
        self.osInfo = settings.get('osInfo')
        self.versionInfo  = settings.get('appVersion')

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    
    def _formatJiraTitle(self,row:pd.Series):
        title = f'''[Mac][Navigation][{self.osInfo}][{self.releaseVersion}] {row["controlName"]}:{row["error"]}'''
        if len(title) > 250:
            title = title[:250] + "..."
        
        return title
    
    def _formatJiraDescription(self,row:pd.Series):
        columns = list(row.index)
        description = f'''h1. {{color:#172b4d}}WebEx APP Meetings Accessibility Report [MAC]\r\n\r\n'''
        description = description + "||" + "|| ".join(columns) + "||\r\n"
        rowStr = ""
        for index, value in row.items():
            rowStr = rowStr + " | " + str(value)
        
        description = description  + rowStr + " | \r\n" 
        return description
    

    def _fileJiraBug(self,row:pd.Series):
        title = self._formatJiraTitle(row)
        descripiton = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title,descripiton)
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        return (jiraID,title)
    
    def _reportDuplicateName(self):
        if self.dbConnection is None:
            return
        
        sql = f'''SELECT * FROM RegressShield.navigation_mac order by `processID`ASC ,`order`ASC;'''
        data,columns = self.dbConnection.Query(sql)
        df = pd.DataFrame(data=data,columns=columns)
        maxCount = 5
        jiraInfos = []
        for level in range(1,10):
            newDf = df[df["level"] == level]
            newDf.reset_index(inplace=True)
            print(newDf)
            duplicates = newDf.duplicated(subset=['controlName'],keep="first")
            duplicatesDf = newDf[duplicates]
            for _, row in duplicatesDf.iterrows():
                    row["error"] = f'''Dupliacte Control Name in level: {level}'''
                    if maxCount <=0:
                        break

                    hashString = f'''[{row["controlName"]}] [{row["error"]}]'''

                    hashString = hashString.replace("'", "\\'").replace("#!", "\\'")
                    IssueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
                    sql = f'''select * from `RegressShield`.`bugInfo` where `hash` = "{IssueHash}" or `hashString` = "{hashString}";'''
                    results,_ = dbConnection.Query(sql)
                    if len(results) > 0:
                        message = f'''CRSNavigationJiraReporter: duplicate issue with hash:{IssueHash}, hashString:{hashString}'''
                        LOGGER_INFO(message)
                        continue

                    jiraID,title = self._fileJiraBug(row)
                    if jiraID is not None:
                        LOGGER_INFO(f'''New Screen Reader bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                        maxCount = maxCount - 1
                        date = datetime.today().date()
                        sql1 = f'''INSERT INTO `RegressShield`.`bugInfo` (`jiraID`, `createDate`, `title`, `affectVersion`, `platform`, `hash`, `hashString`, `status`) VALUES ('{jiraID}', '{str(date)}', '{title}', '{self.releaseVersion}', '{self.osInfo}', '{IssueHash}', '{hashString}', 'open');'''
                        dbConnection.Execute(sql1)
                        jiraInfos.append((jiraID,title))



    def _reportIssueWithError(self):
        pass


    def ReporterAboutNavigationJira(self):
        self._readConfigs()
        self._reportDuplicateName()



if __name__ == "__main__":
    from config.mysql import ConnectToDB
    from tools.Jira.Jira import TeamsJiraIssueReporter
    dbConnection = ConnectToDB()
    reporter = CNavigationJiraReporter(dbConnection)
    reporter.ReporterAboutNavigationJira()
