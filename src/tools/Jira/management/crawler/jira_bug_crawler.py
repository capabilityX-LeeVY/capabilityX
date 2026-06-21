"""
Jira Bug Crawler
This module provides functionality for crawling Jira bugs and storing them in database
Author: WebexRegressShield Team
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from jira import JIRA
import re
from typing import Any, Dict
import pandas as pd
import os

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR
from tools.Jira.jira_handler import JIRA_TOKEN
from config.mysql import ConnectToJiraDB
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH
from tools.Jira.management.analyze.jira_steps_extractor import JiraStepsExtractor


class JiraBugCrawler:
    """
    Jira Bug Crawler Class
    Crawls Jira bugs and stores them in database
    """

    def __init__(self, project_key: str = "SPARK", database_name: str = "jira_crawler_db"):
        """
        Initialize Jira Bug Crawler
        
        Args:
            project_key: Jira project key (e.g., SPARK)
            database_name: Database name to store bugs
        """
        self.project_key = project_key
        self.database_name = database_name
        self.jira_server = 'https://jira-eng-gpk2.cisco.com/jira'
        self.jira_token = JIRA_TOKEN
        self.jira_client = None
        self.db_connection = None
        self.steps_extractor = JiraStepsExtractor()
        self._initialize_connections()
    
    def _initialize_connections(self) -> None:
        """Initialize JIRA and database connections"""
        try:
            # Initialize JIRA client
            self.jira_client = JIRA(server=self.jira_server, token_auth=self.jira_token)
            LOGGER_INFO("Successfully connected to JIRA")
            
            # Initialize database connection with custom database name
            LOGGER_INFO(f"Connecting to JIRA database {self.database_name}...")
            self.db_connection = ConnectToJiraDB(self.database_name)
            LOGGER_INFO("Successfully connected to database")
            
            # Create bugs table if not exists
            self._create_bugs_table()
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to initialize connections: {e}")
            raise
    
    def _create_bugs_table(self) -> None:
        """Create bugs table in database if not exists"""
        try:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{self.database_name}`.`jira_bugs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `jira_id` VARCHAR(50) UNIQUE NOT NULL,
                `project_key` VARCHAR(20) NOT NULL,
                `summary` TEXT NOT NULL,
                `description` LONGTEXT,
                `issue_type` VARCHAR(50),
                `status` VARCHAR(50),
                `priority` VARCHAR(20),
                `resolution` VARCHAR(50),
                `assignee` VARCHAR(100),
                `reporter` VARCHAR(100),
                `created_date` DATETIME,
                `updated_date` DATETIME,
                `resolved_date` DATETIME,
                `affects_versions` TEXT,
                `fix_versions` TEXT,
                `components` TEXT,
                `labels` TEXT,
                `environment` TEXT,
                `custom_fields` JSON,
                `steps` LONGTEXT COMMENT 'Extracted test steps as JSON string',
                `steps_count` INT DEFAULT 0 COMMENT 'Number of test steps extracted',
                `crawled_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX `idx_jira_id` (`jira_id`),
                INDEX `idx_project_key` (`project_key`),
                INDEX `idx_status` (`status`),
                INDEX `idx_created_date` (`created_date`),
                INDEX `idx_updated_date` (`updated_date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            self.db_connection.Execute(create_table_sql)
            LOGGER_INFO(f"Bugs table created/verified in database: {self.database_name}")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to create bugs table: {e}")
            raise
    
    def _build_jql_query(self, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        issue_types: Optional[List[str]] = None,
                        statuses: Optional[List[str]] = None,
                        updated_since: Optional[str] = None) -> str:
        """
        Build JQL query for searching bugs
        
        Args:
            start_date: Start date for created date filter (YYYY-MM-DD)
            end_date: End date for created date filter (YYYY-MM-DD)
            issue_types: List of issue types to filter (e.g., ['Bug', 'Task'])
            statuses: List of statuses to filter (e.g., ['Open', 'In Progress'])
            updated_since: Updated since date (YYYY-MM-DD)
            
        Returns:
            JQL query string
        """
        jql_parts = [f"project = {self.project_key}"]
        
        if start_date:
            jql_parts.append(f"created >= '{start_date}'")
        
        if end_date:
            jql_parts.append(f"created <= '{end_date}'")
        
        if updated_since:
            jql_parts.append(f"updated >= '{updated_since}'")
        
        if issue_types:
            types_str = "', '".join(issue_types)
            jql_parts.append(f"issuetype in ('{types_str}')")
        
        if statuses:
            statuses_str = "', '".join(statuses)
            jql_parts.append(f"status in ('{statuses_str}')")
        
        jql = " AND ".join(jql_parts)
        jql += " ORDER BY created DESC"
        
        return jql

    def _extract_and_process_steps(self, description: str) -> tuple[str, int]:
        """
        Extract test steps from description and return JSON string and count
        
        Args:
            description: Bug description text
            
        Returns:
            Tuple of (steps_json_string, steps_count)
        """
        try:
            if not description or not description.strip():
                return '[]', 0
            
            # Extract steps using TestStepsExtractor
            extracted_info = self.steps_extractor.extract_all(description)
            
            # Get just the steps
            steps = extracted_info.get('steps', [])
            
            if not steps:
                return '[]', 0
            
            # Convert to JSON string for database storage
            steps_json = json.dumps(steps, ensure_ascii=False, separators=(',', ':'))
            
            LOGGER_INFO(f"Extracted {len(steps)} test steps from description")
            return steps_json, len(steps)
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract steps from description: {e}")
            return '[]', 0
        
    def _extract_bug_data(self, issue: Any) -> Dict[str, Any]:
        """
        Extract bug data from JIRA issue object
        
        Args:
            issue: JIRA issue object
            
        Returns:
            Dictionary containing extracted bug data
        """
        try:
            # Basic fields
            bug_data = {
                'jira_id': issue.key,
                'project_key': issue.fields.project.key,
                'summary': issue.fields.summary,
                'description': getattr(issue.fields, 'description', None),
                'issue_type': issue.fields.issuetype.name,
                'status': issue.fields.status.name,
                'priority': getattr(issue.fields.priority, 'name', None) if issue.fields.priority else None,
                'resolution': getattr(issue.fields.resolution, 'name', None) if issue.fields.resolution else None,
                'assignee': getattr(issue.fields.assignee, 'displayName', None) if issue.fields.assignee else None,
                'reporter': getattr(issue.fields.reporter, 'displayName', None) if issue.fields.reporter else None,
                'environment': getattr(issue.fields, 'environment', None),
            }

            # Extract and process test steps
            steps_json, steps_count = self._extract_and_process_steps(bug_data['description'])
            bug_data['steps'] = steps_json
            bug_data['steps_count'] = steps_count

            # Date fields
            bug_data['created_date'] = self._parse_jira_datetime(issue.fields.created)
            bug_data['updated_date'] = self._parse_jira_datetime(issue.fields.updated)
            bug_data['resolved_date'] = self._parse_jira_datetime(getattr(issue.fields, 'resolutiondate', None))
            
            # Version fields
            bug_data['affects_versions'] = ', '.join([v.name for v in issue.fields.versions]) if issue.fields.versions else None
            bug_data['fix_versions'] = ', '.join([v.name for v in issue.fields.fixVersions]) if issue.fields.fixVersions else None
            
            # Components
            bug_data['components'] = ', '.join([c.name for c in issue.fields.components]) if issue.fields.components else None
            
            # Labels
            bug_data['labels'] = ', '.join(issue.fields.labels) if issue.fields.labels else None
            
            # Custom fields (store as JSON)
            custom_fields = {}
            for field_name in dir(issue.fields):
                if field_name.startswith('customfield_'):
                    field_value = getattr(issue.fields, field_name)
                    if field_value:
                        custom_fields[field_name] = str(field_value)

            custom_fields_json = self.safe_json_dumps(custom_fields)

            bug_data['custom_fields'] = custom_fields_json if custom_fields else None

            return bug_data
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract data from issue {issue.key}: {e}")
            return None

    def clean_json_data(self,data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self.clean_json_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_data(item) for item in data]
        elif isinstance(data, str):
            cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', data)
            try:
                cleaned.encode('utf-8').decode('utf-8')
                return cleaned
            except (UnicodeDecodeError, UnicodeEncodeError):
                return cleaned.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        else:
            return data

    def safe_json_dumps(self, data: Any) -> str:
        try:
            cleaned_data = self.clean_json_data(data)
            json_str = json.dumps(cleaned_data, ensure_ascii=False, separators=(',', ':'))
            json.loads(json_str)
            return json_str
        except (TypeError, ValueError, UnicodeDecodeError) as e:
            return '{}'
    
    def _parse_jira_datetime(self, jira_datetime: Optional[str]) -> Optional[str]:
        """
        Parse JIRA datetime format to MySQL datetime format
        
        Args:
            jira_datetime: JIRA datetime string
            
        Returns:
            MySQL datetime string or None
        """
        if not jira_datetime:
            return None
        
        try:
            # JIRA datetime format: 2023-12-01T10:30:00.000+0000
            if jira_datetime.endswith('+0000'):
                jira_datetime = jira_datetime[:-5] + '+00:00'
            jira_datetime = jira_datetime.replace('.000', '')  # Optional: remove milliseconds
            dt = datetime.fromisoformat(jira_datetime.replace('Z', '+00:00').replace('.000+', '+'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            LOGGER_WARNING(f"Failed to parse datetime {jira_datetime}: {e}")
            return None
    
    def _bug_exists_in_db(self, jira_id: str) -> bool:
        """
        Check if bug already exists in database
        
        Args:
            jira_id: JIRA issue ID
            
        Returns:
            True if bug exists, False otherwise
        """
        try:
            sql = f"SELECT COUNT(*) FROM `{self.database_name}`.`jira_bugs` WHERE `jira_id` = '{jira_id}'"
            results, _ = self.db_connection.Query(sql)
            return results[0][0] > 0 if results else False
        except Exception as e:
            LOGGER_ERROR(f"Failed to check if bug exists: {e}")
            return False
    
    def _insert_bug_to_db(self, bug_data: Dict[str, Any]) -> bool:
        """
        Insert bug data to database
        
        Args:
            bug_data: Dictionary containing bug data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare SQL statement
            columns = ", ".join([f"`{key}`" for key in bug_data.keys()])
            placeholders = ", ".join(["%s" for _ in bug_data.values()])
            
            sql = f"""
            INSERT INTO `{self.database_name}`.`jira_bugs` 
            ({columns}) 
            VALUES ({placeholders})
            """
            
            # Execute with parameters to prevent SQL injection
            values = [str(value) if value is not None else None for value in bug_data.values()]
            
            # Use direct execution for now (you might want to implement parameterized queries)
            escaped_values = []
            for value in values:
                if value is None:
                    escaped_values.append("NULL")
                else:
                    escaped_value = str(value).replace("'", "\\'").replace('"', '\\"')
                    escaped_values.append(f"'{escaped_value}'")
            
            final_sql = f"""
            INSERT INTO `{self.database_name}`.`jira_bugs` 
            ({columns}) 
            VALUES ({', '.join(escaped_values)})
            """
            
            self.db_connection.Execute(final_sql)
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to insert bug {bug_data.get('jira_id', 'unknown')}: {e}")
            return False
    
    def _update_bug_in_db(self, bug_data: Dict[str, Any]) -> bool:
        """
        Update existing bug data in database
        
        Args:
            bug_data: Dictionary containing bug data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            jira_id = bug_data['jira_id']
            
            # Build SET clause
            set_clauses = []
            for key, value in bug_data.items():
                if key != 'jira_id':  # Don't update the primary identifier
                    if value is None:
                        set_clauses.append(f"`{key}` = NULL")
                    else:
                        escaped_value = str(value).replace("'", "\\'").replace('"', '\\"')
                        set_clauses.append(f"`{key}` = '{escaped_value}'")
            
            sql = f"""
            UPDATE `{self.database_name}`.`jira_bugs` 
            SET {', '.join(set_clauses)}
            WHERE `jira_id` = '{jira_id}'
            """
            
            self.db_connection.Execute(sql)
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to update bug {bug_data.get('jira_id', 'unknown')}: {e}")
            return False
    
    def crawl_bugs(self, 
                   max_results: int = 1000,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   issue_types: Optional[List[str]] = None,
                   statuses: Optional[List[str]] = None,
                   updated_since: Optional[str] = None,
                   update_existing: bool = True) -> Dict[str, int]:
        """
        Crawl bugs from JIRA and store in database
        
        Args:
            max_results: Maximum number of results to fetch
            start_date: Start date for created date filter (YYYY-MM-DD)
            end_date: End date for created date filter (YYYY-MM-DD)
            issue_types: List of issue types to filter
            statuses: List of statuses to filter
            updated_since: Updated since date (YYYY-MM-DD)
            update_existing: Whether to update existing bugs
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_fetched': 0,
            'new_bugs': 0,
            'updated_bugs': 0,
            'failed_bugs': 0
        }
        
        try:
            # Build JQL query
            jql = self._build_jql_query(start_date, end_date, issue_types, statuses, updated_since)
            LOGGER_INFO(f"JQL Query: {jql}")
            
            # Search issues
            LOGGER_INFO(f"Starting to crawl bugs from JIRA...")
            issues = self.jira_client.search_issues(jql, maxResults=max_results, expand='changelog')
            
            stats['total_fetched'] = len(issues)
            LOGGER_INFO(f"Found {stats['total_fetched']} issues to process")
            
            # Process each issue
            for i, issue in enumerate(issues, 1):
                try:
                    # Extract bug data
                    bug_data = self._extract_bug_data(issue)
                    if not bug_data:
                        stats['failed_bugs'] += 1
                        continue
                    
                    # Check if bug exists
                    exists = self._bug_exists_in_db(bug_data['jira_id'])
                    
                    if exists and update_existing:
                        # Update existing bug
                        if self._update_bug_in_db(bug_data):
                            stats['updated_bugs'] += 1
                            LOGGER_INFO(f"Updated bug: {bug_data['jira_id']}")
                        else:
                            stats['failed_bugs'] += 1
                    elif not exists:
                        # Insert new bug
                        if self._insert_bug_to_db(bug_data):
                            stats['new_bugs'] += 1
                            LOGGER_INFO(f"Inserted new bug: {bug_data['jira_id']}")
                        else:
                            stats['failed_bugs'] += 1
                    
                    # Progress logging
                    if i % 50 == 0:
                        LOGGER_INFO(f"Processed {i}/{stats['total_fetched']} issues...")
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)
                    
                except Exception as e:
                    LOGGER_ERROR(f"Failed to process issue {issue.key}: {e}")
                    stats['failed_bugs'] += 1
                    continue
            
            LOGGER_INFO(f"Crawling completed. Stats: {stats}")
            return stats
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to crawl bugs: {e}")
            raise
    
    def crawl_by_jql(self, 
                     jql_query: str,
                     max_results: int = 1000,
                     update_existing: bool = True) -> Dict[str, int]:
        """
        Crawl bugs using custom JQL query
        
        Args:
            jql_query: Custom JQL query string
            max_results: Maximum number of results to fetch
            update_existing: Whether to update existing bugs
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_fetched': 0,
            'new_bugs': 0,
            'updated_bugs': 0,
            'failed_bugs': 0
        }
        
        try:
            LOGGER_INFO(f"Crawling bugs with JQL: {jql_query}")
            
            # Search issues using the provided JQL
            issues = self.jira_client.search_issues(jql_query, maxResults=max_results, expand='changelog')
            
            stats['total_fetched'] = len(issues)
            LOGGER_INFO(f"Found {stats['total_fetched']} issues to process")
            
            # Process each issue
            for i, issue in enumerate(issues, 1):
                try:
                    # Extract bug data
                    bug_data = self._extract_bug_data(issue)
                    if not bug_data:
                        stats['failed_bugs'] += 1
                        continue
                    
                    # Check if bug exists
                    exists = self._bug_exists_in_db(bug_data['jira_id'])
                    
                    if exists and update_existing:
                        # Update existing bug
                        if self._update_bug_in_db(bug_data):
                            stats['updated_bugs'] += 1
                            LOGGER_INFO(f"Updated bug: {bug_data['jira_id']}")
                        else:
                            stats['failed_bugs'] += 1
                    elif not exists:
                        # Insert new bug
                        if self._insert_bug_to_db(bug_data):
                            stats['new_bugs'] += 1
                            LOGGER_INFO(f"Inserted new bug: {bug_data['jira_id']}")
                        else:
                            stats['failed_bugs'] += 1
                    
                    # Progress logging
                    if i % 50 == 0:
                        LOGGER_INFO(f"Processed {i}/{stats['total_fetched']} issues...")
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)
                    
                except Exception as e:
                    LOGGER_ERROR(f"Failed to process issue {issue.key}: {e}")
                    stats['failed_bugs'] += 1
                    continue
            
            LOGGER_INFO(f"JQL crawling completed. Stats: {stats}")
            return stats
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to crawl bugs with JQL: {e}")
            raise

    def crawl_recent_bugs(self, days_back: int = 7) -> Dict[str, int]:
        """
        Crawl bugs updated in the last N days
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with statistics
        """
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        LOGGER_INFO(f"Crawling bugs updated since {since_date}")
        
        return self.crawl_bugs(
            updated_since=since_date,
            max_results=5000,
            update_existing=True
        )
    
    def crawl_bugs_by_project(self, project_keys: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Crawl bugs from multiple projects
        
        Args:
            project_keys: List of project keys to crawl
            
        Returns:
            Dictionary with statistics for each project
        """
        all_stats = {}
        
        for project_key in project_keys:
            LOGGER_INFO(f"Crawling bugs for project: {project_key}")
            original_project = self.project_key
            self.project_key = project_key
            
            try:
                stats = self.crawl_recent_bugs()
                all_stats[project_key] = stats
            except Exception as e:
                LOGGER_ERROR(f"Failed to crawl bugs for project {project_key}: {e}")
                all_stats[project_key] = {'error': str(e)}
            finally:
                self.project_key = original_project
        
        return all_stats
    
    def get_bug_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about bugs in database
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}
            
            # Total bugs count
            sql = f"SELECT COUNT(*) FROM `{self.database_name}`.`jira_bugs`"
            results, _ = self.db_connection.Query(sql)
            stats['total_bugs'] = results[0][0] if results else 0
            
            # Bugs by status
            sql = f"""
            SELECT status, COUNT(*) as count 
            FROM `{self.database_name}`.`jira_bugs` 
            GROUP BY status 
            ORDER BY count DESC
            """
            results, columns = self.db_connection.Query(sql)
            stats['by_status'] = {row[0]: row[1] for row in results} if results else {}
            
            # Bugs by priority
            sql = f"""
            SELECT priority, COUNT(*) as count 
            FROM `{self.database_name}`.`jira_bugs` 
            WHERE priority IS NOT NULL
            GROUP BY priority 
            ORDER BY count DESC
            """
            results, columns = self.db_connection.Query(sql)
            stats['by_priority'] = {row[0]: row[1] for row in results} if results else {}
            
            # Recent bugs (last 7 days)
            sql = f"""
            SELECT COUNT(*) 
            FROM `{self.database_name}`.`jira_bugs` 
            WHERE created_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            results, _ = self.db_connection.Query(sql)
            stats['recent_bugs_7days'] = results[0][0] if results else 0
            
            return stats
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to get bug statistics: {e}")
            return {}
    
    def crawl_bugs_by_ids(self, issue_ids: List[str], update_existing: bool = True) -> Dict[str, Any]:
        """
        Crawl specific bugs by Jira IDs
        
        Args:
            issue_ids: List of Jira issue IDs (e.g., ['SPARK-12345', 'SPARK-67890'])
            update_existing: Whether to update existing bugs in database
            
        Returns:
            Dictionary with crawling statistics
        """
        LOGGER_INFO(f"Starting to crawl {len(issue_ids)} specific bugs by IDs")
        
        stats = {
            'total_requested': len(issue_ids),
            'total_fetched': 0,
            'new_bugs': 0,
            'updated_bugs': 0,
            'failed_bugs': 0,
            'skipped_bugs': 0,
            'failed_ids': []
        }
        
        try:
            for issue_id in issue_ids:
                try:
                    LOGGER_INFO(f"Fetching issue: {issue_id}")
                    
                    # Get issue from Jira
                    issue = self.jira_client.issue(issue_id)
                    
                    # Extract bug data
                    bug_data = self._extract_bug_data(issue)
                    
                    # Check if bug exists in database
                    bug_exists = self._bug_exists_in_db(bug_data['jira_id'])
                    
                    if bug_exists:
                        if update_existing:
                            if self._update_bug_in_db(bug_data):
                                stats['updated_bugs'] += 1
                                LOGGER_INFO(f"Updated bug: {bug_data['jira_id']}")
                            else:
                                stats['failed_bugs'] += 1
                                stats['failed_ids'].append(issue_id)
                        else:
                            stats['skipped_bugs'] += 1
                            LOGGER_INFO(f"Skipped existing bug: {bug_data['jira_id']}")
                    else:
                        if self._insert_bug_to_db(bug_data):
                            stats['new_bugs'] += 1
                            LOGGER_INFO(f"Inserted new bug: {bug_data['jira_id']}")
                        else:
                            stats['failed_bugs'] += 1
                            stats['failed_ids'].append(issue_id)
                    
                    stats['total_fetched'] += 1
                    
                    # Small delay to avoid overwhelming Jira
                    time.sleep(0.1)
                    
                except Exception as e:
                    LOGGER_ERROR(f"Failed to process issue {issue_id}: {e}")
                    stats['failed_bugs'] += 1
                    stats['failed_ids'].append(issue_id)
            
            LOGGER_INFO(f"Completed crawling by IDs. Stats: {stats}")
            return stats
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to crawl bugs by IDs: {e}")
            raise
    
    def export_to_excel(self, bugs_data: List[Dict[str, Any]], output_file: str) -> bool:
        """
        Export bugs data to Excel file
        
        Args:
            bugs_data: List of bug dictionaries
            output_file: Output Excel file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not bugs_data:
                LOGGER_WARNING("No bugs data to export")
                return False
            
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Convert to DataFrame
            df = pd.DataFrame(bugs_data)
            
            # Reorder columns for better readability
            preferred_columns = [
                'jira_id', 'project_key', 'summary', 'status', 'priority', 
                'issue_type', 'assignee', 'reporter', 'created_date', 'updated_date',
                'resolution', 'resolved_date', 'affects_versions', 'fix_versions',
                'components', 'labels', 'description', 'environment', 
                'steps_count', 'steps', 'custom_fields'
            ]
            
            # Only include columns that exist in the data
            columns = [col for col in preferred_columns if col in df.columns]
            df = df[columns]
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Bugs', index=False)
                
                # Get the worksheet
                worksheet = writer.sheets['Bugs']
                
                # Adjust column widths
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    # Cap maximum width at 50
                    worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
            
            LOGGER_INFO(f"Successfully exported {len(bugs_data)} bugs to {output_file}")
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to export bugs to Excel: {e}")
            return False
    
    def close_connections(self) -> None:
        """Close all connections"""
        try:
            if self.db_connection:
                self.db_connection.close()
                LOGGER_INFO("Database connection closed")
        except Exception as e:
            LOGGER_ERROR(f"Failed to close connections: {e}")


if __name__ == "__main__":
    # Initialize crawler
    crawler = JiraBugCrawler(project_key="SPARK")
    
    try:
        # Crawl recent bugs (last 7 days)
        stats = crawler.crawl_recent_bugs(days_back=7)
        print(f"Crawling stats: {stats}")
        
        # Get database statistics
        db_stats = crawler.get_bug_statistics()
        print(f"Database stats: {db_stats}")
        
    finally:
        # Always close connections
        crawler.close_connections()
