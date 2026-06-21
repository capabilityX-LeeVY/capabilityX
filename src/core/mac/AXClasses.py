"""
AXClasses.py Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
from .AXClasses import CRSCircleCheck
from .AXClasses import NativeUIElement
from .AXClasses import CElementKeyInfoItem

# Re-export for backward compatibility
__all__ = ['CRSCircleCheck', 'NativeUIElement', 'CElementKeyInfoItem']
