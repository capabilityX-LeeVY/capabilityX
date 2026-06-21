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
from typing import Optional, Union
from types import SimpleNamespace

AUTHORIZATION = "Bearer NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G"
JIRA_token = 'NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G'


class ReportParserToJira(object):
    def __init__(self, jira_info_file: Union[str, Path], pdf_file: Optional[Union[str, Path]] = None, 
                 control_img_file: Optional[Union[str, Path]] = None, windows_img_file: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize Jira bug reporter.
        
        Args:
            jira_info_file: Path to jira info JSON file (str or Path)
            pdf_file: Optional path to a single PDF file (str or Path)
            control_img_file: Optional path to control screenshot image (str or Path)
            windows_img_file: Optional path to Windows screenshot image (str or Path)
        """
        host = 'gc-hgh05-level2-lab-irc-5.cisco.com'
        port = 3306
        user = 'test'
        password = 'pass'
        dbName = 'issue_db'
        self.dbconnection = MysqlConnection(host,port,user,password,dbName)

        self.jiraInfo = Path(jira_info_file)
        self.pdf = Path(pdf_file) if pdf_file else None
        self.control_img = Path(control_img_file) if control_img_file else None
        self.windows_img = Path(windows_img_file) if windows_img_file else None
            
        self.jiraInfo = self._getJiraInfo(self.jiraInfo)
        self.jiraType = self.jiraInfo.jiraType
        self.jiraPlatform = self.jiraInfo.platform
        self.jiraControlName = self.jiraInfo.controlName or "unknown"
        self.jiraAnalysisResult = self.jiraInfo.analysisResult
        self.jiraLabels = self.jiraInfo.labels
        self.jiraAppVersion = self.jiraInfo.appVersion or '0.0.0.0'
        self.jiraWorkflow = self.jiraInfo.workflow
        self.jiraTestStep = self.jiraInfo.testStep
        self.jiraTestCase = self.jiraInfo.testCase
        self.jiraTestSuite = self.jiraInfo.testSuite
        self.jiraReportId = self.jiraInfo.reportId
        self.majorVersion, self.jiraVersion = self._getJiraVersion(self.jiraAppVersion)
        self.messageBot = MessageBot()

    def _getJiraInfo(self, jiraInfoFile: Path):
        if not jiraInfoFile.exists():
            raise FileNotFoundError(f"Jira info file not found: {jiraInfoFile}")
        with open(jiraInfoFile, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Jira info is empty: {jiraInfoFile}")
            data = json.loads(content, object_hook=lambda d: SimpleNamespace(**d))
            return data

    def _formatHash(self, jiraType, jiraPlatform, jiraControlName):
        parts = []
        if jiraType:
            parts.append(f"[{jiraType}]")
        if jiraPlatform:
            parts.append(f"[{jiraPlatform}]")
        parts.append(f"[{jiraControlName}]")
        return "".join(parts)

    def _formatJiraTitle(self, jiraAnalysisResult):
        title = self._formatHash(self.jiraType, self.jiraPlatform, self.jiraControlName)
        if jiraAnalysisResult:
            title = f"{title}[{jiraAnalysisResult}]"
        return title
    
    def _getImageData(self, image_path):
        try:
            img = Image.open(image_path)
            imgWhash = str(imagehash.whash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgWhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None

    def _getJiraVersion(self, jiraAppVersion):
        if jiraAppVersion:
            affectVersion = jiraAppVersion.split('.')
            if len(affectVersion) >=2:
                majorVersion = ".".join(affectVersion[:2])
        jiraVersion = [{ "name": f'''WxRel-{majorVersion}'''},]
        return majorVersion, jiraVersion
    
    def _formatJiraDescription(self, uploadedUrls):
        description = f"h1. {{color:#172b4d}}Accessibility Issue Report{{color}}\n\n"
        if self.jiraTestCase:
            description += f"*Test Case:* {self.jiraTestCase or 'N/A'}\n"
        description += f"*Control Name:* {self.jiraControlName or 'N/A'}\n"
        description += f"*Analysis Result:* {self.jiraAnalysisResult or 'N/A'}\n\n"
        if uploadedUrls and len(uploadedUrls) > 0:
            description += "h2. Attachments\n\n"
            for i, url in enumerate(uploadedUrls, 1):
                filename = url.split('/')[-1] if '/' in url else f"attachment_{i}"
                file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']:
                    description += f"!{filename}|thumbnail!\n"
                elif file_ext == 'pdf':
                    description += f"📄 [^{filename}]\n"
            description += "\n"
        if self.jiraReportId:
            description += f"*Report ID:* {self.jiraReportId}\n"
        return description
        
    def _fileJiraBug(self):
        title = self._formatJiraTitle(self.jiraAnalysisResult)
        description = self._formatJiraDescription([])
        jira = TeamsJiraIssueReporter(title, description, self.jiraVersion)
        if self.jiraLabels:
            jira.labels.extend(self.jiraLabels)
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        print(f'''Jira title: {title}''')
        print(f'''Jira description: {description}''')

        if jiraID:
            uploaded_files = []
            try:
                imagePaths = []
                if self.control_img:
                    imagePaths.append(str(self.control_img))
                if self.windows_img:
                    imagePaths.append(str(self.windows_img))
                if imagePaths:
                    uploadedUrls = jira.upload_attachments(jiraID, imagePaths)
                    if uploadedUrls:
                        uploaded_files.extend(uploadedUrls)
                if self.pdf:
                    pdfPaths = [str(self.pdf)]
                    pdfUrls = jira.upload_attachments(jiraID, pdfPaths)
                    if pdfUrls:
                        uploaded_files.extend(pdfUrls)
                        print(f"✅ PDF uploaded successfully")
                if uploaded_files:
                    description = self._formatJiraDescription(uploaded_files)
                    jira.update_fields_for_issue(jiraID, {"description": description})
            except Exception as upload_err:
                print(f"⚠️  Warning: File upload encountered an error: {upload_err}")
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
        jiraInfos = []
        
        imgPhash, imgBytes = None, None
        if self.control_img and self.control_img.exists():
            imgPhash, imgBytes = self._getImageData(self.control_img)
        elif self.windows_img and self.windows_img.exists():
            imgPhash, imgBytes = self._getImageData(self.windows_img)
        
        hashString = f"{self._formatHash(self.jiraType, self.jiraPlatform, self.jiraControlName)}"
        issueHash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()
        sql = f'''select * from issue_by_wrs where (hash = "{issueHash}" or hashString = "{hashString}") and controlName != "unknown" and (status != "Done" OR resolution NOT IN ("Invalid"));'''
        results, columns = self.dbconnection.Query(sql)
        if len(results) > 0:
            existingJiraIds = [result[columns.index('jiraID')] for result in results]
            existingIdsStr = ", ".join(existingJiraIds)
            message = f'''[{self.jiraType}]: Found existing issue(s) in Jira (ID: {existingIdsStr}) with hash: {issueHash}, hashString: {hashString}'''
            print(message)
            return
        
        jiraID, title = self._fileJiraBug()
        if jiraID is not None:
            print(f'''New bug filed: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}''')
            date = datetime.today().date()
            sql1 = '''
            INSERT INTO issue_db.issue_by_wrs
            (jiraID, title, affectVersion, platform, analysisResult, type, status, hash, hashString, controlName, imgBytes, imgHash, testStep, testCase, testSuite, reportId, createDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            values = (
                jiraID,
                title,
                self.majorVersion or "0.0",
                self.jiraPlatform or "Unknown",
                self.jiraAnalysisResult,
                self.jiraType,
                "New",
                issueHash,
                hashString,
                self.jiraControlName,
                imgBytes,
                imgPhash,
                self.jiraTestStep,
                self.jiraTestCase,
                self.jiraTestSuite,
                self.jiraReportId,
                str(date)
            )
            try:
                self.dbconnection.ExecuteWithData(sql1, values)
                jiraInfos.append((jiraID, title))
            except Exception as e:
                print(f"⚠️  Warning: Failed to insert Jira info to database: {e}")
                jiraInfos.append((jiraID, title))

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
        self.labels = ["accessibility", "RegressShield", "WebexRegressShield", "wrs_auto"]
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
    
    def upload_attachments(self, issue_key, file_paths):
        headers = {
            "Authorization": AUTHORIZATION,
            "X-Atlassian-Token": "no-check"
        }
        url = f"https://jira-eng-gpk2.cisco.com/jira/rest/api/2/issue/{issue_key}/attachments"
        files = []
        uploaded_urls = []
        
        try:
            for file_path in file_paths:
                try:
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        print(f"⚠️  Warning: File not found: {file_path}")
                        continue
                    
                    file_size = file_path_obj.stat().st_size
                    if file_size > 100 * 1024 * 1024:
                        print(f"⚠️  Warning: File too large (>100MB), skipping: {file_path}")
                        continue
                    
                    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
                    file_name = file_path_obj.name
                    try:
                        file_name_encoded = file_name.encode('utf-8').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError) as enc_err:
                        print(f"⚠️  Warning: Filename encoding issue: {file_name}, error: {enc_err}")
                        # Try ASCII-safe fallback
                        file_name_encoded = file_path_obj.stem.encode('ascii', 'ignore').decode('ascii') + file_path_obj.suffix
                    files.append(("file", (file_name_encoded, open(file_path, "rb"), mime_type)))
                    
                except Exception as file_err:
                    print(f"⚠️  Warning: Error processing file {file_path}: {file_err}")
                    continue

            if not files:
                print("ℹ️  No valid files to upload, continuing with other operations...")
                return uploaded_urls

            response = requests.post(url, headers=headers, files=files, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                uploaded_urls = [attachment["content"] for attachment in response_data]
                file_names = [attachment["filename"] for attachment in response_data]
                print(f"✅ File upload success: {', '.join(file_names)}")
            else:
                print(f"⚠️  File upload failed: {response.status_code}, {response.text}")
                print("ℹ️  Continuing with other operations...")
                
        except requests.exceptions.Timeout:
            print("⚠️  File upload timeout, continuing with other operations...")
        except requests.exceptions.RequestException as req_err:
            print(f"⚠️  Network error during file upload: {req_err}, continuing with other operations...")
        except Exception as e:
            print(f"⚠️  Unexpected error during file upload: {e}, continuing with other operations...")
        finally:
            for _, file_tuple in files:
                try:
                    if file_tuple[1] and not file_tuple[1].closed:
                        file_tuple[1].close()
                except Exception as close_err:
                    print(f"⚠️  Warning: Error closing file: {close_err}")
                
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
    json_file = Path("/Users/weiqli/test data/api/test_jira_info.json")
    pdf_file = Path("/Users/weiqli/test data/api/pdf_test.pdf")
    control_img = Path("/Users/weiqli/test data/api/control_test.png")
    windows_img = Path("/Users/weiqli/test data/api/window_test.png")
    
    jira = ReportParserToJira(
        jira_info_file=json_file,
        pdf_file=pdf_file if pdf_file.exists() else None,
        control_img_file=control_img if control_img.exists() else None,
        windows_img_file=windows_img if windows_img.exists() else None
    )
    
    jira.ParserReportAndFileBugs()