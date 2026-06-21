import re
import pandas as pd
from tools.Jira.Jira import TeamsJiraIssueReporter
from datetime import datetime
import hashlib
from config.paths import SETTINGS_PATH, WINDOW_IMAGE_PATH    
from tools.markdownToDataframe import MarkdownToDataframe
from config.mysql import ConnectToDB
from common.handler.settingsHandler import DynamicConfig

class CLocalizationReportParser(object):
    def __init__(self,fullPath) -> None:
        self.fullPath = fullPath / "deduplicated_markdown.md"
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

    def _formatJiraTitle(self,row:pd.Series,df:pd.DataFrame):
        col_en = df.columns[4]
        col_control_name= df.columns[3]
        col_language = df.columns[5]
        print(f'''col_en: {col_en}, col_language: {col_language}''')
        title = f'''[{row["Analysis Result"]}][{row[col_language]}][{row[col_control_name]}][{row["Compliance"]}][{row["Reference"]}]'''
        if len(title) > 250:
            title = title[:250] + "..." 
        return title
    
    def _formatJiraDescription(self,row:pd.Series):
        columns = list(row.index)
        if len(columns) > 1:
            del columns[1]
        description = f'''h1. {{color:#172b4d}}WebEx APP UI issue Report{{color}}\r\n\r\n'''
        description = description + "||" + "|| ".join(columns) + "||\r\n"
        rowStr = ""
        for index, value in row.items():
            if index not in columns:
                continue
            if "Localization Compliance" in index:
                value = f'''{{color:red}}{value}{{color}}'''

            if "Suggestions for Improvement" in index:
                value = f'''*{value.strip()}*'''
            rowStr = rowStr + " | " + str(value)
        
        description = description  + rowStr + " | \r\n" 
        return description
    
    def _fileJiraBug(self,row:pd.Series,df:pd.DataFrame):
        title = self._formatJiraTitle(row,df)
        descripiton = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title,descripiton,self.jiraVersion)
        jira.labels = ["WebexRegressShield_localization",]
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        return (jiraID,title)

    def _uploadImage(self,jiraID,image_paths):
        jira = TeamsJiraIssueReporter(None,None)
        jira.upload_image(jiraID, image_paths)


    def ParserReportAndFileBugs(self):
        dbConnection = ConnectToDB()
        df:pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        df = df[df["Compliance"].str.contains('Non-compliant')]
        df.reset_index(drop=True, inplace=True)
        jiraInfos = []
        maxCount = 50
        print(f'''max bug count: {maxCount}, {df.shape[0]}''')
        for _, row in df.iterrows():
            if maxCount <=0:
                print("test")
                break
            col_image = df.columns[2]
            col_control_name = df.columns[3]
            hashString = row[col_control_name].replace("'", "\\'").replace("#!", "\\'")

            IssueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
            sql = f'''select * from `Localization`.`issueinfo` where `hash` = "{IssueHash}" or `hashString` = "{hashString}";'''
            results,coulums = dbConnection.Query(sql)
            
            if len(results) > 0:
                message = f'''Localization: duplicate issue with hash:{IssueHash}, hashString:{hashString}'''
                tempDf = pd.DataFrame(data=results,columns=coulums)
                jiraID = tempDf["jiraID"].values[0]
                title = tempDf["title"].values[0]
                jiraInfos.append((jiraID,title))
                continue

            jiraID,title = self._fileJiraBug(row,df)
            if jiraID is not None:
                print(f'''New Localiztion bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                maxCount = maxCount - 1
                date = datetime.today().date()
                sql1 = f'''INSERT INTO `Localization`.`issueinfo` (`jiraID`, `createDate`, `title`, `affectVersion`, `platform`, `hash`, `hashString`, `status`) VALUES ('{jiraID}', '{str(date)}', '{title}', '{self.releaseVersion}', '{self.osInfo}', '{IssueHash}', '{hashString}', 'open');'''
                dbConnection.Execute(sql1)
                jiraInfos.append((jiraID,title))
                image_paths = row[col_image]
                alt_value = self.extract_alt_value(image_paths)
                image_paths = f"{WINDOW_IMAGE_PATH}/{alt_value}"
                print(f'''image path: {image_paths}''')
                self._uploadImage(jiraID,[image_paths])

        return jiraInfos
    
    def extract_alt_value(self, image_paths):
        match = re.search(r'alt="([^"]+)"', image_paths)
        if match:
            return match.group(1)
        return None

    def AddJiaInfoAndToHTML(self,htmlPath):
        dbConnection = ConnectToDB()
        df:pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        df["References"] = df["References"].str.replace("**","")
        df["Jira"] = ""
        for index,row in df.iterrows():
            description = row["EN"].replace("'", "\\'").replace("#!", "\\'")
            sql = f'''SELECT jiraID FROM Localization.issueinfo where hashString = "{description}";'''
            data,_ = dbConnection.Query(sql)
            df.at[index, 'References'] = f'''<b>{row["References"]}</b>'''

            if len(data) >0:
                df.at[index, 'Jira'] = f'''<a href="https://jira-eng-gpk2.cisco.com/jira/browse/{data[0][0]}" target="_blank">{data[0][0]}</a>''' 
    
        MarkdownToDataframe.DataframeToHTML(df,htmlPath)

if __name__ == "__main__":
    fullPath = "src/report/localization/result_gpt4_vision_message.md"
    parser = CLocalizationReportParser(fullPath)
    parser.ParserReportAndFileBugs()

        