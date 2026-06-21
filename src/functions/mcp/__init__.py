"""
MCP (Model Context Protocol) module for RegressShield

This module provides the MCP server functionality for running test suites and test cases.
"""

from .server import (
    mcp,
    run_test_suite,
    run_test_case,
    list_test_suites
)

__all__ = [
    'mcp',
    'run_test_suite', 
    'run_test_case',
    'list_test_suites'
]
