"""
Processors Module - Specialized processors for separation of concerns

This module contains all processor classes that handle different aspects
of the control automation workflow.
"""

from core.windows.processors.control_metadata_processor import ControlMetadataProcessor
from core.windows.processors.control_locator_processor import ControlLocatorProcessor
from core.windows.processors.control_action_processor import ControlActionProcessor
from core.windows.processors.control_verification_processor import ControlVerificationProcessor
from core.windows.processors.report_processor import ReportProcessor

__all__ = [
    'ControlMetadataProcessor',
    'ControlLocatorProcessor',
    'ControlActionProcessor', 
    'ControlVerificationProcessor',
    'ReportProcessor'
]
