"""
Common handlers for global application state management.
"""

from .report_id_generator import (
    ReportIDGenerator,
    get_current_report_id,
    reset_report_session,
    set_report_id,
    generate_report_id,
    report_id_generator
)

__all__ = [
    'ReportIDGenerator',
    'get_current_report_id',
    'reset_report_session', 
    'set_report_id',
    'generate_report_id',
    'report_id_generator'
]
