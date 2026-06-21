"""
JIRA Handler Module

This module provides functionality for interacting with JIRA system, including:
- Creating Bug and Task
- Updating JIRA issues
- Counting bug statistics
- Managing attachments and comments

Author: WebexRegressShield Team
"""

import requests
import json
import mimetypes
from jira import JIRA
from config.paths import SETTINGS_PATH
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_WARNING, LOGGER_INFO, LOGGER_ERROR

# JIRA authentication configuration
AUTHORIZATION = "Bearer NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G"
JIRA_TOKEN = 'NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G'


class JiraHandler:
    """
    JIRA Handler Class
    
    Handles all interactions with JIRA system, including creating, updating and querying JIRA issues
    """
    def __init__(self, summary, description, affects_versions=None, fix_versions=None):
        """
        Initialize JIRA handler
        
        Args:
            summary: issue title
            description: issue description
            affects_versions: affected versions
            fix_versions: fix versions
        """
        self.summary = summary
        self.description = description
        self.components = [{"name": "Client: Desktop (Windows and MacOS)"}]
        self.issuetype = {"name": "Bug"}
        self.epicLink = "SPARK-559755"
        self.project = {"key": "SPARK"}
        self.affects_versions = affects_versions  # [{ "name": "WBS41.7.0"}]
        self.watchers = []
        self.team = {"value": "Polaris"}
        self.found = {"value": "Test"}
        self.labels = ["WebexRegressSheild"]
        self.assignee = {"name": "binbiwan"}
        self.severity = {"value": "S3 - Moderate"}
        self.priority = {'name': "P3"}
        self.fix_versions = fix_versions
        self.jira_token = JIRA_TOKEN

    def __format_bug_payload(self):
        """Format Bug payload"""
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
        if self.affects_versions is not None:
            payload['versions'] = self.affects_versions
        if self.fix_versions is not None:
            payload['fixVersions'] = self.fix_versions
        payload['customfield_11800'] = self.team
        if self.labels is not None:
            payload['labels'] = self.labels

        if self.assignee is not None:
            payload['assignee'] = self.assignee
            
        return {"fields":payload}

    def __format_task_payload(self):
        """Format Task payload"""
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
        payload['customfield_11800'] = self.team
        if self.labels is not None:
            payload['labels'] = self.labels

        if self.assignee is not None:
            payload['assignee'] = self.assignee

        return {"fields": payload}

    def send_create_issue_request(self, payload):
        """Send create issue request"""
        url = "https://jira-eng-gpk2.cisco.com/jira/rest/api/2/issue/"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jira_token} "
        }
        request_payload = json.dumps(payload)

        response = requests.request(
            "POST",
            url,
            data=request_payload,
            headers=headers,
        )

        if response.status_code == 201:
            jira_id = json.loads(response.text)['key']
            return jira_id
        else:
            LOGGER_ERROR(f"Failed to create issue: {response.status_code}, {response.text}")
            return None

    
    def modify_watcher(self, jira_id, watcher):
        """Add watcher to JIRA issue"""
        jira_client = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=self.jira_token)
        jira_client.add_watcher(jira_id, watcher)

    def update_reporter(self, jira_id, reporter="binbiwan"):
        """Update JIRA issue reporter"""
        jira_url = 'https://jira-eng-gpk2.cisco.com/jira'
        jira_client = JIRA(server=jira_url, token_auth=JIRA_TOKEN)
        issue = jira_client.issue(jira_id)
        fields = {}
        fields['reporter'] = {'name': reporter}
        try:
            issue.update(fields)
        except Exception as e:
            LOGGER_ERROR(f"Reporter has no jira access: {jira_id}: {e}")

    def update_fields_for_issue(self, issue_id, field):
        """Update JIRA issue fields"""
        jira_url = 'https://jira-eng-gpk2.cisco.com/jira'
        jira_client = JIRA(server=jira_url, token_auth=JIRA_TOKEN)
        try:
            issue = jira_client.issue(issue_id)
            issue.update(fields=field)
            return f'Successfully updated JIRA issue {issue_id}'
        except Exception as e:
            error_message = f'Failed to update JIRA issue {issue_id}: {e}'
            return error_message
        
    def update_status_for_issue(self, issue_id, status_name, resolution=None):
        """
        Update JIRA issue status
        
        Args:
            issue_id: JIRA issue ID (e.g., 'SPARK-123456')
            status_name: Target status name (e.g., 'In Progress', 'Done', 'Closed', 'To Do')
            resolution: Resolution when transitioning to Done (e.g., 'Done', 'Fixed', 'Won\'t Fix', 'Duplicate')
        
        Returns:
            str: Success or error message
        """
        jira_url = 'https://jira-eng-gpk2.cisco.com/jira'
        jira_client = JIRA(server=jira_url, token_auth=JIRA_TOKEN)
        
        try:
            issue = jira_client.issue(issue_id)
            current_status = issue.fields.status.name
            
            # Get available transitions for the issue
            transitions = jira_client.transitions(issue)
            
            # Find the transition that leads to the target status
            target_transition = None
            for transition in transitions:
                transition_to_name = transition['to']['name']
                # Exact match first, then case-insensitive match
                if transition_to_name == status_name or transition_to_name.lower() == status_name.lower():
                    target_transition = transition
                    break
            
            if target_transition is None:
                available_statuses = [t['to']['name'] for t in transitions]
                error_message = f'Status "{status_name}" is not available for issue {issue_id}.\n'
                error_message += f'Current status: {current_status}\n'
                error_message += f'Available transitions: {available_statuses}'
                LOGGER_ERROR(error_message)
                return error_message
            
            # Check if already in target status
            if current_status == status_name:
                success_message = f'JIRA issue {issue_id} is already in status "{status_name}"'
                LOGGER_INFO(success_message)
                return success_message
            
            # Prepare transition fields
            transition_fields = {}
            
            # If transitioning to Done and resolution is provided
            if status_name.lower() == 'done' and resolution:
                transition_fields['resolution'] = {'name': resolution}
            
            # Perform the transition with fields
            if transition_fields:
                jira_client.transition_issue(issue, target_transition['id'], fields=transition_fields)
                success_message = f'Successfully updated JIRA issue {issue_id} status from "{current_status}" to "{status_name}" with resolution "{resolution}"'
            else:
                jira_client.transition_issue(issue, target_transition['id'])
                success_message = f'Successfully updated JIRA issue {issue_id} status from "{current_status}" to "{status_name}"'
            
            LOGGER_INFO(success_message)
            return success_message
            
        except Exception as e:
            error_message = f'Failed to update JIRA issue {issue_id} status to "{status_name}": {e}'
            LOGGER_ERROR(error_message)
            return error_message

    def create_task(self):
        """Create JIRA task"""
        settings = DynamicConfig(SETTINGS_PATH)
        if settings.get('jira') == False:
            LOGGER_WARNING("create_task failed, please run with param `--jira`","YELLOW")
            return None
        
        payload = self.__format_task_payload()
        jira_id = self.send_create_issue_request(payload)
        if jira_id != None:
            for watcher in self.watchers:
                self.modify_watcher(jira_id, watcher)
            self.update_reporter(jira_id)
        return jira_id

    def create_bug(self):
        """Create JIRA Bug"""
        settings = DynamicConfig(SETTINGS_PATH)
        if settings.get('jira') == False:
            LOGGER_WARNING("create_bug failed, please run with param `--jira`","YELLOW")
            return None
        
        payload = self.__format_bug_payload()
        jira_id = self.send_create_issue_request(payload)
        if jira_id !=None:
            LOGGER_INFO(f'''New Jira Created: https://jira-eng-gpk2.cisco.com/jira/browse/{jira_id}''')
            for watcher in self.watchers:
                self.modify_watcher(jira_id, watcher)
            self.update_reporter(jira_id)
        return jira_id
    
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
                return uploaded_urls
            else:
                LOGGER_ERROR(f"File upload failed: {response.status_code}, {response.text}")
                return []
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()

    def delete_attachment(self, attachment_id):
        url = f"https://jira-eng-gpk2.cisco.com/jira/rest/api/2/attachment/{attachment_id}"
        headers = {
            "Authorization": AUTHORIZATION
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            return True
        else:
            LOGGER_ERROR(f"Failed to delete attachment {attachment_id}: {response.status_code}, {response.text}")
            return False

    @staticmethod
    def add_comments(jira_id, comments):
        """Add comment to JIRA issue"""
        jira_client = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=JIRA_TOKEN)
        jira_client.add_comment(jira_id, comments)
    
    @staticmethod
    def delete_comment(jira_id, comment_id):
        """
        Delete a comment from JIRA issue
        
        Args:
            jira_id: JIRA issue ID (e.g., 'SPARK-123456')
            comment_id: Comment ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            jira_client = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=JIRA_TOKEN)
            issue = jira_client.issue(jira_id)
            comment = jira_client.comment(jira_id, comment_id)
            comment.delete()
            LOGGER_INFO(f"Successfully deleted comment {comment_id} from JIRA issue {jira_id}")
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to delete comment {comment_id} from JIRA issue {jira_id}: {e}")
            return False
    
    @staticmethod
    def get_comments(jira_id):
        """
        Get all comments from a JIRA issue
        
        Args:
            jira_id: JIRA issue ID (e.g., 'SPARK-123456')
            
        Returns:
            list: List of comment objects with id, body, author, and created date
        """
        try:
            jira_client = JIRA(server='https://jira-eng-gpk2.cisco.com/jira', token_auth=JIRA_TOKEN)
            issue = jira_client.issue(jira_id)
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'author': comment.author.displayName,
                    'created': comment.created
                })
            return comments
        except Exception as e:
            LOGGER_ERROR(f"Failed to get comments from JIRA issue {jira_id}: {e}")
            return []
    

    @staticmethod
    def search(jql):
        """Search JIRA issues by JQL query"""
        url = f'''https://jira-eng-gpk2.cisco.com/jira/rest/api/2/search?{jql}'''

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTHORIZATION
        }
        response = requests.request(
            "GET",
            url,
            headers=headers,
        )
        js = json.loads(response.text)
        issues = js["issues"]
        jira_ids = []
        for issue in issues:
            jira_ids.append(issue["key"])

        return jira_ids
    
    @staticmethod
    def filter_and_update_team_pt():
        """Filter and update team/PT information"""
        jql = f'''jql=labels%20%3D%20WebexRegressSheild%20and%20"Epic%20Link"%20%3DSPARK-559755%20and%20"Team%2FPT"%20not%20in%20(Polaris)'''
        jira_ids = JiraHandler.search(jql)
        for jira_id in jira_ids:
            jira_handler = JiraHandler(None, None)
            fields = {}
            fields['reporter'] = {'name': "binbiwan"}
            fields['customfield_11800'] = {"value": "Polaris"}
            jira_handler.update_fields_for_issue(jira_id, fields)

    @staticmethod
    def count_issues_by_jql(jql=None):
        """
        Count issues by JQL query
        Args:
            jql: JQL query string. If None, defaults to WebexRegressShield bug filter
        Returns:
            dict: Dictionary containing issue count and detailed information
        """
        if jql is None:
            jql = 'labels = WebexRegressSheild and issuetype = Bug'
        
        url = 'https://jira-eng-gpk2.cisco.com/jira/rest/api/2/search'
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTHORIZATION
        }
        
        params = {
            'jql': jql,
            'maxResults': 1000,
            'fields': 'status,priority,summary,created,updated,issuetype'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                total_issues = data["total"]
                issues = data["issues"]
                
                status_counts = {}
                priority_counts = {}
                issuetype_counts = {}
                
                for issue in issues:
                    status = issue["fields"]["status"]["name"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    priority = issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else "Unset"
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                    
                    issuetype = issue["fields"]["issuetype"]["name"]
                    issuetype_counts[issuetype] = issuetype_counts.get(issuetype, 0) + 1
                
                result = {
                    "total_issues": total_issues,
                    "status_breakdown": status_counts,
                    "priority_breakdown": priority_counts,
                    "issuetype_breakdown": issuetype_counts,
                    "jql_query": jql
                }
                
                return result
                
            else:
                LOGGER_ERROR(f"Failed to fetch issue statistics: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Error counting issues by JQL: {e}")
            return None

    @staticmethod
    def count_bug_by_filter():
        """
        Count bugs in WebexRegressShield filter (backward compatibility)
        Returns:
            dict: Dictionary containing bug count and detailed information
        """
        return JiraHandler.count_issues_by_jql('labels = WebexRegressSheild and issuetype = Bug')
