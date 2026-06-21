"""
RSDeepTraversal.py Import Wrapper (WRS Compiled Version)

This file imports the compiled Cython version.
Generated automatically by WRS compilation script.
Build Environment: Isolated from source code development environment.
"""

# Import the compiled Cython module
from .RSDeepTraversal import CRSDeepTraversal

# Re-export for backward compatibility
__all__ = ['CRSDeepTraversal']
