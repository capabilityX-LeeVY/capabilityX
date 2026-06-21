import os
import re
import pandas as pd
import hashlib
import json
import pymysql
import requests
import mimetypes
import imagehash

from jira import JIRA
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from typing import Optional

AUTHORIZATION = "Bearer NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G"
JIRA_token = 'NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G'


class ReportParserToJira(object):
    def __init__(self,fullPath,rowNumber) -> None:
        host = 'gc-hgh05-level2-lab-irc-5.cisco.com'
        port = 3306
        user = 'test'
        password = 'pass'
        dbName = 'issue_db'
        self.dbconnection = MysqlConnection(host,port,user,password,dbName)

        self.fullPath = fullPath
        self.fileName = self.fullPath.name
        self.df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(self.fullPath)
        self.rowNumber = rowNumber
        self.jobInfo = Path(self.fullPath).parents[2] / "wrs-job-info.json"
        print(f"Job info path: {self.jobInfo}")
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.jiraType = self._getJiraType(self.fileName)
        self.messageBot = MessageBot()

    def _readConfigs(self):
        if self.jobInfo.exists():
            try:
                with open(self.jobInfo, "r", encoding="utf-8") as f:
                    jobData = json.load(f)
                self.osInfo = jobData.get("deviceOS", "Unknown")
                self.versionInfo = jobData.get("appVersion", "0.0.0.0")
                self.reportId = jobData.get("reportId", None)
            except json.JSONDecodeError as e:
                print(f"Error reading job_info file: {e}")
        else:
            self.osInfo = "Unknown OS"
            self.versionInfo = "0.0.0.0"
            self.reportId = "Unknown report ID"
            print(f"Job info file does not exist: {self.jobInfo}")

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
        
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

    def _getImagePath(self,row:pd.Series):
        if "Image" not in row or pd.isna(row["Image"]):
            return None 
        img_html = str(row["Image"])
        match = re.search(r'src\s*=\s*"([^"]+)"', img_html)
        if match:
            imgRelPath = match.group(1).replace("\\", "/")
            mdPath = Path(self.fullPath).parent
            imgFullPaht = (mdPath / imgRelPath).resolve()
            return imgFullPaht
        return None

    def _getImageData(self,image_path):
        try:
            print(f"🔍 Checking image path: {image_path}, exists={image_path.exists()}")
            img = Image.open(image_path)
            imgWhash = str(imagehash.whash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgWhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None
    
    def _getJiraType(self, filename: str) -> Optional[str]:
        filenameLower = filename.lower()
        mapping = {
            "fr-report": "Focus Ring",
            "i18n-report": "i18n",
            "sr-report": "Screen Reader"
        }
        return next((v for k, v in mapping.items() if k in filenameLower), None)
    
    def _getJiraLabels(self, jiraType: Optional[str]) -> Optional[list[str]]:
        labels = {
            "Focus Ring": ["WebexRegressShield", "WRS_FocusRing"],
            "i18n": ["WebexRegressShield_localization"],
            "Screen Reader": ["WebexRegressShield"]
        }
        return labels.get(jiraType) if jiraType is not None else None
    
    def _formatHash(self,row:pd.Series):
        osInfo = self.osInfo.split(" ")[0] if self.osInfo else "Unknown OS"
        if self.jiraType == "i18n":
            return f"[{row['Analysis Result']}][{osInfo}][{row['Control Name']}]"
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
            print("imageUrlMap is None")
        else:
            print("imageUrlMap keys:", list(imageUrlMap.keys()), "imageUrlMap values:", list(imageUrlMap.values()))
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
        
        controlHistory = self._getControlHistoryFromResult(self.rowNumber)
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
                    else f"{{color:#FF0000}}*{val}*{{color}}" if idx == controlHistory.index[-2] and len(controlHistory) >= 2
                    else str(val)
                    for col, val in zip(controlHistory.columns, row)
                ) + " |"
                for idx, row in controlHistory.iterrows()
            )
            controlHistoryStr = f"h2. Traversal Context\r\n{table_header}{table_rows}\r\n\r\n"
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
        print(f'''Jira title: {title}''')
        print(f'''Jira description: {descripiton}''')

        if jiraID:
            imgFullPath = self._getImagePath(row) if row.get("Image") else None
            if imgFullPath:
                historyImages = []
                imgDirPath = imgFullPath.parent
                historyDF = self._getControlHistoryFromResult(self.rowNumber)
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
        print("ready to File New Jira Notifition....")
        if len(JiraInfos) == 0:
            return
        
        message = f"#### **New {self.jiraType} Issue(s) found:**\n"
        for jiraInfo in JiraInfos:
            jiraID = jiraInfo[0]
            title = jiraInfo[1]
            newLine = f'''* **[{jiraID}](https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID})** [{title}]\n'''
            message = message + newLine
        
        message = message + f'''* **[More ... ](https://jira-eng-gpk2.cisco.com/jira/secure/Dashboard.jspa?selectPageId=61721)**'''
        self.messageBot.sendMessageToTeams(message,roomId="a48ab4a0-7d98-11f0-95e9-4735252c61fe")

    def ParserReportAndFileBugs(self):
        self._readConfigs()
        df: pd.DataFrame = self.df
        df = df[df['No.'].astype(str).str.strip() == str(self.rowNumber)]
        if df.empty:
            print(f"No matching row found: row number [{self.rowNumber}].")
            return
        df.reset_index(drop=True, inplace=True)
        jiraInfos = []
        for _, row in df.iterrows():
            imgFullPath = self._getImagePath(row) if row.get("Image") else None
            imgPhash, imgBytes = self._getImageData(imgFullPath) if imgFullPath else (None, None)
            hashString = f"{self._formatHash(row)}"
            issueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
            controlName = row["Control Name"].strip()
            analysisResult = row["Analysis Result"].strip()
            sql = f'''select * from issue_by_wrs where (hash = "{issueHash}" or hashString = "{hashString}") and controlName != "unknown" and (status != "Done" OR resolution NOT IN ("Invalid"));'''
            results, columns = self.dbconnection.Query(sql)
            if len(results) > 0:
                existingJiraIds = [row[columns.index('jiraID')] for row in results]
                existingIdsStr = ", ".join(existingJiraIds)
                message = f'''[{self.jiraType}]: Found existing issue(s) in Jira (ID: {existingIdsStr}) with hash: {issueHash}, hashString: {hashString}'''
                print(message)
                continue
            
            jiraID,title = self._fileJiraBug(row)
            if jiraID is not None:
                print(f'''New focus ring bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
                date = datetime.today().date()
                sql1 = '''
                INSERT INTO issue_db.issue_by_wrs
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
                self.dbconnection.ExecuteWithData(sql1, values)
                jiraInfos.append((jiraID,title))

        self.FileNewJiraNotifition(jiraInfos)

class TeamsJiraIssueReporter(object):
    def __init__(self,summary,description,affectsVersions = None, fixversions = None):
        self.summary = summary
        self.description = description
        self.components = [{"name": "Client: Desktop (Windows and MacOS)"},]
        self.issuetype = {"name": "Bug"}
        self.epicLink = "SPARK-559755"
        self.project = {"key": "SPARK"}
        self.affectsVersions = affectsVersions #[{ "name": "WBS41.7.0"},]
        self.watchers = [] 
        self.Team = {"value": "Polaris"}
        self.found = { "value":"Test" }
        self.labels = ["accessibility", "RegressShield", "wrs_auto"]
        self.assignee = {"name":"binbiwan"}
        self.severity = {"value": "S3 - Moderate"}
        self.priority = {'name': "P3"}
        self.fixVersions = fixversions
        self.JIRA_token = JIRA_token

    def __formatBugPayload(self):
        payload = {}
        if self.summary is None:
            return None

        if self.description is None:
            return None

        payload['summary'] = self.summary
        payload['description'] = self.description
        payload['issuetype'] = self.issuetype
        payload['project'] = self.project
        payload['components'] = self.components
        payload['customfield_10712'] = self.found
        payload['customfield_10408'] = self.severity
        payload['priority'] = self.priority
        if self.epicLink is not None:
            payload['customfield_10001'] = self.epicLink
        if self.affectsVersions is not None:
            payload['versions'] = self.affectsVersions
        if self.fixVersions is not None:
            payload['fixVersions'] = self.fixVersions
        payload['customfield_11800'] = self.Team
        if self.labels is not None:
            payload['labels'] = self.labels

        if self.assignee is not None:
            payload['assignee'] = self.assignee
            
        return {"fields":payload}

    def __formatTaskPayload(self):
        payload = {}
        if self.summary is None:
            return None

        if self.description is None:
            return None

        payload['summary'] = self.summary
        payload['description'] = self.description
        payload['issuetype'] = {"name": "Task"}
        payload['project'] = self.project
        payload['components'] = self.components
        if self.epicLink is not None:
            payload['customfield_10001'] = self.epicLink
        payload['customfield_11800'] = self.Team
        if self.labels is not None:
            payload['labels'] = self.labels

        if self.assignee is not None:
            payload['assignee'] = self.assignee

        return {"fields": payload}

    def sendCreateIssueRequest(self,payload):
        url = "https://jira-eng-gpk2.cisco.com/jira/rest/api/2/issue/"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.JIRA_token} "
        }
        request_payload = json.dumps(payload)

        print(request_payload)
        response = requests.request(
            "POST",
            url,
            data=request_payload,
            headers=headers,
        )

        if response.status_code == 201:
            print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
            jiraID = json.loads(response.text)['key']
            return jiraID
        else:
            print(response,response.status_code,response.text)
            return None

    
    def ModifyWatcher(self,JiraID,watcher):
        J = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=self.JIRA_token)
        J.add_watcher(JiraID,watcher)

    def update_reporter(self, JiraID, reporter="binbiwan"):
        jira_url = 'https://jira-eng-gpk2.cisco.com/jira'
        jira = JIRA(server=jira_url, token_auth=JIRA_token)
        issue = jira.issue(JiraID)
        fields = {}
        fields['reporter'] = {'name': reporter}
        try:
            issue.update(fields)
        except Exception as e:
            print(f"reporter has no jira access: {JiraID}: {e}")

    def update_fields_for_issue(self,issue_id, field):
        jira_url = 'https://jira-eng-gpk2.cisco.com/jira'
        jira = JIRA(server=jira_url, token_auth=JIRA_token)
        try:
            issue = jira.issue(issue_id)
            issue.update(fields=field)
            return f'Successfully updated JIRA issue {issue_id}'
        except Exception as e:
            error_message = f'Failed to update JIRA issue {issue_id}: {e}'
            return error_message

    def creatTask(self):
        payload = self.__formatTaskPayload()
        JiraID = self.sendCreateIssueRequest(payload)
        if JiraID != None:
            for watcher in self.watchers:
                self.ModifyWatcher(JiraID, watcher)
            self.update_reporter(JiraID)
        return JiraID

    def creatBug(self):
        payload = self.__formatBugPayload()
        JiraID = self.sendCreateIssueRequest(payload)
        if JiraID !=None:
            print(f'''New Jira Created: https://jira-eng-gpk2.cisco.com/jira/browse/{JiraID}''')
            for watcher in self.watchers:
                self.ModifyWatcher(JiraID,watcher)
            self.update_reporter(JiraID)
        return JiraID
    
    def upload_image(self, issue_key, image_paths):
        headers = {
            "Authorization": AUTHORIZATION,
            "X-Atlassian-Token": "no-check"
        }
        url = f"https://jira-eng-gpk2.cisco.com/jira/rest/api/2/issue/{issue_key}/attachments"
        files = []
        try:
            for image_path in image_paths:
                mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
                files.append(("file", (image_path, open(image_path, "rb"), mime_type)))

            response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                response_data = response.json()
                uploaded_urls = [attachment["content"] for attachment in response_data]
                print("File upload success")
            else:
                print(f"File upload failed: {response.status_code}, {response.text}")
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()
        return uploaded_urls

    def delete_attachment(self, attachment_id):
        url = f"https://jira-eng-gpk2.cisco.com/jira/rest/api/2/attachment/{attachment_id}"
        headers = {
            "Authorization": AUTHORIZATION
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"Attachment {attachment_id} deleted successfully.")
        else:
            print(f"Failed to delete attachment {attachment_id}: {response.status_code}, {response.text}")

    @staticmethod
    def AddComments(jiraID,comments):
        J = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=JIRA_token)
        J.add_comment(jiraID, comments)

    @staticmethod
    def Search(jql):
        url = f'''https://jira-eng-gpk2.cisco.com/jira/rest/api/2/search?{jql}'''

        headers = {
            "Content-Type": "application/json",
            "Authorization":AUTHORIZATION
        }
        response = requests.request(
            "GET",
            url,
            headers=headers,
        )
        js = json.loads(response.text)
        issues = js["issues"]
        JiraIDs = []
        for issue in issues:
            JiraIDs.append(issue["key"])

        return JiraIDs
    
    @staticmethod
    def FilterAndUpdateTeamPT():
        jql = f'''jql=labels%20%3D%20WebexRegressSheild%20and%20"Epic%20Link"%20%3DSPARK-559755%20and%20"Team%2FPT"%20not%20in%20(Polaris)'''
        JiraIDs = TeamsJiraIssueReporter.Search(jql)
        for jiraID in JiraIDs:
            jira = TeamsJiraIssueReporter(None,None)
            fields = {}
            fields['reporter'] = {'name': "binbiwan"}
            fields['customfield_11800'] = {"value": "Polaris"}
            jira.update_fields_for_issue(jiraID,fields)
            print(f'''update: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID} to Polaris''')
#================================================================================================================================

class MysqlConnection(object):
    def __init__(self,host, port, user, password, dbName, charset = 'utf8mb4'):
        self.db = pymysql.connect(host= host, port=port,user=user, password=password,db=dbName, charset=charset)

    def __del__(self):
        if self.db:
            self.db.close()


    def Query(self,sql_statement):
        if self.db is None:
            return ((),())

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            results = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            return (results,columns)
        except:
            print ("Error: unable to fecth data","RED")
        
        return ((),())
        
    def Execute(self,sql_statement):
        if self.db is None:
            print('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg,"RED")
            self.db.rollback()
            return False
        
    def ExecuteWithData(self, sql_statement, data):
        if self.db is None:
            print('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, data)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg,"RED")
            self.db.rollback()
            return False
            
    def TableInfo(self):
        if self.db is None:
            return None
        cursor = self.db.cursor()
        columns = [item[0] for item in cursor.description]
        return columns
    
class MessageBot(object):
    def __init__(self):
        self.bear_token = "NWE0ZjBhZjEtNDUxZS00ZDNkLThhOGItMjcwNjUwMjFlNWZkMDI2NTY0MmQtY2Nl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"

    def sendMessageToTeams(self,message,roomId ="c0af0ac0-772f-11ef-9431-6382b932281b"):    
        if roomId is None:
            return 
        sparkapi = 'https://webexapis.com/v1/messages'
        headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Authorization': f'''Bearer {self.bear_token}'''
                }
        data = {"roomId": roomId, "text": "", "markdown": "%s" % (message)}
        try:
            req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
            if req.status_code == 200:
                print(f"Notify message bot succeeded. with room ID: ({roomId})")
            else:
                print(f"Notify message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
        except Exception as e:
            print(f"Notify message bot failed")

    def sendMessageToPerson(self,emailaddress, message): 
        if emailaddress is None:
            return
        sparkapi = 'https://webexapis.com/v1/messages'
        headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'Authorization': f'''Bearer {self.bear_token}'''
                }
        data = {"toPersonEmail": emailaddress, "text": "", "markdown": "%s" % (message)}
        try:
            req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
            if req.status_code == 200:
                print(f"Notify message bot succeeded. with person email: ({emailaddress})")
            else:
                print(f"Notify message bot failed, status code : {req.status_code} - {req.text} with person email: {emailaddress}")
        except Exception as e:
            print(f"Notify message bot failed: {e}")

    def sendCardToTeams(self,card_content, roomId="c0af0ac0-772f-11ef-9431-6382b932281b"):
        if roomId is None:
            return
            
        sparkapi = 'https://webexapis.com/v1/messages'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {self.bear_token}'''
        }
        
        data = {
            "roomId": roomId,
            "text": "Test Execution Report - please update your client to see the full card",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content
            }]
        }
        
        try:
            req = requests.post(sparkapi, data=json.dumps(data), headers=headers)
            if req.status_code == 200:
                print(f"Notify card message bot succeeded. with room ID: ({roomId})")
                return True
            else:
                print(f"Notify card message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
                return False
        except Exception as e:
            print(f"Notify card message bot failed: {e}")
            return False

    def sendCardToPerson(self,emailaddress, card_content):
        if emailaddress is None:
            return
            
        sparkapi = 'https://webexapis.com/v1/messages'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {self.bear_token}'''
        }
        
        data = {
            "toPersonEmail": emailaddress,
            "text": "Test Execution Report - please update your client to see the full card",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content
            }]
        }
        
        try:
            req = requests.post(sparkapi, data=json.dumps(data), headers=headers)
            if req.status_code == 200:
                print(f"Notify card message bot succeeded. with person email: ({emailaddress})")
                return True
            else:
                print(f"Notify card message bot failed, status code : {req.status_code} - {req.text} with person email: {emailaddress}")
                return False
        except Exception as e:
            print(f"Notify card message bot failed: {e}")
            return False
        
class MarkdownToDataframe(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def MarkdownToDataframe(path:str,startLine = 0) -> pd.DataFrame:
        from io import StringIO
        df = None
        with open(path,"r",encoding="utf-8",errors="ignore") as f:
            content = f.read()
            csv_data = "\n".join(line.strip('| ') for line in content.strip().split('\n')[startLine:])
            data = StringIO(csv_data)
            tmpDf = pd.read_csv(data, sep="|")
            tmpDf.columns = tmpDf.columns.str.strip()
            df = pd.DataFrame(tmpDf[1:])
            df.reset_index(drop=True, inplace=True)
            return df
        
        return df
    

    @staticmethod 
    def DataframeToHTML(df:pd.DataFrame,htmlPath):
        html = df.to_html(escape=False,index=False)
        styled_html = ""
        if len(html) != 0:
            styled_html = f"""
            <!DOCTYPE html> <html lang="zh">
            <head> <meta charset="UTF-8"> <style> 
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    tr:nth-child(odd) {{ background-color: #ffffff; }}
                    </style>
            </head> 
            <body> {html} </body>
            </html>
            """
            with open(htmlPath,"w+",encoding="utf-8",errors="ignore") as f:
                f.write(styled_html)


if __name__ == "__main__":
    fullPath = Path("/Users/weiqli/workF/wrs-output/WEIQLI-M-10GN_DQ4W10GNV4/20250829-104927/report/focus-ring/public_i18n-report-onfocus_45.10.0.32995.md")
    rowNum = 7
    jira = ReportParserToJira(fullPath,rowNum)
    jira.ParserReportAndFileBugs()