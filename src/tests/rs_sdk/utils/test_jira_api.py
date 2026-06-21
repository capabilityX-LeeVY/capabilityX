import os
import sys
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from pathlib import Path
from tools.Jira.jiraAPI import ReportParserToJira

def test_jira_api():
    fullPath = Path("/Users/weiqli/workF/wrs-output/WEIQLI-M-10GN_DQ4W10GNV4/20250828-101951/report/focus-ring/public_fr-report-onfocus_45.10.0.32989.md")
    rowNum = 3
    jira = ReportParserToJira(fullPath,rowNum)
    jira.ParserReportAndFileBugs()

test_jira_api()