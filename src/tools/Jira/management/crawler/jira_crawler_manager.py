"""
Jira Crawler Manager
Advanced management for Jira bug crawling with scheduling, notifications, and batch processing
Author: WebexRegressShield Team
"""

import json
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .jira_bug_crawler import JiraBugCrawler
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR
from common.handler.settingsHandler import DynamicConfig


class JiraCrawlerManager:
    """
    Advanced Jira Crawler Manager
    Handles scheduling, batch processing, and notifications
    """
    
    def __init__(self, config_path: str = "src/config/jira_crawler_config.json"):
        """
        Initialize Jira Crawler Manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.crawler = None
        self.is_running = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                LOGGER_INFO(f"Loaded configuration from {self.config_path}")
                return config.get('jira_crawler', {})
            else:
                LOGGER_WARNING(f"Configuration file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            LOGGER_ERROR(f"Failed to load configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "default_project": "SPARK",
            "default_database": "jira_crawler_db",
            "batch_size": 100,
            "delay_between_requests": 0.1,
            "max_retries": 3,
            "timeout": 30,
            "default_issue_types": ["Bug", "Task", "Story"],
            "excluded_statuses": ["Closed", "Resolved"],
            "custom_field_mappings": {},
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "teams_room_id": ""
            },
            "schedule": {
                "enabled": False,
                "cron_expression": "0 */6 * * *",
                "days_back": 1
            }
        }
    
    def _get_crawler(self, project_key: Optional[str] = None, 
                    database_name: Optional[str] = None) -> JiraBugCrawler:
        """Get or create crawler instance"""
        project = project_key or self.config.get('default_project', 'SPARK')
        database = database_name or self.config.get('default_database', 'jira_crawler_db')

        if not self.crawler or self.crawler.project_key != project:
            if self.crawler:
                self.crawler.close_connections()
            self.crawler = JiraBugCrawler(project_key=project, database_name=database)
        
        return self.crawler
    
    def crawl_with_retry(self, 
                        project_key: Optional[str] = None,
                        max_results: int = 1000,
                        days_back: int = 7,
                        **kwargs) -> Dict[str, int]:
        """
        Crawl bugs with retry mechanism
        
        Args:
            project_key: JIRA project key
            max_results: Maximum number of results
            days_back: Number of days to look back
            **kwargs: Additional parameters for crawling
            
        Returns:
            Dictionary with statistics
        """
        max_retries = self.config.get('max_retries', 3)
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                crawler = self._get_crawler(project_key)
                
                if days_back:
                    stats = crawler.crawl_recent_bugs(days_back=days_back)
                else:
                    stats = crawler.crawl_bugs(max_results=max_results, **kwargs)
                
                LOGGER_INFO(f"Crawling successful on attempt {attempt + 1}")
                return stats
                
            except Exception as e:
                LOGGER_ERROR(f"Crawling failed on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries - 1:
                    LOGGER_INFO(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    LOGGER_ERROR(f"All {max_retries} attempts failed")
                    raise
        
        return {}
    
    def crawl_with_jql(self, 
                       jql_query: str,
                       project_key: Optional[str] = None,
                       max_results: int = 1000,
                       update_existing: bool = True) -> Dict[str, int]:
        """
        Crawl bugs using JQL query with retry mechanism
        
        Args:
            jql_query: JQL query string
            project_key: JIRA project key (for logging)
            max_results: Maximum number of results
            update_existing: Whether to update existing bugs
            
        Returns:
            Dictionary with statistics
        """
        max_retries = self.config.get('max_retries', 3)
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                crawler = self._get_crawler(project_key)
                stats = crawler.crawl_by_jql(
                    jql_query=jql_query,
                    max_results=max_results,
                    update_existing=update_existing
                )
                
                LOGGER_INFO(f"JQL crawling successful on attempt {attempt + 1}")
                return stats
                
            except Exception as e:
                LOGGER_ERROR(f"JQL crawling failed on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries - 1:
                    LOGGER_INFO(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    LOGGER_ERROR(f"All {max_retries} attempts failed for JQL query")
                    raise
        
        return {}
    
    def batch_crawl_projects(self, 
                           project_keys: List[str],
                           days_back: int = 7) -> Dict[str, Dict[str, int]]:
        """
        Batch crawl multiple projects with progress tracking
        
        Args:
            project_keys: List of project keys to crawl
            days_back: Number of days to look back
            
        Returns:
            Dictionary with statistics for each project
        """
        all_stats = {}
        batch_size = self.config.get('batch_size', 5)
        delay = self.config.get('delay_between_requests', 0.1)
        
        LOGGER_INFO(f"Starting batch crawl for {len(project_keys)} projects")
        
        for i in range(0, len(project_keys), batch_size):
            batch = project_keys[i:i + batch_size]
            
            LOGGER_INFO(f"Processing batch {i//batch_size + 1}: {', '.join(batch)}")
            
            for project_key in batch:
                try:
                    LOGGER_INFO(f"Crawling project: {project_key}")
                    stats = self.crawl_with_retry(
                        project_key=project_key,
                        days_back=days_back
                    )
                    all_stats[project_key] = stats
                    
                    # Small delay between projects
                    time.sleep(delay)
                    
                except Exception as e:
                    LOGGER_ERROR(f"Failed to crawl project {project_key}: {e}")
                    all_stats[project_key] = {'error': str(e)}
            
            # Longer delay between batches
            if i + batch_size < len(project_keys):
                LOGGER_INFO(f"Batch completed. Waiting before next batch...")
                time.sleep(delay * 10)
        
        return all_stats
    
    def incremental_sync(self, 
                        project_key: Optional[str] = None,
                        hours_back: int = 6) -> Dict[str, int]:
        """
        Perform incremental sync of recently updated bugs
        
        Args:
            project_key: JIRA project key
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary with statistics
        """
        since_date = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d %H:%M')
        LOGGER_INFO(f"Performing incremental sync since {since_date}")
        
        crawler = self._get_crawler(project_key)
        
        # Get only updated bugs
        stats = crawler.crawl_bugs(
            updated_since=since_date[:10],  # Date part only
            max_results=5000,
            update_existing=True
        )
        
        LOGGER_INFO(f"Incremental sync completed: {stats}")
        return stats
    
    def full_project_sync(self, 
                         project_key: Optional[str] = None,
                         start_date: Optional[str] = None) -> Dict[str, int]:
        """
        Perform full synchronization of a project
        
        Args:
            project_key: JIRA project key
            start_date: Start date for synchronization (YYYY-MM-DD)
            
        Returns:
            Dictionary with statistics
        """
        project = project_key or self.config.get('default_project', 'SPARK')
        LOGGER_INFO(f"Starting full sync for project: {project}")
        
        crawler = self._get_crawler(project_key)
        
        # Get all bugs
        stats = crawler.crawl_bugs(
            start_date=start_date,
            max_results=50000,  # Large number for full sync
            update_existing=True
        )
        
        LOGGER_INFO(f"Full sync completed: {stats}")
        return stats
    
    def cleanup_old_data(self, 
                        days_old: int = 365,
                        dry_run: bool = True) -> Dict[str, int]:
        """
        Clean up old bug data from database
        
        Args:
            days_old: Days old to consider for cleanup
            dry_run: If True, only count records to be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        database = self.config.get('default_database', 'RegressShield')
        
        try:
            crawler = self._get_crawler()
            
            # Count old records
            cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            count_sql = f"""
            SELECT COUNT(*) 
            FROM `{database}`.`jira_bugs` 
            WHERE created_date < '{cutoff_date}' 
            AND status IN ('Closed', 'Resolved', 'Done')
            """
            
            results, _ = crawler.db_connection.Query(count_sql)
            old_count = results[0][0] if results else 0
            
            stats = {'old_records_found': old_count, 'deleted': 0}
            
            if not dry_run and old_count > 0:
                # Delete old records
                delete_sql = f"""
                DELETE FROM `{database}`.`jira_bugs` 
                WHERE created_date < '{cutoff_date}' 
                AND status IN ('Closed', 'Resolved', 'Done')
                """
                
                crawler.db_connection.Execute(delete_sql)
                stats['deleted'] = old_count
                LOGGER_INFO(f"Deleted {old_count} old records")
            
            return stats
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to cleanup old data: {e}")
            return {'error': str(e)}
    
    def get_crawl_health_report(self) -> Dict[str, Any]:
        """
        Generate health report for crawling operations
        
        Returns:
            Dictionary with health metrics
        """
        try:
            crawler = self._get_crawler()
            stats = crawler.get_bug_statistics()
            
            # Add health metrics
            health_report = {
                'database_stats': stats,
                'last_crawl_time': datetime.now().isoformat(),
                'config': {
                    'project': self.config.get('default_project'),
                    'database': self.config.get('default_database'),
                    'batch_size': self.config.get('batch_size'),
                },
                'recommendations': []
            }
            
            # Add recommendations based on data
            total_bugs = stats.get('total_bugs', 0)
            recent_bugs = stats.get('recent_bugs_7days', 0)
            
            if total_bugs == 0:
                health_report['recommendations'].append("No bugs found in database. Consider running full sync.")
            elif recent_bugs == 0:
                health_report['recommendations'].append("No recent bugs found. Check if incremental sync is working.")
            elif recent_bugs > 1000:
                health_report['recommendations'].append("High number of recent bugs. Consider increasing crawl frequency.")
            
            return health_report
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def setup_scheduled_crawling(self):
        """Setup scheduled crawling based on configuration"""
        schedule_config = self.config.get('schedule', {})
        
        if not schedule_config.get('enabled', False):
            LOGGER_INFO("Scheduled crawling is disabled")
            return
        
        days_back = schedule_config.get('days_back', 1)
        
        # Setup schedule (simplified - runs every 6 hours by default)
        schedule.every(6).hours.do(self._scheduled_crawl_job, days_back=days_back)
        
        LOGGER_INFO("Scheduled crawling enabled - runs every 6 hours")
    
    def _scheduled_crawl_job(self, days_back: int = 1):
        """Scheduled crawl job"""
        try:
            LOGGER_INFO("Starting scheduled crawl job")
            stats = self.incremental_sync(hours_back=days_back * 24)
            LOGGER_INFO(f"Scheduled crawl completed: {stats}")
            
            # Send notification if enabled
            self._send_notification(f"Scheduled crawl completed: {stats}")
            
        except Exception as e:
            LOGGER_ERROR(f"Scheduled crawl failed: {e}")
            self._send_notification(f"Scheduled crawl failed: {e}")
    
    def _send_notification(self, message: str):
        """Send notification (placeholder for Teams/Slack integration)"""
        notification_config = self.config.get('notification', {})
        
        if notification_config.get('enabled', False):
            # Placeholder for notification implementation
            LOGGER_INFO(f"Notification: {message}")
    
    def run_scheduler(self):
        """Run the scheduler"""
        self.setup_scheduled_crawling()
        self.is_running = True
        
        LOGGER_INFO("Crawler scheduler started")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            LOGGER_INFO("Scheduler stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the crawler manager"""
        self.is_running = False
        if self.crawler:
            self.crawler.close_connections()
        LOGGER_INFO("Crawler manager stopped")


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = JiraCrawlerManager()
    
    try:
        # Example operations
        
        # Incremental sync
        stats = manager.incremental_sync(project_key="SPARK", hours_back=24)
        print(f"Incremental sync stats: {stats}")
        
        # Batch crawl multiple projects
        projects = ["SPARK", "WEBEX"]
        batch_stats = manager.batch_crawl_projects(projects, days_back=7)
        print(f"Batch crawl stats: {batch_stats}")
        
        # Health report
        health = manager.get_crawl_health_report()
        print(f"Health report: {health}")
        
    finally:
        manager.stop()
