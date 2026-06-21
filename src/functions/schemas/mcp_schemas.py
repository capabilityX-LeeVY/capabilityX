"""
MCP (Model Context Protocol) schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union


class MCPToolRequest(BaseModel):
    """Base MCP tool request"""
    name: str
    arguments: Dict[str, Any]


class MCPToolResponse(BaseModel):
    """Base MCP tool response"""
    name: str
    result: Union[str, Dict[str, Any], List[Any]]
    error: Optional[str] = None


class MCPServerInfo(BaseModel):
    """MCP server information"""
    name: str
    version: str
    description: str
    capabilities: List[str]


class MCPTool(BaseModel):
    """MCP tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: Optional[List[str]] = None


class AccessibilityToolRequest(MCPToolRequest):
    """Request for accessibility validation tool"""
    workflow: Optional[str] = None
    target_control: Optional[str] = None


class MeetingControlToolRequest(MCPToolRequest):
    """Request for meeting control tool"""
    action: str  # start, stop, mute, unmute, etc.
    target: Optional[str] = None


class NavigationToolRequest(MCPToolRequest):
    """Request for navigation tool"""
    ui_path: str
    control_metadata: Dict[str, Any]
