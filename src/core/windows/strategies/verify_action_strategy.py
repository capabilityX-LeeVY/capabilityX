"""
Verify Action Strategy

This module contains the VerifyActionStrategy for verifying control values.
"""

from typing import Dict, Any
from core.windows.strategies.action_strategy import ActionStrategy
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG


class VerifyActionStrategy(ActionStrategy):
    """Verify action strategy for checking control values"""
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        """
        Execute value verification action using ControlVerificationProcessor
        
        Args:
            ctrl_action: Action configuration containing expected value
            execution_context: Execution context with verification_processor
            dependencies: Additional dependencies
            
        Returns:
            Verification result status string
        """
        expected_value = ctrl_action.get("value", "")
        
        # Get verification processor from execution context
        verification_processor = getattr(execution_context, 'verification_processor', None)
        if not verification_processor:
            LOGGER_ERROR("[operator][Locate][action][verify] No verification_processor available in execution context", "RED")
            return "❌Failed (No Processor)"
        
        # Use verify_control_value method from ControlVerificationProcessor
        result = verification_processor.verify_control_value(expected_value)
        
        # Format result for display: convert status to simplified format
        status = result['status']
        if 'Success' in status:
            display_result = "✅Success"
        elif 'Failed' in status:
            display_result = "❌Failed"
        else:
            display_result = status
        
        LOGGER_INFO(f"[operator][Locate][action][verify] Verification result: {display_result}", "CYAN")
        
        return display_result
    
    def get_action_type(self) -> str:
        return "verify"
