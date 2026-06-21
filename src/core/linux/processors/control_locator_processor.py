"""
Linux Control Locator Processor

Handles control location using keyboard navigation (Navigator) ONLY.
Matches Windows strategy: pure keyboard-based navigation for test execution.

Architecture (matching Windows):
- Primary & Only: ControlNavigator for keyboard-based navigation
- No Fallback: ControlExplorer is for data collection only, NOT test execution
- Retry Strategy: 3 attempts with 1 second delay
"""

import time
from typing import Tuple, Optional
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR


class ControlLocatorProcessor:
    """
    Linux control locator processor - Navigator ONLY strategy (matching Windows)
    
    Uses pure keyboard navigation for test execution.
    Explorer is available for data collection but NOT used during tests.
    """
    
    def __init__(self, control_navigator, control_explorer):
        """
        Initialize the control locator processor
        
        Args:
            control_navigator: ControlNavigator instance for keyboard navigation (PRIMARY)
            control_explorer: ControlExplorer instance for data collection only (NOT used in tests)
        """
        self.control_navigator = control_navigator
        self.control_explorer = control_explorer  # Available but not used in locate flow
        self.max_retry_attempts = 3
        self.retry_delay = 1
        
        # Store control name sequence for potential future intelligent retry
        self.control_name_sequence = []
        self.current_step_index = 0
        
        # Global retry enable/disable flag
        self.enable_retry = True
        
        # Record traversal flag
        self.record_traversal = False
        
        # Retry strategy configuration (simplified, matching Windows philosophy)
        self.retry_strategies_enabled = {
            "keyboard_navigation": True,  # ONLY strategy for test execution
        }
        
        LOGGER_INFO("[Linux][LocatorProcessor] Initialized with Navigator-ONLY strategy (matching Windows)", "GREEN")
        
        LOGGER_INFO("[Linux][ControlLocatorProcessor] Initialized", "GREEN")
    
    def set_control_name_sequence(self, control_names_list):
        """Set the control name sequence for potential future intelligent retry"""
        self.control_name_sequence = control_names_list
        self.current_step_index = 0
        LOGGER_DEBUG(f"[Linux][Locate][sequence] Set control name sequence: {control_names_list}", "CYAN")
    
    def set_enable_retry(self, enable: bool):
        """
        Enable or disable retry mechanism for control location
        
        Args:
            enable: True to enable retry, False to disable
        """
        self.enable_retry = enable
        mode = "ENABLED" if enable else "DISABLED"
        LOGGER_INFO(f"[Linux][Locate][retry][config] Retry mechanism {mode}", "CYAN")
    
    def set_record_traversal(self, record: bool):
        """
        Enable or disable recording of all controls during traversal
        
        Args:
            record: True to record controls, False to skip recording
        """
        self.record_traversal = record
        mode = "ENABLED" if record else "DISABLED"
        LOGGER_INFO(f"[Linux][Locate][record][config] Control traversal recording {mode}", "CYAN")
    
    def set_current_step_index(self, index: int):
        """Set the current step index in the control sequence"""
        self.current_step_index = index
        LOGGER_DEBUG(f"[Linux][Locate][sequence] Current step index: {index}", "CYAN")
    
    def locate_control_handler_for_operator(self, control_meta, close_flag=False, 
                                           locate_id_flag=True, is_optional=False):
        """
        Core control location logic with retry mechanism
        
        Args:
            control_meta: Dictionary containing control metadata (name, id, test_case_step_description)
            close_flag: Whether to close control after locating (unused in Linux)
            locate_id_flag: Whether to locate by ID (unused in Linux, we use name)
            is_optional: Whether this is an optional step
            
        Returns:
            tuple: (control_visited, result) where:
                - control_visited: Control metadata or None
                - result: True if control found, False otherwise
        """
        target_control_name = control_meta.get('name', 'Unknown')
        LOGGER_DEBUG(f"[Linux][Locate][navigate]: [{target_control_name}]", "YELLOW")
        LOGGER_INFO(f"[Linux][Locate][control_meta]: {control_meta}", "CYAN")
        
        # Determine max attempts based on optional flag and retry setting
        if is_optional or not self.enable_retry:
            max_attempts = 1
            if is_optional:
                LOGGER_DEBUG(f"[Linux][Locate][navigate][optional]: Step is optional, limiting to single attempt", "CYAN")
            if not self.enable_retry:
                LOGGER_INFO(f"[Linux][Locate][navigate][no_retry]: Retry disabled, using single attempt", "YELLOW")
        else:
            max_attempts = self.max_retry_attempts
        
        # Attempt to locate control with retries - NAVIGATOR ONLY (matching Windows)
        for attempt in range(max_attempts):
            if attempt > 0:
                LOGGER_DEBUG(f"[Linux][Locate][navigate][retry attempt {attempt + 1}/{max_attempts}]", "YELLOW")
                time.sleep(self.retry_delay)
            
            try:
                # Use ONLY ControlNavigator (keyboard-based navigation) - matching Windows strategy
                LOGGER_DEBUG(f"[Linux][Locate] Using keyboard navigation for: {target_control_name}", "CYAN")
                
                _, _, nav_success, nav_metadata = self.control_navigator.control_navigator(
                    is_located=True,
                    locate_control_meta=control_meta
                )
                
                if nav_success:
                    LOGGER_INFO(f"[Linux][Locate] ✅ Control found via keyboard navigation: {target_control_name}", "GREEN")
                    return nav_metadata[0] if nav_metadata else None, True
                
                LOGGER_DEBUG(f"[Linux][Locate] ⚠️ Control not found (attempt {attempt + 1}): {target_control_name}", "YELLOW")
                
                # If we have more attempts, continue
                if attempt < max_attempts - 1:
                    continue
                    
            except Exception as e:
                LOGGER_ERROR(f"[Linux][Locate] Error locating control (attempt {attempt + 1}): {str(e)}")
                
                # If we have more attempts, continue
                if attempt < max_attempts - 1:
                    continue
        
        # All attempts failed
        LOGGER_WARNING(f"[Linux][Locate] ❌ Control not found after {max_attempts} attempts: {target_control_name}", "RED")
        return None, False
    
    def locate_control(self, locate_target, locate_id_flag=True, current_control=None):
        """
        Locate control - simplified version for compatibility
        
        Args:
            locate_target: Target control information
            locate_id_flag: Whether to locate by ID
            current_control: Current control context (unused in Linux)
            
        Returns:
            LocateResult-like dict with success status
        """
        # Extract control name from locate_target
        if isinstance(locate_target, dict):
            control_name = locate_target.get('name', 'Unknown')
        else:
            control_name = str(locate_target)
        
        LOGGER_DEBUG(f"[Linux][Locate] Locating control: {control_name}", "CYAN")
        
        # Use the main locate handler
        control_meta = {'name': control_name}
        control_visited, result = self.locate_control_handler_for_operator(control_meta, locate_id_flag=locate_id_flag)
        
        # Return result in expected format
        return {
            'success': result,
            'control': control_visited,
            'platform': 'linux'
        }
    
    def configure_retry_strategies(self, strategy_config: dict):
        """
        Configure retry strategies
        
        Args:
            strategy_config: Dictionary of strategy names to enabled status
        """
        for strategy_name, enabled in strategy_config.items():
            if strategy_name in self.retry_strategies_enabled:
                self.retry_strategies_enabled[strategy_name] = enabled
                status = "ENABLED" if enabled else "DISABLED"
                LOGGER_INFO(f"[Linux][Locate][retry][{strategy_name}] {status}", "CYAN")
    
    def get_retry_config(self):
        """
        Get current retry configuration
        
        Returns:
            dict: Retry configuration details
        """
        return {
            "max_attempts": self.max_retry_attempts,
            "retry_delay": self.retry_delay,
            "enabled_strategies": {k: v for k, v in self.retry_strategies_enabled.items() if v},
            "disabled_strategies": {k: v for k, v in self.retry_strategies_enabled.items() if not v}
        }
