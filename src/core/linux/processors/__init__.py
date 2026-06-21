"""
Linux Processors Package

This package contains specialized processor classes for Linux UI automation:
- ControlLocatorProcessor: Handles control location with retry strategies
"""

from core.linux.processors.control_locator_processor import ControlLocatorProcessor

__all__ = [
    'ControlLocatorProcessor',
]
