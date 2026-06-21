import os
import sys


from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
from tools.Jira.e2eReportParserToJira import Ce2eReportParserToJira
from common.utils.logger import LOGGER_INFO



def test_e2e_jira():
    reportId = "33422e23-f60e-4c24-842a-f19383ef2d5f"
    e2e_jira = Ce2eReportParserToJira(reportId)
    e2e_jira.ParserReportAndFileBugs()

test_e2e_jira()