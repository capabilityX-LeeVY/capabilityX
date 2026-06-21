
import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from tools.Jira.management.crawler.jira_crawler_manager import JiraCrawlerManager
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


def read_jql_file(jql_file_path: str) -> str:
    try:
        with open(jql_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        LOGGER_ERROR(f"Failed to read JQL file {jql_file_path}: {e}")
        return ""

manager = JiraCrawlerManager("src/config/jira_crawler_config.json")

jql_query = read_jql_file("my_accessibility_query.jql")

if jql_query:
    LOGGER_INFO("Running JQL crawl...")
    stats = manager.crawl_with_jql(
        jql_query=jql_query,
        max_results=5,
        update_existing=True
    )
    LOGGER_INFO(f"Crawl completed: {stats}")

manager.run_scheduler()