import os
import re
import pandas as pd
import hashlib
import imagehash
import shutil

from PIL import Image, UnidentifiedImageError
from typing import Optional
from pathlib import Path
from tools.Jira.Jira import TeamsJiraIssueReporter
from config.mysql import ConnectToDB
from datetime import datetime
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_DEBUG
from tools.MessageBot.BotMessage import sendMessageToTeams
from config.paths import image_path
from config.config import TC_DB, ISSUE_DB, BUG_REPORT_LIMIT
from common.handler.textHandler import preProcessString
from rs_sdk.utils import image_handler


class Ce2eReportParserToJira(object):
    def __init__(self,reportId) -> None:
        self.dbConnectionToIssue = ConnectToDB(ISSUE_DB)
        self.dbConnectionToTestcase = ConnectToDB(TC_DB)
        self.reportId = reportId
        self.df = self._getDataFrame(self.reportId)
        if self.df.empty:
            LOGGER_WARNING(f"No data found for report {self.reportId}.")
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.imgPath = Path(image_path / "temp")

    def _getDataFrame(self, reportId: str) -> pd.DataFrame:
        sql = f'''SELECT * FROM TestCaseNavigateReport WHERE report_id = "{reportId}";'''
        results, columns = self.dbConnectionToTestcase.Query(sql)
        df = pd.DataFrame(results, columns=columns)
        if "locate_control_name" in df.columns:
            df["locate_control_name"] = (
                df["locate_control_name"]
                .fillna("")
                .astype(str)
                .apply(lambda x: preProcessString(x, timestamp_prefix=""))
            )
        return df
        
    def _readConfigs(self, row: Optional[pd.Series] = None):
        self.osInfo = row["platform"] if row is not None else "unknown OS"
        self.versionInfo = row["app_version"] if row is not None else "0.0.0.0"
        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    def _createImage(self,row:pd.Series):
        imgName = row["locate_control_name"]
        imgBytes = row["window_img"]
        if not imgName or not imgBytes:
            return None
        imgFullPath = image_handler.save_image(imgName, image_data=imgBytes, output_path=str(self.imgPath))
        return imgFullPath
    
    def _removeImages(self):
        try:
            if os.path.exists(self.imgPath) and os.path.isdir(self.imgPath):
                shutil.rmtree(self.imgPath)
        except Exception as e:
            LOGGER_WARNING(f"Error removing image directory {self.imgPath}: {e}")

    def _getImageData(self,image_path):
        try:
            image_path = Path(image_path)
            LOGGER_DEBUG(f"🔍 Checking image path: {image_path}, exists={image_path.exists()}")
            img = Image.open(image_path)
            imgWhash = str(imagehash.whash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgWhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None
    
    def _getJiraTypeWithValue(self, row: pd.Series) -> list[tuple[str, str]]:
        compliance_map = {
            "focus_ring_result": "Focus Ring",
            "screen_reader_result": "Screen Reader",
            "i18n_reader_result": "i18n",
            "navigate_result": "Keyboard Navigation"
        }
        jira_list = []
        for col, jira_type in compliance_map.items():
            if col in row.index and "❌" in str(row[col]):
                jira_list.append((jira_type, row[col]))
        return jira_list
    
    def _getJiraLabels(self, jiraType: Optional[str]) -> Optional[list[str]]:
        labels = {
            "Focus Ring": ["WRS_FocusRing"],
            "i18n": ["WebexRegressShield_localization"],
            "Screen Reader": [],
            "Keyboard Navigation": ["KB_Navigate"]
        }
        return labels.get(jiraType) if jiraType is not None else None
    
    def _formatHash(self, row: pd.Series, jira_type: Optional[str] = None):
        if jira_type:
            return f"[{jira_type}][{self.osInfo}][{row['locate_control_name']}]"
        else:
            return f"[{self.osInfo}][{row['locate_control_name']}]"

    def _formatJiraTitle(self, row: pd.Series, jira_type: str, compliance_value: str):
        hash_val = self._formatHash(row, jira_type)
        title = f"{hash_val}[{compliance_value}]"
        return title
    
    def _formatJiraDescription(self,row:pd.Series, imageUrlMap = None):
        imageName = f"{row['locate_control_name']}.png"
        description = f'''h1. {{color:#172b4d}}WebEx APP Accessibility Report[{self.osInfo}][{self.versionInfo}]{{color}}\r\n\r\n'''
        display_columns = ["window_img", "test_case", "test_steps", "navigate_result", "focus_ring_result", "screen_reader_result", "screen_reader_description", "screen_reader_suggestions", "screen_reader_suggested_revision"]
        filtered_columns = [c for c in display_columns if c in row.index]
        description = description + "||" + "|| ".join(filtered_columns) + "||\r\n"
        rowReportStr = ""
        if not imageUrlMap:
            LOGGER_DEBUG("imageUrlMap is None")
        else:
            LOGGER_DEBUG(f"imageUrlMap keys: {list(imageUrlMap.keys())}, imageUrlMap values: {list(imageUrlMap.values())}")
        for col in filtered_columns:
            value = row[col]
            if pd.isna(value):
                value = ""
            if col == "window_img" and imageUrlMap and imageName in imageUrlMap:
                value = f'!{imageName}|thumbnail!'
            rowReportStr += f" | {value}"
        description += rowReportStr + " | \r\n\r\n"
        LOGGER_DEBUG(f"Jira description: {description}")

        return description
    
    def _fileJiraBug(self,row:pd.Series, jiraType: str, complianceValue: str):
        self.jiraType = jiraType
        title = self._formatJiraTitle(row, jiraType, complianceValue)
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
            imgFullPath = self._createImage(row) if row.get("window_img") else None
            if imgFullPath:
                imagePaths = [f"{imgFullPath}"]
                uploadedUrls = jira.upload_image(jiraID, imagePaths)
                if uploadedUrls:
                    imageName = f"{row['locate_control_name']}.png"
                    imageUrlMap = {imageName: uploadedUrls[0]} if uploadedUrls else {}
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
        if self.df is None or self.df.empty:
            LOGGER_WARNING(f"Table is empty, no data to process.")
            return
        df: pd.DataFrame = self.df
        complianceColumns = ["focus_ring_result", "screen_reader_result", "navigate_result"]
        validCols = [col for col in complianceColumns if col in df.columns]
        if not validCols:
            LOGGER_WARNING(f"No compliance fields found.")
            return
        mask = df[validCols].apply(lambda row: row.astype(str).str.contains("❌").any(), axis=1)
        df = df[mask]
        if df.empty:
            LOGGER_WARNING(f"No failed data found.")
            return
        df.reset_index(drop=True, inplace=True)
        maxCount = BUG_REPORT_LIMIT
        LOGGER_INFO(f'''max bug count: {maxCount}''')
        jiraInfos = []
        jiraIDs = []
        for _, row in df.iterrows():
            if maxCount is not None and maxCount <= 0:
                break
            jiraTypesWithValue = self._getJiraTypeWithValue(row)
            for jiraType, complianceValue in jiraTypesWithValue:
                self._readConfigs(row)
                self.jiraType = jiraType
                imgFullPath = self._createImage(row)
                imgPhash, imgBytes = self._getImageData(imgFullPath) if imgFullPath else (None, None)
                hashString = f"{self._formatHash(row)}"
                issueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
                controlName = row["locate_control_name"]
                testCase = row["test_case"]
                analysisResult = complianceValue
                sql = f'''select * from issue_by_wrs where (hash = "{issueHash}" or hashString = "{hashString}") and (status != "Done" OR resolution NOT IN ("Invalid","Won't Do","Working as designed","Duplicate"));'''
                results, columns = self.dbConnectionToIssue.Query(sql)
                if len(results) > 0:
                    existingJiraIds = [row[columns.index('jiraID')] for row in results]
                    existingIdsStr = ", ".join(existingJiraIds)
                    message = f'''[{self.jiraType}]: Found existing issue(s) in Jira (ID: {existingIdsStr}) with hash: {issueHash}, hashString: {hashString}'''
                    LOGGER_WARNING(message)
                    if isinstance(results[0], dict):
                        jiraIDs = [row[columns.index("jiraID")] for row in results]
                    elif isinstance(results[0], (tuple, list)) and columns:
                        try:
                            idx = columns.index("jiraID")
                            jiraIDs = [row[idx] for row in results]
                        except ValueError:
                            jiraIDs = []
                    else:
                        jiraIDs = []
                    if jiraIDs:
                        jiraIDs_str = ",".join(jiraIDs)
                        sql = f'''UPDATE TestCaseNavigateReport SET jira_issue_id = "{jiraIDs_str}" WHERE id = "{row["id"]}";'''
                        self.dbConnectionToTestcase.Execute(sql)
                    continue
                
                jiraID,title = self._fileJiraBug(row, jiraType, complianceValue)
                if jiraID is not None:
                    jiraIDs.append(jiraID)
                    jiraIDs_str = ",".join(jiraIDs)
                    LOGGER_INFO(f'''New {self.jiraType} bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                    if maxCount is not None:
                        maxCount = maxCount - 1
                    date = datetime.today().date()
                    sql1 = '''
                    INSERT INTO issue_by_wrs
                    (jiraID, title, affectVersion, platform, analysisResult, type, hash, hashString, testCase, controlName, imgBytes, imgHash, reportId, createDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    '''
                    values = (
                        jiraID,
                        title,
                        self.releaseVersion,
                        self.osInfo,
                        analysisResult,
                        self.jiraType,
                        issueHash,
                        hashString,
                        testCase,
                        controlName,
                        imgBytes,
                        imgPhash,
                        self.reportId,
                        str(date)
                    )
                    self.dbConnectionToIssue.ExecuteWithData(sql1, values)
                    sql2 = f'''UPDATE TestCaseNavigateReport SET jira_issue_id = "{jiraIDs_str}" WHERE id = "{row["id"]}";'''
                    self.dbConnectionToTestcase.Execute(sql2)
                    jiraInfos.append((jiraID,title))
        self._removeImages()
        self.FileNewJiraNotifition(jiraInfos)

        