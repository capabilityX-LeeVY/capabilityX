"""
API schemas for dynamic test case execution
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DynamicTestCaseRequest(BaseModel):
    """Request model for dynamic test case execution with support for arbitrary parameters"""
    model_config = {"extra": "allow"}  # Allow any additional fields
    
    test_case_name: str = Field(
        ..., 
        description="Test case name in path format (e.g., 'jmt/basic/start_pmr_meeting')",
        examples=["jmt/basic/start_pmr_meeting"]
    )
    platform: Optional[str] = Field(
        default="windows",
        description="Platform to run on (windows, mac, web)"
    )


class DynamicTestCaseResponse(BaseModel):
    """Response model for dynamic test case execution"""
    status: str
    message: str
    test_case_name: str
    platform: str
    navigate_report_path: Optional[str] = None
    performance_report_path: Optional[str] = None
    stress_report_path: Optional[str] = None


class TestCaseListResponse(BaseModel):
    """Response model for listing all available test cases"""
    total_count: int
    categories: Dict[str, int]
    test_cases: List[Dict[str, str]]


class TestCaseInfoResponse(BaseModel):
    """Response model for test case information"""
    name: str
    path: str
    owner: Optional[str] = None
    account: Optional[str] = None
    description: Optional[str] = None
    expect_result: Optional[str] = None
    pre_conditions: Optional[List[str]] = None
    steps_count: Optional[int] = None
    error: Optional[str] = None


class TestCaseSearchRequest(BaseModel):
    """Request model for searching test cases"""
    keyword: str = Field(..., description="Search keyword")


class TestCaseSearchResponse(BaseModel):
    """Response model for test case search results"""
    keyword: str
    total_count: int
    test_cases: List[Dict[str, str]]
