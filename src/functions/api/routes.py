"""
API routes definition
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from functions.registry import function_registry
from functions.schemas.api_schemas import (
    BaseResponse,
    StartMeetingResponse,
    EndMeetingResponse,
    InvitePeopleResponse,
    WhoAreYouResponse,
    FunctionListResponse,
    GreetUserRequest,
    GreetUserResponse,
    StartCallingResponse,
    RunTestSuiteRequest,
    RunTestSuiteResponse,
    RunTestCaseRequest,
    RunTestCaseResponse,
    StressTestRequest,
    StressTestResponse
)
from functions.schemas.dynamic_test_case_schemas import (
    DynamicTestCaseRequest,
    DynamicTestCaseResponse
)
from functions.handlers.meetings_functions import (
    run_test_suite_function,
    run_test_case_function, 
    run_stress_test_function
)
from rs_sdk.utils.test_case_discovery import test_case_discovery

router = APIRouter()


@router.post("/run_meetings_functions", response_model=StartMeetingResponse)
def run_meetings_functions():
    """Start a Webex meeting"""
    try:
        result = function_registry.execute_function('run_meetings_functions')
        return StartMeetingResponse(status="Meeting started")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/start_pmr_meeting", response_model=StartMeetingResponse)
def start_pmr_meeting():
    """Start a Webex meeting"""
    try:
        function_registry.execute_function('start_pmr_meeting')
        return StartMeetingResponse(status="Meeting started")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end_meeting", response_model=EndMeetingResponse)
def end_meeting():
    """End a Webex meeting"""
    try:
        function_registry.execute_function('end_meeting')
        return EndMeetingResponse(status="Meeting ended")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invite_people", response_model=BaseResponse)
def invite_people():
    """Invite people to a Webex meeting"""
    try:
        function_registry.execute_function('invite_people')
        return BaseResponse(message="People invited")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/start_screen_sharing", response_model=BaseResponse)
def start_screen_sharing():
    """Start screen sharing"""
    try:
        function_registry.execute_function('start_screen_sharing')
        return BaseResponse(message="Screen sharing started")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/stop_screen_sharing", response_model=BaseResponse)
def stop_screen_sharing():
    """Stop screen sharing"""
    try:
        function_registry.execute_function('stop_screen_sharing')
        return BaseResponse(message="Screen sharing stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run_test_suite", response_model=RunTestSuiteResponse)
def run_test_suite(request: RunTestSuiteRequest):
    """
    Run a test suite
    
    Args:
        request: RunTestSuiteRequest containing test_suite_name and optional platform
        
    Returns:
        RunTestSuiteResponse with execution results
        
    Example:
        POST /run_test_suite
        {
            "test_suite_name": "web_video_vbg",
            "platform": "windows"
        }
    """
    try:
        platform = request.platform or "windows"  # Default to "windows" if None
        
        result = run_test_suite_function(
            test_suite_name=request.test_suite_name,
            platform=platform
        )
        
        return RunTestSuiteResponse(
            status=result["status"],
            message=result["message"],
            test_suite_name=result["test_suite_name"],
            platform=result["platform"],
            navigate_report_path=result.get("navigate_report_path"),
            performance_report_path=result.get("performance_report_path"),
            stress_report_path=result.get("stress_report_path")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to execute test suite: {str(e)}"
        )


@router.post("/run_test_case", response_model=RunTestCaseResponse)
def run_test_case(request: RunTestCaseRequest):
    """
    Run a specific test case
    
    Args:
        request: RunTestCaseRequest containing test_case_name and optional platform
        
    Returns:
        RunTestCaseResponse with execution results
        
    Example:
        POST /run_test_case
        {
            "test_case_name": "sign_in",
            "platform": "windows"
        }
    """
    try:
        platform = request.platform or "windows"  # Default to "windows" if None
        
        result = run_test_case_function(
            test_case_name=request.test_case_name,
            platform=platform
        )
        
        return RunTestCaseResponse(
            status=result["status"],
            message=result["message"],
            test_case_name=result["test_case_name"],
            navigate_report_path=result.get("navigate_report_path"),
            performance_report_path=result.get("performance_report_path"),
            stress_report_path=result.get("stress_report_path")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to execute test case: {str(e)}"
        )


@router.post("/run_calling_functions", response_model=StartCallingResponse)
def run_calling_functions():
    """Start a calling"""
    try:
        result = function_registry.execute_function('run_calling_functions')
        return StartCallingResponse(status="calling started")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/run_bwc_calling_functions", response_model=StartCallingResponse)
def run_bwc_calling_functions():
    """Start bwc a calling"""
    try:
        result = function_registry.execute_function('run_bwc_calling_functions')
        return StartCallingResponse(status="bwc calling started")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run_init_app_functions", response_model=StartCallingResponse)
def run_init_app_functions():
    """Start restart app"""
    try:
        result = function_registry.execute_function('run_init_app_functions')
        return StartCallingResponse(status="restart app")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/uninstall_app", response_model=BaseResponse)
def uninstall_app():
    """Uninstall app"""
    try:
        result = function_registry.execute_function('uninstall_app')
        return BaseResponse(message="uninstall app")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/install_app", response_model=BaseResponse)
def install_app():
    """Install app"""
    try:
        result = function_registry.execute_function('install_app')
        return BaseResponse(message="install app")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/who_are_you", response_model=WhoAreYouResponse)
def who_are_you():
    """Get information about the AI assistant"""
    try:
        result = function_registry.execute_function('who_are_you')
        return WhoAreYouResponse(status=result.get("response"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/greet_user", response_model=GreetUserResponse)
def greet_user(request: GreetUserRequest):
    """Greet a user with their name"""
    try:
        result = function_registry.execute_function('greet_user', request.name)
        return GreetUserResponse(greeting=result.get("greeting"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync_code")
def sync_code(remote: Optional[str] = None, branch: Optional[str] = None, restart: bool = True):
    from functions.handlers.meetings_functions import sync_code as _sync
    result = _sync(remote=remote, branch=branch, restart=restart)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/start_video")
def start_video():
    """Start video in meeting"""
    try:
        result = function_registry.execute_function('start_video')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop_video")
def stop_video():
    """Stop video in meeting"""
    try:
        result = function_registry.execute_function('stop_video')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/current_time")
def get_current_time():
    """Get current time"""
    try:
        result = function_registry.execute_function('get_current_time')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current_date")
def get_current_date():
    """Get current date"""
    try:
        result = function_registry.execute_function('get_date')
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run_stress_test", response_model=StressTestResponse)
def run_stress_test(request: StressTestRequest):
    """
    Execute stress test (test_stress.yaml)
    
    Stress test workflow:
    1. Sign in → 2. Start PMR meeting → 3. Send stress message → 4. Chat test → 5. End meeting
    """
    try:
        from datetime import datetime
        import uuid
        
        # Generate unique execution ID
        execution_id = f"stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Call stress test handler function
        result = run_stress_test_function(
            test_case_name=request.test_case_name,
            platform=request.platform,
            stress_duration=request.stress_duration,
            participant_count=request.participant_count,
            custom_message=request.custom_message,
            enable_chat_test=request.enable_chat_test,
            enable_video=request.enable_video,
            enable_audio=request.enable_audio
        )
        
        return StressTestResponse(
            status=result["status"],
            message=result["message"],
            test_case_name=request.test_case_name,
            execution_id=execution_id,
            start_time=datetime.now().isoformat(),
            estimated_duration=request.stress_duration + 120,  # 加上准备时间
            stress_config=result["stress_config"],
            result_url=result.get("result_url"),  # Add the upload URL
            navigate_report_path=result.get("navigate_report_path"),
            performance_report_path=result.get("performance_report_path"),
            stress_report_path=result.get("stress_report_path")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute stress test: {str(e)}"
        )


@router.get("/test_unregistered")
def test_unregistered():
    try:
        result = function_registry.execute_function('non_existent_function')
        return {"result": result}
    except Exception as e:
        return {"error": str(e), "message": "This demonstrates what happens when a function is not registered"}


# ==================== Dynamic Test Case API Routes ====================
# These routes allow calling any test case directly without manual registration

@router.post("/dynamic/run_test_case", response_model=DynamicTestCaseResponse)
def dynamic_run_test_case(request: DynamicTestCaseRequest):
    """
    Dynamically run any test case from test_space/test_cases directory
    
    This endpoint automatically discovers and executes test cases without requiring
    manual registration in api_config.json, registry.py, or routes.py
    
    Args:
        request: DynamicTestCaseRequest containing:
            - test_case_name: Test case path (e.g., 'jmt/basic/start_pmr_meeting')
            - platform: Platform to run on (default: 'windows')
        
    Returns:
        DynamicTestCaseResponse with execution results
        
    Examples:
        POST /dynamic/run_test_case
        {
            "test_case_name": "jmt/basic/start_pmr_meeting",
            "platform": "windows"
        }
        
        POST /dynamic/run_test_case
        {
            "test_case_name": "meetings/share/start_screen_sharing",
            "platform": "windows"
        }
    """
    from common.utils.logger import LOGGER_INFO
    
    try:
        # Validate test case exists
        if not test_case_discovery.is_valid_test_case(request.test_case_name):
            raise HTTPException(
                status_code=404,
                detail=f"Test case not found: {request.test_case_name}"
            )
        
        params = request.model_dump(exclude_none=True, exclude={'test_case_name'})
        LOGGER_INFO(f"API route received request for test case: {request.test_case_name}")
        LOGGER_INFO(f"API route extracted params: {params}")
        
        # Execute the test case with all parameters via StartupInitializer
        result = run_test_case_function(
            test_case_name=request.test_case_name,
            **params  # platform, account, language, version, openai, jira, etc.
        )
        
        return DynamicTestCaseResponse(
            status=result["status"],
            message=result["message"],
            test_case_name=result["test_case_name"],
            platform=params.get('platform', 'windows'),
            navigate_report_path=result.get("navigate_report_path"),
            performance_report_path=result.get("performance_report_path"),
            stress_report_path=result.get("stress_report_path")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute test case: {str(e)}"
        )


@router.get("/dynamic/test_cases")
def list_all_test_cases():
    """
    List all available test cases from test_space/test_cases directory
    
    Returns a comprehensive list of all test cases that can be executed dynamically.
    Excludes the 'agent' directory by default.
    
    Returns:
        - total_count: Total number of test cases
        - categories: Count of test cases per category
        - test_cases: List of all test cases with name and path
            
    Example:
        GET /dynamic/test_cases
    """
    try:
        all_test_cases = test_case_discovery.get_all_test_cases()
        categories = test_case_discovery.list_test_cases_by_category()
        
        categories_count = {cat: len(cases) for cat, cases in categories.items()}
        
        return {
            "total_count": len(all_test_cases),
            "categories": categories_count,
            "test_cases": all_test_cases
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list test cases: {str(e)}"
        )


@router.get("/dynamic/test_cases/{test_case_name:path}")
def get_test_case_info(test_case_name: str):
    """
    Get detailed information about a specific test case
    
    Args:
        test_case_name: Test case path (e.g., 'jmt/basic/start_pmr_meeting')
        
    Returns:
        Test case metadata from YAML file
        
    Example:
        GET /dynamic/test_cases/jmt/basic/start_pmr_meeting
    """
    try:
        test_case_info = test_case_discovery.get_test_case_info(test_case_name)
        return test_case_info
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get test case info: {str(e)}"
        )


@router.post("/dynamic/search_test_cases")
def search_test_cases(keyword: str):
    """
    Search test cases by keyword
    
    Args:
        keyword: Search keyword (query parameter)
        
    Returns:
        Search results with matching test cases
        
    Example:
        POST /dynamic/search_test_cases?keyword=screen_sharing
    """
    try:
        results = test_case_discovery.search_test_cases(keyword)
        
        return {
            "keyword": keyword,
            "total_count": len(results),
            "test_cases": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search test cases: {str(e)}"
        )
