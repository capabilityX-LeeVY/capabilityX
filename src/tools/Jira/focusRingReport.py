import re
import pandas as pd
import hashlib


from pathlib import Path
from tools.Jira.Jira import TeamsJiraIssueReporter
from config.mysql import ConnectToDB
from rs_sdk.utils.control_db import ControlDB as localControlDB
from datetime import datetime
from common.utils.logger import LOGGER_INFO
from tools.MessageBot.BotMessage import sendMessageToTeams
from config.paths import SETTINGS_PATH, CONTROL_IMAGE_PATH, APP_VERSION_PATH
from common.handler.settingsHandler import DynamicConfig
from common.utils import deviceInfo
from common.handler import fileHandler
from tools.markdownToDataframe import MarkdownToDataframe
from common.handler.settingsHandler import DynamicConfig

class CFocusRingReportParser(object):
    def __init__(self,fullPath,imagePath=CONTROL_IMAGE_PATH) -> None:
        self.local_DB = localControlDB()
        self.fullPath = fullPath
        self.imagePath = imagePath
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.qtVersion = None
        self.releaseVersion = None
        if "onfocus" in str(self.fullPath):
            self.rawResults = next(Path(self.fullPath).parent.glob("*public_fr-report-onfocus*.md"), None)
            self.controlTag = "current"
        elif "lostfocus" in str(self.fullPath):
            self.rawResults = next(Path(self.fullPath).parent.glob("*public_fr-report-lostfocus*.md"), None)
            # self.rawResults = next(Path(self.fullPath).parent.glob("pre_controls_focus_status.md"), None)
            self.controlTag = "pre"
        else:
            self.rowfile = None

    def _readConfigs(self):
        settings = DynamicConfig(SETTINGS_PATH)
        self.osInfo = deviceInfo.getOSInfo()
        self.versionInfo  = fileHandler.readFile(APP_VERSION_PATH)
        self.qtVersion = settings.get('qtVersion')

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    def _formatJiraTitle(self,row:pd.Series):
        osInfo = self.osInfo.split(" ")[0] if self.osInfo else "Unknown"
        title = f'''[Focus Ring][{osInfo}][{row["Description"]}][{row["Compliance"]}]'''
        if len(title) > 250:
            title = title[:250] + "..."
        
        return title
    
    def _formatJiraDescriptionWithDB(self,row:pd.Series, imageUrl = None):
        row = row.drop(labels=["alt"], errors="ignore")
        columns = list(row.index)
        description = f'''h1. {{color:#172b4d}}WebEx APP Meetings Accessibility Report[{self.osInfo}][{self.versionInfo}]{{color}}\r\n\r\n'''
        description = description + "||" + "|| ".join(columns) + "||\r\n"
        rowReportStr = ""
        controlHistoryStr = ""
        imageTag = f'!{imageUrl}!' if imageUrl else "No Image"

        for index, value in row.items():
            if "Compliance" in index: # type: ignore
                value = f'''{{color:red}}{value}{{color}}'''

            if index == "Image":
                value = imageTag
                
            if "Description" in index: # type: ignore
                imageName = value
                controlHistory = self._getControlHistory(imageName)
                
                if controlHistory is not None and not controlHistory.empty:
                    controlHistory = controlHistory.drop(columns=["Image", "PreControlImage", "WindowImage", "Created"], errors='ignore')
                    table_header = "|| " + " || ".join(controlHistory.columns) + " ||\r\n"
                    table_rows = "\r\n".join(
                    f"| {' | '.join(f'{{color:#0052CC}}*{str(val)}*{{color}}' for val in row)} |" 
                    if idx == controlHistory.index[2] else "| " + " | ".join(map(str, row)) + " |"
                    for idx, row in controlHistory.iterrows()
                )
                    controlHistoryStr = f"h2. Control History\r\n{table_header}{table_rows}\r\n\r\n"

            rowReportStr = rowReportStr + " | " + value
        
        description = description  + rowReportStr + " | \r\n\r\n"

        if controlHistoryStr:
            description += controlHistoryStr
 
        return description
    
    def _formatJiraDescription(self,row:pd.Series, imageUrlMap = None):
        row = row.drop(labels=["alt"], errors="ignore")
        columns = list(row.index)
        image_name = row.get("Description", "").strip()
        description = f'''h1. {{color:#172b4d}}WebEx APP Meetings Accessibility Report[{self.osInfo}][{self.versionInfo}]{{color}}\r\n\r\n'''
        description = description + "||" + "|| ".join(columns) + "||\r\n"
        rowReportStr = ""
        controlHistoryStr = ""
        # imageTag = f'!{imageUrl}!' if imageUrl else "No Image"
        # LOGGER_INFO("ImageName:", image_name)
        if imageUrlMap is not None:
            print("imageUrlMap keys:", list(imageUrlMap.keys()), "imageUrlMap values:", list(imageUrlMap.values()))
        else:
            print("imageUrlMap is None")

        for index, value in row.items():
            if "Compliance" in index: # type: ignore
                value = f'''{{color:red}}{value}{{color}}'''

            if index == "Image":
                # value = imageTag
                image_name = row.get("Description", "").strip()
                if imageUrlMap and image_name in imageUrlMap:
                    value = f'!{imageUrlMap[image_name]}|width=100!'
                
            rowReportStr = rowReportStr + " | " + value
        description += rowReportStr + " | \r\n\r\n"
            
        controlHistory = self._getControlHistoryFromResult(image_name)
        if controlHistory is not None and not controlHistory.empty:
            controlHistory = controlHistory.drop(columns=["Analysis Result", "Compliance"], errors='ignore')
            table_header = "|| " + " || ".join(controlHistory.columns) + " ||\r\n"
            table_rows = "\r\n".join(
                "| " + " | ".join(
                    f'!{imageUrlMap[row.get("Description", "").strip()]}|width=100!'
                    if col == "Image" and imageUrlMap and row.get("Description", "").strip() in imageUrlMap
                    else f"{{color:#FF0000}}*{val}*{{color}}" if idx == controlHistory.index[-2] and len(controlHistory) >= 2
                    else str(val)
                    for col, val in zip(controlHistory.columns, row)
                ) + " |"
                for idx, row in controlHistory.iterrows()
            )
            controlHistoryStr = f"h2. Control History\r\n{table_header}{table_rows}\r\n\r\n"
            description += controlHistoryStr

            return description
    
    def _getControlHistory(self, imageName:str):
        results = self.local_DB.fetch_control_history()
        if len(results) == 0:
            return None
        
        if isinstance(results["Image"].iloc[0], bytes):
            return None
        else:
            progressImages = results["Image"].str.replace(r'.*[\\/]', '', regex=True).str.strip()
        
        imageName = imageName.strip()
        matched_rows = results[progressImages == imageName]
        LOGGER_INFO(f'''Control history matched rows: {matched_rows}''')
        if matched_rows.empty:
            return None

        match_index = matched_rows.index[0]
        start_index = max(0, match_index - 2)
        end_index = min(len(results), match_index + 3)  
        context_rows = results.iloc[start_index:end_index]

        return context_rows
    
    def _getControlHistoryFromResult(self, imageName: str):
        if self.rawResults is None:
            return None
        df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(str(self.rawResults))

        if "Image" not in df.columns or df.empty:
            return None
        
        imageName = imageName.strip()
        progressImages = df["Description"].str.replace(r'.*[\\/]', '', regex=True).str.strip()
        matched_rows = df[progressImages == imageName]
        
        if matched_rows.empty:
            return None

        match_index = matched_rows.index[0]
        start_index = max(0, match_index - 5)
        end_index = min(len(df), match_index + 2)
        context_rows = df.iloc[start_index:end_index]

        return context_rows
        
    def _fileJiraBug(self,row:pd.Series):
        title = self._formatJiraTitle(row)
        descripiton = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title,descripiton,self.jiraVersion)
        jira.labels.append("WRS_FocusRing")
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        LOGGER_INFO(f'''Jira title: {title}''')
        LOGGER_INFO(f'''Jira description: {descripiton}''')

        if jiraID:
            imageName = row["Description"]
            historyDF = self._getControlHistoryFromResult(imageName)
            if historyDF is not None and "Description" in historyDF.columns:
                historyImages = historyDF["Description"].dropna().str.strip().unique()

            if self.controlTag == "current":
                imagePaths = [
                    f"{self.imagePath}/currentControls/{name}"
                    for name in historyImages
                ]
            elif self.controlTag == "pre":
                imagePaths = [
                    f"{self.imagePath}/preControls/{name}"
                    for name in historyImages
                ]
            else:
                imagePaths = None
            uploadedUrls = jira.upload_image(jiraID, imagePaths)
            if uploadedUrls:
                # imageUrl = uploadedUrls[0]
                imageUrlMap = dict(zip(historyImages, uploadedUrls)) if uploadedUrls else {}
                descripiton = self._formatJiraDescription(row, imageUrlMap)
                jira.update_fields_for_issue(jiraID, {"description": descripiton})
        return (jiraID,title)

    def FileNewJiraNotifition(self,JiraInfos):
        LOGGER_INFO("ready to File New Jira Notifition....")
        if len(JiraInfos) == 0:
            return
        
        message = "#### **New Focus Ring Issue(s) found:**\n"
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

        # df["Name Without Timestamp"] = df["Description"].apply(lambda x: x.split("_", 1)[-1])
        def extract_alt(md_cell):
            match = re.search(r'alt="([^"]+)"', md_cell)
            return match.group(1) if match else None

        df["alt"] = df["Image"].apply(extract_alt)
        for _, row in df.iterrows():
            if maxCount is not None and maxCount <= 0:
                break

            imageName = row["Description"]
            # >>> begin: remove control history matching code
            # controlHistory = self._getControlHistory(imageName)
            # if controlHistory is not None and not controlHistory.empty:
            #     controlType = controlHistory["ControlType"].unique()
            #     if (controlType == 50020).any():
            #         continue
            # >>> end: remove control history matching code

            hashString = f"{row['Description']}|{row['alt']}"
            IssueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
            sql = f'''select * from `RegressShield`.`bugInfo` where `hash` = "{IssueHash}" or `hashString` = "{hashString}";'''
            results,_ = dbConnection.Query(sql)
            if len(results) > 0:
                message = f'''FocusRing: duplicate issue with hash:{IssueHash}, hashString:{hashString}'''
                LOGGER_INFO(message)
                continue
            
            # df = df.drop(columns=["Description Without Timestamp"], errors='ignore')
            jiraID,title = self._fileJiraBug(row)
            if jiraID is not None:
                LOGGER_INFO(f'''New focus ring bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                if maxCount is not None:
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
            description = row["Description"]
            sql = f'''SELECT jiraID FROM RegressShield.bugInfo where hashString = "{description}";'''
            data,_ = dbConnection.Query(sql)
            df.at[index, 'References'] = f'''<b>{row["References"]}</b>'''

            if len(data) >0:
                df.at[index, 'Jira'] = f'''<a href="https://jira-eng-gpk2.cisco.com/jira/browse/{data[0][0]}" target="_blank">{data[0][0]}</a>''' 
    
        MarkdownToDataframe.DataframeToHTML(df,htmlPath)

        