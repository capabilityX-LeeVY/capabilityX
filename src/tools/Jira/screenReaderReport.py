import re
import pandas as pd
from tools.Jira.Jira import TeamsJiraIssueReporter
from config.mysql import ConnectToDB
from datetime import datetime
import hashlib
from common.utils.logger import LOGGER_INFO
from tools.MessageBot.BotMessage import sendMessageToTeams
from config.paths import SETTINGS_PATH
from common.handler.settingsHandler import DynamicConfig
from tools.markdownToDataframe import MarkdownToDataframe
from common.handler.settingsHandler import DynamicConfig

class CScreenReaderReportParser(object):
    def __init__(self,fullPath) -> None:
        self.fullPath = fullPath
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.qtVersion = None
        self.releaseVersion = None

    def _readConfigs(self):
        settings = DynamicConfig(SETTINGS_PATH)
        self.osInfo = settings.get('osInfo')
        self.versionInfo  = settings.get('appVersion')
        self.qtVersion = settings.get('qtVersion')

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    def _formatJiraTitle(self,row:pd.Series):
        osInfo = self.osInfo.split(" ")[0] if self.osInfo else "Unknown"
        title = f'''[Screen Reader][{osInfo}][{row["Control Name"]}][{row["Compliance"]}][{row["Suggestion"]}]'''
        if len(title) > 250:
            title = title[:250] + "..."
        
        return title
    
    def _formatJiraDescription(self,row:pd.Series):
        columns = list(row.index)
        description = f'''h1. {{color:#172b4d}}WebEx APP Meetings Accessibility Report[{self.osInfo}][{self.versionInfo}]{{color}}\r\n\r\n'''
        description = description + "||" + "|| ".join(columns) + "||\r\n"
        rowStr = ""
        for index, value in row.items():
            if "Compliance" in index:
                value = f'''{{color:red}}{value}{{color}}'''

            if "Suggestion" in index:
                value = f'''*{value.strip()}*'''
            rowStr = rowStr + " | " + value
        
        description = description  + rowStr + " | \r\n" 
        description = description + "\r\n\r\n[more details |http://wbxregresssheild.qa.webex.com:8088/job/WebexRegressSheild_QT5_BTS/Report/ScreenReaderReport.html]\r\n"
        return description
    
    def _fileJiraBug(self,row:pd.Series):
        title = self._formatJiraTitle(row)
        descripiton = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title,descripiton,self.jiraVersion)
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        return (jiraID,title)


    def FileNewJiraNotifition(self,JiraInfos):
        LOGGER_INFO("ready to File New Jira Notifition....")
        if len(JiraInfos) == 0:
            return
        
        message = "#### **New Screen Reader Issue(s) found:**\n"
        for jiraInfo in JiraInfos:
            jiraID = jiraInfo[0]
            title = jiraInfo[1]
            newLine = f'''* **[{jiraID}](https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID})** [{title}]\n'''
            message = message + newLine
        
        message = message + f'''* **[More ... ](https://jira-eng-gpk2.cisco.com/jira/secure/Dashboard.jspa?selectPageId=61721)**'''
        sendMessageToTeams(message,roomId="a48ab4a0-7d98-11f0-95e9-4735252c61fe")

    def ParserReportAndFileBugs(self):
        dbConnection = ConnectToDB()
        self._readConfigs()
        df:pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        df = df[df["Compliance"].str.contains('Non-compliant')]
        df.reset_index(drop=True, inplace=True)
        jiraInfos = []
        maxCount = DynamicConfig(SETTINGS_PATH).get("fileNBugs")
        LOGGER_INFO(f'''max bug count: {maxCount}''')
        for _, row in df.iterrows():
            if maxCount <=0:
                break

            hashString = row["Control Name"].replace("'", "\\'").replace("#!", "\\'")
            IssueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
            sql = f'''select * from `RegressShield`.`bugInfo` where `hash` = "{IssueHash}" or `hashString` = "{hashString}";'''
            results,_ = dbConnection.Query(sql)
            if len(results) > 0:
                message = f'''ScreenReader: duplicate issue with hash:{IssueHash}, hashString:{hashString}'''
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

        self.FileNewJiraNotifition(jiraInfos)

    def AddJiaInfoAndToHTML(self,htmlPath):
        dbConnection = ConnectToDB()
        df:pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        df["References"] = df["References"].str.replace("**","")
        df["Jira"] = ""
        for index,row in df.iterrows():
            description = row["Control Name"].replace("'", "\\'").replace("#!", "\\'")
            sql = f'''SELECT jiraID FROM RegressShield.bugInfo where hashString = "{description}";'''
            data,_ = dbConnection.Query(sql)
            df.at[index, 'References'] = f'''<b>{row["References"]}</b>'''

            if len(data) >0:
                df.at[index, 'Jira'] = f'''<a href="https://jira-eng-gpk2.cisco.com/jira/browse/{data[0][0]}" target="_blank">{data[0][0]}</a>''' 
    
        MarkdownToDataframe.DataframeToHTML(df,htmlPath)

        