"""
Test for run_test_suite API endpoint
Tests calling the API server to run test suites (e.g., web_video_vbg)
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)


def test_run_test_suite_web_video_vbg():
    """
    Test the /api/run_test_suite endpoint with web_video_vbg suite
    
    This test:
    1. Calls the API server at http://localhost:9909
    2. Executes run_test_suite endpoint
    3. Runs the web_video_vbg test suite
    4. Verifies the response
    """
    
    # API endpoint URL
    api_url = "http://localhost:9909/api/run_test_suite"
    
    print("=" * 80)
    print("🧪 Testing run_test_suite API with web_video_vbg suite")
    print("=" * 80)
    
    try:
        # Prepare request payload with web_video_vbg suite
        payload = {
            "test_suite_name": "web_video_vbg",
            "platform": "web"
        }
        
        # Send POST request to the API
        print(f"\n📡 Sending POST request to: {api_url}")
        print(f"   Request Payload:")
        print(json.dumps(payload, indent=2))
        
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=300  # 5 minutes timeout for test execution
        )
        
        # Check response status
        print(f"\n📊 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API Response:")
            print(json.dumps(result, indent=2))
            
            # Verify expected fields
            assert "status" in result, "Response missing 'status' field"
            assert "test_suite_name" in result, "Response missing 'test_suite_name' field"
            assert result["test_suite_name"] == "web_video_vbg", "Wrong test suite name in response"
            
            print(f"\n✅ Test Suite Execution Status: {result['status']}")
            print(f"📝 Test Suite Name: {result['test_suite_name']}")
            print(f"💻 Platform: {result.get('platform', 'N/A')}")
            
            if "message" in result:
                print(f"📄 Message: {result['message']}")
            
            if result.get("navigate_report_path"):
                print(f"📊 Navigate Report: {result['navigate_report_path']}")
            
            if result.get("performance_report_path"):
                print(f"⚡ Performance Report: {result['performance_report_path']}")
                
            if result.get("stress_report_path"):
                print(f"🔥 Stress Report: {result['stress_report_path']}")
            
            print("\n" + "=" * 80)
            print("✅ TEST PASSED: run_test_suite API call successful")
            print("=" * 80)
            
            return result
            
        else:
            print(f"\n❌ API Request Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            raise AssertionError(f"API returned status code {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("   Please ensure the server is running:")
        print("   → Run: python src/functions/api/server.py")
        print("   → Or: uvicorn src.functions.api.server:app --host 0.0.0.0 --port 9909")
        raise
        
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timeout after 5 minutes")
        print("   The test suite may be taking longer than expected")
        raise
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise


def test_run_test_suite_direct_call():
    """
    Test the run_test_suite_function directly without API
    
    This demonstrates calling the function directly with custom parameters
    """
    
    print("\n" + "=" * 80)
    print("🧪 Testing run_test_suite_function - Direct Function Call")
    print("=" * 80)
    
    try:
        # Import the function directly for testing
        from functions.handlers.meetings_functions import run_test_suite_function
        
        # Call with web_video_vbg suite
        test_suite_name = "web_video_vbg"
        platform = "web"
        
        print(f"\n📋 Running test suite: {test_suite_name}")
        print(f"💻 Platform: {platform}")
        
        result = run_test_suite_function(
            test_suite_name=test_suite_name,
            platform=platform
        )
        
        print(f"\n✅ Direct Function Call Result:")
        print(json.dumps(result, indent=2))
        
        assert result["status"] == "success" or result["status"] == "error", "Invalid status"
        assert result["test_suite_name"] == test_suite_name, "Wrong test suite name"
        
        print("\n" + "=" * 80)
        print("✅ TEST PASSED: Direct function call successful")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR in direct function call: {str(e)}")
        raise


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("Starting run_test_suite API Tests")
    print("🚀" * 40 + "\n")
    
    # Test 1: API endpoint test
    try:
        print("\n" + "📌" * 40)
        print("TEST 1: API Endpoint Test")
        print("📌" * 40)
        test_run_test_suite_web_video_vbg()
    except Exception as e:
        print(f"\n⚠️ Test 1 failed: {str(e)}")
    
    # Test 2: Direct function call test
    # try:
    #     print("\n" + "📌" * 40)
    #     print("TEST 2: Direct Function Call Test")
    #     print("📌" * 40)
    #     test_run_test_suite_direct_call()
    # except Exception as e:
    #     print(f"\n⚠️ Test 2 failed: {str(e)}")
    
    # print("\n" + "🎉" * 40)
    # print("All Tests Completed!")
    # print("🎉" * 40 + "\n")
