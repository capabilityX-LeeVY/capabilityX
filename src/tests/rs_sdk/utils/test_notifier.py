
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

from common.finalizer import notifier

def test_notifier_passed():
    """Test PASSED status notification"""
    print("🧪 Testing PASSED status...")
    execution_result = "PASSED"
    jira_open_count = 80  # Example Jira count
    output_url = "https://wrs.qa.webex.com/report/45.10.0/Dell-XPS15-Inteli9-Utral-High_72RX2D3/20250807-104629/"
    
    # Test card notification with Jira and failure details
    print("  📱 Sending card notification with Jira and failure details...")
    notifier.notify_messageBot_card(str(output_url), execution_result=execution_result, jira_open_count=jira_open_count,
                                   llm_failures=2, nav_failures=1, focus_ring_failures=3)
    print("  ✅ PASSED card with Jira and failure details sent successfully!")
    
def test_notifier_failed():
    """Test FAILED status notification"""
    print("🧪 Testing FAILED status...")
    execution_result = "FAILED - 3 tests failed, 2 timeout errors"
    jira_open_count = 125  # Example higher Jira count for failed case
    output_url = "https://wrs.qa.webex.com/report/45.10.0/Dell-XPS15-Inteli9-Utral-High_72RX2D3/20250807-104629/"
    
    # Test failed card notification with failure breakdown
    print("  📱 Sending FAILED card notification with failure breakdown...")
    notifier.notify_messageBot_card(str(output_url), execution_result=execution_result, jira_open_count=jira_open_count,
                                   llm_failures=5, nav_failures=3, focus_ring_failures=2)
    print("  ❌ FAILED card with failure breakdown sent successfully!")
    
def test_notifier_running():
    """Test RUNNING/other status notification"""
    print("🧪 Testing RUNNING status...")
    execution_result = "RUNNING - Test execution in progress (50% complete)"
    jira_open_count = 95  # Example Jira count for running case
    output_url = "https://wrs.qa.webex.com/report/45.10.0/Dell-XPS15-Inteli9-Utral-High_72RX2D3/20250807-104629/"
    
    # Test card notification with Jira
    print("  📱 Sending card notification with Jira...")
    notifier.notify_messageBot_card(str(output_url), execution_result=execution_result, jira_open_count=jira_open_count)
    print("  ℹ️ RUNNING card with Jira sent successfully!")
    


def test_all_statuses():
    """Test all notification statuses"""
    print("🚀 Testing card with 3 buttons design...\n")
    
    try:
        test_notifier_passed()
        print("\n" + "="*50 + "\n")
        
        test_notifier_failed()
        print("\n" + "="*50 + "\n")
        
        print("✅ All card tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

def test_jira_only():
    """Test just the Jira integration features"""
    print("🎯 Testing optimized 3-button card design...\n")
    
    try:
        print("🧪 Testing PASSED status with 3 buttons...")
        execution_result = "PASSED"
        jira_open_count = 80
        output_url = "https://wrs.qa.webex.com/report/45.10.0/Dell-XPS15-Inteli9-Utral-High_72RX2D3/20250807-104629/"
        
        print("  📱 Sending PASSED card with 3 buttons...")
        notifier.notify_messageBot_card(str(output_url), execution_result=execution_result, jira_open_count=jira_open_count)
        print("  ✅ PASSED card sent successfully!")
        
        print("\n" + "-"*30 + "\n")
        
        print("🧪 Testing FAILED status with 3 buttons...")
        execution_result = "FAILED - 3 tests failed, 2 timeout errors"
        jira_open_count = 125
        
        print("  📱 Sending FAILED card with 3 buttons...")
        notifier.notify_messageBot_card(str(output_url), execution_result=execution_result, jira_open_count=jira_open_count)
        print("  ❌ FAILED card sent successfully!")
        
        print("✅ 3-button card design test completed!")
        
    except Exception as e:
        print(f"❌ Card test failed with error: {e}")
        raise


if __name__ == "__main__":
    # Test options - uncomment the one you want to run:
    
    # 🚀 Run tests for PASSED and FAILED cases with 3 buttons
    test_all_statuses()
    
    # 🎯 Run detailed 3-button design tests
    # test_jira_only()
    
    # 📱 Run individual test functions:
    # test_notifier_passed()
    # test_notifier_failed()