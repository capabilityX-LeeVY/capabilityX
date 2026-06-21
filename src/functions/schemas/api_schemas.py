"""
API request and response schemas
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None


class StartMeetingResponse(BaseModel):
    """Response for start meeting endpoint"""
    status: str

class EndMeetingResponse(BaseModel):
    """Response for end meeting endpoint"""
    status: str

class InvitePeopleResponse(BaseModel):
    """Response for invite people endpoint"""
    status: str

class StartCallingResponse(BaseModel):
    """Response for start meeting endpoint"""
    status: str

class WhoAreYouResponse(BaseModel):
    """Response for who are you endpoint"""
    status: str


class GreetUserRequest(BaseModel):
    """Request for greet user endpoint"""
    name: str


class GreetUserResponse(BaseModel):
    """Response for greet user endpoint"""
    greeting: str


class FunctionListResponse(BaseModel):
    """Response for function list endpoint"""
    functions: Dict[str, str]


class ValidationResponse(BaseModel):
    """Response for accessibility validation"""
    response: str
    total_controls: Optional[int] = None
    success_count: Optional[int] = None
    fail_count: Optional[int] = None
    report_url: Optional[str] = None


class RunTestSuiteRequest(BaseModel):
    """Request for run test suite endpoint"""
    test_suite_name: str  # Test suite name, e.g., "web_video_vbg", "smoke"
    platform: Optional[str] = "windows"


class RunTestSuiteResponse(BaseModel):
    """Response for run test suite endpoint"""
    status: str
    message: str
    test_suite_name: str
    platform: str
    navigate_report_path: Optional[str] = None
    performance_report_path: Optional[str] = None
    stress_report_path: Optional[str] = None


class RunTestCaseRequest(BaseModel):
    """Request for run test case endpoint"""
    test_case_name: str
    platform: Optional[str] = "windows"


class RunTestCaseResponse(BaseModel):
    """Response for run test case endpoint"""
    status: str
    message: str
    test_case_name: str
    navigate_report_path: Optional[str] = None
    performance_report_path: Optional[str] = None
    stress_report_path: Optional[str] = None


class StressTestRequest(BaseModel):
    """Request for stress test endpoint"""
    test_case_name: str = "test_stress"
    platform: str = "windows"
    stress_duration: int = 180  # Stress test duration (seconds), default 3 minutes
    participant_count: int = 20  # Number of participants
    custom_message: Optional[str] = None  # Custom stress message
    enable_chat_test: bool = False  # Whether to enable chat testing, default off
    enable_video: bool = True  # Whether to enable video
    enable_audio: bool = False  # Whether to enable audio


class StressTestResponse(BaseModel):
    """Response for stress test endpoint"""
    status: str
    message: str
    test_case_name: str
    execution_id: str  # Execution tracking ID
    start_time: str
    estimated_duration: int
    stress_config: Dict[str, Any]  # Stress test configuration
    result_url: Optional[str] = None  # URL of uploaded results
    navigate_report_path: Optional[str] = None
    performance_report_path: Optional[str] = None
    stress_report_path: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None
