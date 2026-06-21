import requests
import json
import mimetypes
from pathlib import Path
from jira import JIRA
from config.paths import SETTINGS_PATH
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_WARNING,LOGGER_INFO,LOGGER_ERROR

AUTHORIZATION = "Bearer NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G"
JIRA_token = 'NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G'

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
        self.labels = ["WebexRegressSheild", "accessibility", "RegressShield", "wrs_auto"]
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

        # print(request_payload)
        response = requests.request(
            "POST",
            url,
            data=request_payload,
            headers=headers,
        )

        if response.status_code == 201:
            # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
            jiraID = json.loads(response.text)['key']
            return jiraID
        else:
            # print(response,response.status_code,response.text)
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
        settings = DynamicConfig(SETTINGS_PATH)
        if settings.get('jira') == False:
            LOGGER_WARNING("creatTask failed, please run with param `--jira`","YELLOW")
            return None
        
        payload = self.__formatTaskPayload()
        JiraID = self.sendCreateIssueRequest(payload)
        if JiraID != None:
            for watcher in self.watchers:
                self.ModifyWatcher(JiraID, watcher)
            self.update_reporter(JiraID)
        return JiraID

    def creatBug(self):
        settings = DynamicConfig(SETTINGS_PATH)
        if settings.get('jira') == False:
            LOGGER_WARNING("creatBug failed, please run with param `--jira`","YELLOW")
            return None
        
        payload = self.__formatBugPayload()
        JiraID = self.sendCreateIssueRequest(payload)
        if JiraID !=None:
            LOGGER_INFO(f'''New Jira Created: https://jira-eng-gpk2.cisco.com/jira/browse/{JiraID}''')
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
                LOGGER_INFO(f"Response Data: {response_data}")
                uploaded_urls = [attachment["content"] for attachment in response_data]
                LOGGER_INFO("File upload success")
            else:
                LOGGER_ERROR(f"File upload failed: {response.status_code}, {response.text}")
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
            LOGGER_INFO(f"Attachment {attachment_id} deleted successfully.")
        else:
            LOGGER_ERROR(f"Failed to delete attachment {attachment_id}: {response.status_code}, {response.text}")

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
            LOGGER_INFO(f'''update: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID} to Polaris''')
#================================================================


if __name__ == "__main__":
    reporter = TeamsJiraIssueReporter("[*Platform*][ACC][*Control type*]Control Name can't be focused on 'Recognize hand gestures' ","Disconnect | Button | Press SPACE key |  Fail: not operable SPACE ")
    #reporter.epicLink = 'SPARK-342809' #Test Epic
    #reporter.labels = ["111","222"]
    JiraID = reporter.creatBug()
    print(JiraID)