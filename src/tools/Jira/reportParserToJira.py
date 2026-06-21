import re
import pandas as pd
import hashlib
import imagehash

from PIL import Image, UnidentifiedImageError
from typing import Optional
from pathlib import Path
from tools.Jira.Jira import TeamsJiraIssueReporter
from config.mysql import ConnectToDB
from datetime import datetime
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_DEBUG
from tools.MessageBot.BotMessage import sendMessageToTeams
from config.paths import SETTINGS_PATH
from config.config import ISSUE_DB, BUG_REPORT_LIMIT
from common.handler.settingsHandler import DynamicConfig
from common.utils import deviceInfo
from tools.markdownToDataframe import MarkdownToDataframe
from common.handler.report_id_generator import report_id_generator


class CReportParserToJira(object):
    def __init__(self,fullPath,issueType=None) -> None:
        self.dbConnection = ConnectToDB(ISSUE_DB)
        self.fullPath = fullPath
        self.fileName = self.fullPath.name
        self.type = issueType
        self.df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.reportId = report_id_generator.global_report_id
        self.jiraType = self._getJiraType(self.fileName,self.type)

    def _readConfigs(self):
        settings = DynamicConfig(SETTINGS_PATH)
        self.osInfo = deviceInfo.getOSInfo()
        self.versionInfo  = settings.get("appVersion")

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    def _getImagePath(self,row:pd.Series):
        if "Image" not in row or pd.isna(row["Image"]):
            return None 
        img_html = str(row["Image"])
        # match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', img_html)
        match = re.search(r'src\s*=\s*"([^"]+)"', img_html)
        if match:
            imgRelPath = match.group(1).replace("\\", "/")
            mdPath = Path(self.fullPath).parent
            imgFullPaht = (mdPath / imgRelPath).resolve()
            return imgFullPaht
        return None

    def _getImageData(self,image_path):
        try:
            LOGGER_DEBUG(f"🔍 Checking image path: {image_path}, exists={image_path.exists()}")
            img = Image.open(image_path)
            imgWhash = str(imagehash.whash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgWhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None
    
    def _getJiraType(self, filename: str, type: None) -> Optional[str]:
        if type is not None:
            return type
        filenameLower = filename.lower()
        mapping = {
            "fr-report": "Focus Ring",
            "i18n-report": "i18n",
            "sr-report": "Screen Reader",
            "navigator-report": "Navigation"
        }
        return next((v for k, v in mapping.items() if k in filenameLower), None)
    
    def _getJiraLabels(self, jiraType: Optional[str]) -> Optional[list[str]]:
        labels = {
            "Focus Ring": ["WRS_FocusRing"],
            "i18n": ["WebexRegressShield_localization"],
            "Screen Reader": [],
            "Navigation": ["KB_Navigate"]
        }
        return labels.get(jiraType) if jiraType is not None else None
    
    def _formatHash(self,row:pd.Series):
        osInfo = self.osInfo.split(" ")[0] if self.osInfo else "Unknown OS"
        if self.jiraType == "i18n":
            return f"[{row['Analysis Result']}][{osInfo}][{row['Control Name']}]"
        elif self.jiraType == "Navigation":
            return f"[{self.jiraType}][{osInfo}][{row['Control Name']}][{row['FromControl']}]"
        elif self.jiraType:
            return f"[{self.jiraType}][{osInfo}][{row['Control Name']}]"
        else:
            return f"[{osInfo}][{row['Control Name']}]"

    def _formatJiraTitle(self,row:pd.Series):
        hash = self._formatHash(row)
        reference = row['Reference']
        if reference:
            title = f"{hash}[{row['Compliance']}][{reference}]"
        else:
            title = f"{hash}[{row['Compliance']}]"
        return title
    
    def _formatJiraDescription(self,row:pd.Series, imageUrlMap = None):
        columns = list(row.index)
        match = re.search(r'alt="([^"]+)"', row["Image"]) if row.get("Image") else None
        imageName = match.group(1).strip() if match else None
        description = f'''h1. {{color:#172b4d}}WebEx APP Accessibility Report[{self.osInfo}][{self.versionInfo}]{{color}}\r\n\r\n'''
        filtered_columns = [c for c in columns if c != "No."]
        description = description + "||" + "|| ".join(filtered_columns) + "||\r\n"
        rowReportStr = ""
        controlHistoryStr = ""
        if not imageUrlMap:
            LOGGER_WARNING("imageUrlMap is None")
        else:
            LOGGER_DEBUG(f"imageUrlMap keys: {list(imageUrlMap.keys())}, imageUrlMap values: {list(imageUrlMap.values())}")
        for index, value in row.items():
            if index == "No.":
                continue
            if "Compliance" in index: # type: ignore
                value = f'''{{color:red}}{value}{{color}}'''
            if index == "Image":
                if imageUrlMap and imageName in imageUrlMap:
                    value = f'!{imageName}|thumbnail!'
            rowReportStr += f" | {value}"
        description += rowReportStr + " | \r\n\r\n"

        if self.jiraType != "Focus Ring":
            return description
        
        no_col = next(c for c in row.index if c.strip() == "No.")
        rowNumber = row[no_col]
        controlHistory = self._getControlHistoryFromResult(rowNumber)
        if controlHistory is None or controlHistory.empty:
            return description
        if controlHistory is not None and not controlHistory.empty:
            def _extract_alt(img_tag):
                if not isinstance(img_tag, str):
                    return ""
                match = re.search(r'alt="([^"]+)"', img_tag)
                return match.group(1) if match else ""
            controlHistory = controlHistory.drop(columns=["No.", "Analysis Result", "Compliance", "Reference", "Suggestion"], errors='ignore')
            table_header = "|| " + " || ".join(controlHistory.columns) + " ||\r\n"
            table_rows = "\r\n".join(
                "| " + " | ".join(
                    f'!{_extract_alt(val)}|thumbnail!'
                    if col == "Image" and imageUrlMap and _extract_alt(val) in imageUrlMap
                    else f"{{color:#FF0000}}*{val}*{{color}}"
                        if (len(controlHistory) >= 2 and idx == controlHistory.index[-2])
                        or (len(controlHistory) == 1)
                    else str(val)
                    for col, val in zip(controlHistory.columns, row)
                ) + " |"
                for idx, row in controlHistory.iterrows()
            )
            controlHistoryStr = f"h2. Traversal Context\r\n{table_header}{table_rows}\r\n\r\n"
            if len(controlHistory) >= 2:
                description += controlHistoryStr
        return description
    
    def _getControlHistoryFromResult(self, rowNumber) -> Optional[pd.DataFrame]:
        if self.fullPath is None:
            return None
        df: pd.DataFrame = self.df
        if "Image" not in df.columns or df.empty:
            return None
        matchedRows = df[df['No.'].astype(str).str.strip() == str(rowNumber)]
        if matchedRows.empty:
            return None
        if self.jiraType == "Focus Ring":
            matchIndex = matchedRows.index[0]
            startIndex = max(0, matchIndex - 5)
            endIndex = min(len(df), matchIndex + 2)
            contextRows = df.iloc[startIndex:endIndex]
            return contextRows
        else:
            return matchedRows
        
    def _fileJiraBug(self,row:pd.Series):
        title = self._formatJiraTitle(row)
        descripiton = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title,descripiton,self.jiraVersion)
        jiraLabels = self._getJiraLabels(self.jiraType)
        if jiraLabels:
            jira.labels.extend(jiraLabels)
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        LOGGER_DEBUG(f'''Jira title: {title}''')
        LOGGER_DEBUG(f'''Jira description: {descripiton}''')

        if jiraID:
            imgFullPath = self._getImagePath(row) if row.get("Image") else None
            if imgFullPath:
                historyImages = []
                imgDirPath = imgFullPath.parent
                # rowNumber = row['No.']
                no_col = next(c for c in row.index if c.strip() == "No.")
                rowNumber = row[no_col]
                historyDF = self._getControlHistoryFromResult(rowNumber)
                if historyDF is not None:
                    historyImages = historyDF["Image"].str.extract(r'(?i)alt="([^"]+)"')[0].dropna().str.strip().unique()
                if self.jiraType == "Focus Ring":
                    imagePaths = [
                            f"{imgDirPath}/{name}"
                            for name in historyImages
                        ]
                elif self.jiraType == "i18n":
                    imagePaths = [
                            f"{imgFullPath}"
                        ]
                uploadedUrls = jira.upload_image(jiraID, imagePaths)
                if uploadedUrls:
                    imageUrlMap = dict(zip(historyImages, uploadedUrls)) if uploadedUrls else {}
                    descripiton = self._formatJiraDescription(row, imageUrlMap)
                    jira.update_fields_for_issue(jiraID, {"description": descripiton})
        return (jiraID,title)

    def FileNewJiraNotifition(self,JiraInfos):
        LOGGER_INFO("ready to File New Jira Notifition....")
        if len(JiraInfos) == 0:
            return
        
        message = f"#### **New {self.jiraType} Issue(s) found:**\n"
        for jiraInfo in JiraInfos:
            jiraID = jiraInfo[0]
            title = jiraInfo[1]
            newLine = f'''* **[{jiraID}](https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID})** [{title}]\n'''
            message = message + newLine
        
        message = message + f'''* **[More ... ](https://jira-eng-gpk2.cisco.com/jira/secure/Dashboard.jspa?selectPageId=61721)**'''
        sendMessageToTeams(message,roomId="a48ab4a0-7d98-11f0-95e9-4735252c61fe")

    def ParserReportAndFileBugs(self):
        self._readConfigs()
        df: pd.DataFrame = self.df
        df = df[df["Compliance"].str.contains('❌')]
        if df.empty:
            LOGGER_WARNING(f"No matching row found.")
            return
        df.reset_index(drop=True, inplace=True)
        maxCount = BUG_REPORT_LIMIT
        LOGGER_INFO(f'''max bug count: {maxCount}''')
        jiraInfos = []
        for _, row in df.iterrows():
            if maxCount is not None and maxCount <= 0:
                break
            imgFullPath = self._getImagePath(row) if row.get("Image") else None
            imgPhash, imgBytes = self._getImageData(imgFullPath) if imgFullPath else (None, None)
            hashString = f"{self._formatHash(row)}"
            issueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
            controlName = row["Control Name"].strip()
            analysisResult = row["Analysis Result"].strip()
            sql = f'''select * from issue_by_wrs where (hash = "{issueHash}" or hashString = "{hashString}") and controlName != "unknown" and (status != "Done" OR resolution NOT IN ("Invalid"));'''
            results, columns = self.dbConnection.Query(sql)
            if len(results) > 0:
                existingJiraIds = [row[columns.index('jiraID')] for row in results]
                existingIdsStr = ", ".join(existingJiraIds)
                message = f'''[{self.jiraType}]: Found existing issue(s) in Jira (ID: {existingIdsStr}) with hash: {issueHash}, hashString: {hashString}'''
                LOGGER_WARNING(message)
                continue
            
            jiraID,title = self._fileJiraBug(row)
            if jiraID is not None:
                LOGGER_INFO(f'''New {self.jiraType} bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                if maxCount is not None:
                    maxCount = maxCount - 1
                date = datetime.today().date()
                sql1 = '''
                INSERT INTO issue_by_wrs
                (jiraID, title, affectVersion, platform, analysisResult, type, status, hash, hashString, controlName, imgBytes, imgHash, reportId, createDate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                values = (
                    jiraID,
                    title,
                    self.releaseVersion,
                    self.osInfo,
                    analysisResult,
                    self.jiraType,
                    "New",
                    issueHash,
                    hashString,
                    controlName,
                    imgBytes,
                    imgPhash,
                    self.reportId,
                    str(date)
                )
                self.dbConnection.ExecuteWithData(sql1, values)
                jiraInfos.append((jiraID,title))

        self.FileNewJiraNotifition(jiraInfos)

        