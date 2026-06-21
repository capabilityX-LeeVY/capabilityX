from typing import Optional, List, Dict, Any
import json

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR
from config.mysql import ConnectToJiraDB


class JiraDBHandler:

    def __init__(self, database_name: str = "jira_crawler_db"):
        self.database_name = database_name
        self.db_connection = None
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        try:
            LOGGER_INFO(f"Connecting to JIRA database {self.database_name}...")
            self.db_connection = ConnectToJiraDB(self.database_name)
            LOGGER_INFO("Successfully connected to database")
        except Exception as e:
            LOGGER_ERROR(f"Failed to connect to database: {e}")
            raise
    
    def get_steps_by_jira_id(self, jira_id: str) -> Optional[List[Dict[str, Any]]]:
        try:
            sql = f"""
            SELECT steps, steps_count
            FROM `{self.database_name}`.`jira_bugs` 
            WHERE `jira_id` = '{jira_id}'
            """
            
            results, columns = self.db_connection.Query(sql)
            
            if results and len(results) > 0:
                steps_json = results[0][0]
                steps_count = results[0][1]
                
                if steps_json:
                    try:
                        steps = json.loads(steps_json)
                        LOGGER_INFO(f"Found {steps_count} steps for JIRA ID: {jira_id}")
                        return steps
                    except json.JSONDecodeError as e:
                        LOGGER_WARNING(f"Failed to parse steps JSON for {jira_id}: {e}")
                        return None
                else:
                    LOGGER_INFO(f"No steps found for JIRA ID: {jira_id}")
                    return None
            else:
                LOGGER_INFO(f"JIRA ID {jira_id} not found in database")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get steps for JIRA ID {jira_id}: {e}")
            return None
    
    def get_bug_info_by_jira_id(self, jira_id: str) -> Optional[Dict[str, Any]]:
        try:
            sql = f"""
            SELECT *
            FROM `{self.database_name}`.`jira_bugs` 
            WHERE `jira_id` = '{jira_id}'
            """
            
            results, columns = self.db_connection.Query(sql)
            
            if results and len(results) > 0:
                bug_info = dict(zip(columns, results[0]))
                
                if bug_info.get('steps'):
                    try:
                        bug_info['steps'] = json.loads(bug_info['steps'])
                    except json.JSONDecodeError:
                        bug_info['steps'] = []
                
                if bug_info.get('custom_fields'):
                    try:
                        bug_info['custom_fields'] = json.loads(bug_info['custom_fields'])
                    except json.JSONDecodeError:
                        bug_info['custom_fields'] = {}
                
                LOGGER_INFO(f"Found bug info for JIRA ID: {jira_id}")
                return bug_info
            else:
                LOGGER_INFO(f"JIRA ID {jira_id} not found in database")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get bug info for JIRA ID {jira_id}: {e}")
            return None
    
    def close_connection(self) -> None:
        try:
            if self.db_connection:
                self.db_connection.close()
                LOGGER_INFO("Database connection closed")
        except Exception as e:
            LOGGER_ERROR(f"Failed to close database connection: {e}")


if __name__ == "__main__":
    handler = JiraDBHandler()
    
    try:
        jira_id = "SPARK-12345"
        steps = handler.get_steps_by_jira_id(jira_id)
        
        if steps:
            LOGGER_INFO(f"Steps for {jira_id}:")
            for i, step in enumerate(steps, 1):
                LOGGER_INFO(f"  {i}. {step}")
        else:
            LOGGER_INFO(f"No steps found for {jira_id}")
            
        bug_info = handler.get_bug_info_by_jira_id(jira_id)
        if bug_info:
            LOGGER_INFO(f"\nBug summary: {bug_info.get('summary')}")
            LOGGER_INFO(f"Status: {bug_info.get('status')}")
            LOGGER_INFO(f"Steps count: {bug_info.get('steps_count')}")
        
    finally:
        handler.close_connection()