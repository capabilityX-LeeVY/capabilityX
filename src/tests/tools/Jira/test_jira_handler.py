import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from tools.Jira.jira_handler import JiraHandler

def test_custom_bug_query():
    """Test custom JQL query for bugs only"""
    print("🧪 Testing custom bug-only query...")
    
    try:
        # Test with custom JQL for bugs only
        custom_jql = 'labels = WebexRegressSheild and issuetype = Bug and status in (Open, New, "In Progress")'
        result = JiraHandler.count_issues_by_jql(custom_jql)
        
        if result:
            print(f"  ✅ Total Issues: {result['total_issues']}")
            print(f"  📋 JQL Query: {result['jql_query']}")
            print(f"  📊 Active Issues (Open/New/In Progress): {result['total_issues']}")
            
            print("\n  📋 Status Details:")
            for status, count in sorted(result['status_breakdown'].items()):
                print(f"    • {status}: {count}")
                
        else:
            print("  ❌ Failed to get results")
            
    except Exception as e:
        print(f"  ❌ Test failed with error: {e}")
        raise

def test_update_status_for_issue():
    jira_handler = JiraHandler("Test Summary", "Test Description")
    result = jira_handler.update_status_for_issue("SPARK-710104", "Done", "Resolved")
    result = jira_handler.update_status_for_issue("SPARK-710104", "In Progress")

    print(result)

if __name__ == "__main__":
    # test_custom_bug_query()
    test_update_status_for_issue()
