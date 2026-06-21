"""
Report ID Generator
Generates and manages report IDs across the entire application.
"""

import uuid
from typing import Optional
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG

class ReportIDGenerator:
    """
    Report ID Generator - Singleton pattern
    Generates and manages report IDs for the entire application.
    """
    _instance: Optional['ReportIDGenerator'] = None
    _global_report_id: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReportIDGenerator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize global report ID
        if ReportIDGenerator._global_report_id is None:
            ReportIDGenerator._global_report_id = str(uuid.uuid4())
            LOGGER_INFO(f"Generated new global report_id: {ReportIDGenerator._global_report_id}")
        
        self._initialized = True
    
    @classmethod
    def get_global_report_id(cls) -> str:
        """
        Get the current global report ID.
        
        Returns:
            str: Current global report ID
        """
        if cls._global_report_id is None:
            cls._global_report_id = str(uuid.uuid4())
            LOGGER_INFO(f"Generated new global report_id: {cls._global_report_id}")
        
        return cls._global_report_id
    
    @property
    def global_report_id(self) -> str:
        """
        Property to directly access the current global report ID.
        
        Returns:
            str: Current global report ID
        """
        return self.get_global_report_id()
    
    @global_report_id.setter
    def global_report_id(self, report_id: str) -> None:
        """
        Property setter to directly set the global report ID.
        
        Args:
            report_id (str): New report ID to set
        """
        self.set_global_report_id(report_id)
    
    @classmethod
    def set_global_report_id(cls, report_id: str) -> None:
        """
        Set the global report ID.
        
        Args:
            report_id (str): New report ID to set
        """
        cls._global_report_id = report_id
        LOGGER_DEBUG(f"Set global report_id: {report_id}")
    
    @classmethod
    def reset_global_report_session(cls) -> str:
        """
        Reset the global report session by generating a new report ID.
        
        Returns:
            str: New global report ID
        """
        cls._global_report_id = str(uuid.uuid4())
        LOGGER_DEBUG(f"Reset global report session, new report_id: {cls._global_report_id}")
        return cls._global_report_id
    
    @classmethod
    def generate_new_report_id(cls) -> str:
        """
        Generate a new UUID for report ID (without setting it as global).
        
        Returns:
            str: New UUID string
        """
        new_id = str(uuid.uuid4())
        LOGGER_DEBUG(f"Generated new report ID: {new_id}")
        return new_id

# Convenience functions for easy access
def get_current_report_id() -> str:
    """Get the current global report ID."""
    return ReportIDGenerator.get_global_report_id()

def reset_report_session() -> str:
    """Reset the global report session."""
    return ReportIDGenerator.reset_global_report_session()

def set_report_id(report_id: str) -> None:
    """Set the global report ID."""
    ReportIDGenerator.set_global_report_id(report_id)

def generate_report_id() -> str:
    """Generate a new report ID without setting it as global."""
    return ReportIDGenerator.generate_new_report_id()

# Global singleton instance for direct access
report_id_generator = ReportIDGenerator()
