#!/usr/bin/env python3
"""
Common Settings Loader

For loading and merging common configuration settings for test cases
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from config.paths import TEST_CASE_COMMON_SETTINGS_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR


class CommonSettingsLoader:
    """Common configuration loader"""
    
    def __init__(self):
        # Define common configuration file path - using test_space/common directory
        current_path = Path(__file__).parent
        # From src/rs_sdk/utils up to src, then to test_space/common
        src_path = current_path.parent.parent  # to src directory
        self.common_settings_path = TEST_CASE_COMMON_SETTINGS_PATH
        self._common_settings = None
        
    def load_common_settings(self) -> Dict[str, Any]:
        """Load common configuration settings"""
        if self._common_settings is not None:
            return self._common_settings
            
        try:
            if self.common_settings_path.exists():
                with open(self.common_settings_path, "r", encoding="utf-8") as f:
                    self._common_settings = yaml.safe_load(f) or {}
                    LOGGER_DEBUG(f"Loaded common settings from: {self.common_settings_path}")
            else:
                LOGGER_WARNING(f"Common settings file not found: {self.common_settings_path}")
                self._common_settings = {}
                
        except Exception as e:
            LOGGER_ERROR(f"Error loading common settings: {e}")
            self._common_settings = {}
            
        return self._common_settings
    
    def merge_test_case_config(self, test_case_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge test case configuration with common configuration
        Test case configuration takes priority over common configuration
        """
        common_settings = self.load_common_settings()
        merged_config = test_case_config.copy()
        
        # Merge UI response settings
        if "ui_response_settings" not in merged_config and "ui_response_settings" in common_settings:
            merged_config["ui_response_settings"] = common_settings["ui_response_settings"].copy()
            LOGGER_DEBUG("Applied common ui_response_settings")
        elif "ui_response_settings" in merged_config and "ui_response_settings" in common_settings:
            # Merge settings, test case configuration takes priority
            common_ui_settings = common_settings["ui_response_settings"].copy()
            common_ui_settings.update(merged_config["ui_response_settings"])
            merged_config["ui_response_settings"] = common_ui_settings
            LOGGER_DEBUG("Merged ui_response_settings with test case overrides")
        
        # Merge performance settings
        if "performance_settings" not in merged_config and "performance_settings" in common_settings:
            merged_config["performance_settings"] = common_settings["performance_settings"].copy()
            LOGGER_DEBUG("Applied common performance_settings")
        elif "performance_settings" in merged_config and "performance_settings" in common_settings:
            # Merge settings, test case configuration takes priority
            common_perf_settings = common_settings["performance_settings"].copy()
            common_perf_settings.update(merged_config["performance_settings"])
            merged_config["performance_settings"] = common_perf_settings
            LOGGER_DEBUG("Merged performance_settings with test case overrides")
            
        # Merge check point configuration
        if "check_point" not in merged_config and "default_check_points" in common_settings:
            merged_config["check_point"] = common_settings["default_check_points"].copy()
            LOGGER_DEBUG("Applied common check_point settings")
            
        return merged_config
    
    def get_performance_thresholds(self, test_case_config: Dict[str, Any], step_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get performance threshold configuration
        Priority: Step level > Test case level > Common configuration level
        """
        performance_thresholds = {}
        
        # 1. First get default values from common configuration
        common_settings = self.load_common_settings()
        if "performance_settings" in common_settings:
            default_settings = common_settings["performance_settings"]
            if "default_cpu_threshold" in default_settings:
                performance_thresholds["cpu_threshold"] = default_settings["default_cpu_threshold"]
            if "default_mem_threshold_mb" in default_settings:
                performance_thresholds["mem_threshold_mb"] = default_settings["default_mem_threshold_mb"]
            if "default_gpu_threshold" in default_settings:
                performance_thresholds["gpu_threshold"] = default_settings["default_gpu_threshold"]
        
        # 2. Then override from test case level
        if "performance_settings" in test_case_config:
            test_case_settings = test_case_config["performance_settings"]
            if "default_cpu_threshold" in test_case_settings:
                performance_thresholds["cpu_threshold"] = test_case_settings["default_cpu_threshold"]
            if "default_mem_threshold_mb" in test_case_settings:
                performance_thresholds["mem_threshold_mb"] = test_case_settings["default_mem_threshold_mb"]
            if "default_gpu_threshold" in test_case_settings:
                performance_thresholds["gpu_threshold"] = test_case_settings["default_gpu_threshold"]
        
        # 3. Finally override from step level
        if step_config:
            if "performance_cpu_threshold" in step_config:
                performance_thresholds["cpu_threshold"] = step_config["performance_cpu_threshold"]
            if "performance_mem_threshold_mb" in step_config:
                performance_thresholds["mem_threshold_mb"] = step_config["performance_mem_threshold_mb"]
            if "performance_gpu_threshold" in step_config:
                performance_thresholds["gpu_threshold"] = step_config["performance_gpu_threshold"]
        
        return performance_thresholds if performance_thresholds else None
    
    def get_ui_response_threshold(self, test_case_config: Dict[str, Any], step_config: Optional[Dict[str, Any]] = None) -> int:
        """
        Get UI response threshold configuration
        Priority: Step level > Test case level > Common configuration level
        """
        # 1. Check step level configuration
        if step_config and "ui_response_threshold_ms" in step_config:
            return step_config["ui_response_threshold_ms"]
        
        # 2. Check test case level configuration
        if "ui_response_settings" in test_case_config:
            ui_settings = test_case_config["ui_response_settings"]
            if "default_threshold_ms" in ui_settings:
                return ui_settings["default_threshold_ms"]
        
        # 3. Check common configuration level
        common_settings = self.load_common_settings()
        if "ui_response_settings" in common_settings:
            ui_settings = common_settings["ui_response_settings"]
            if "default_threshold_ms" in ui_settings:
                return ui_settings["default_threshold_ms"]
        
        # 4. Return system default value
        return 3000
    
    def get_performance_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get predefined performance configuration profile"""
        common_settings = self.load_common_settings()
        if "performance_profiles" in common_settings:
            return common_settings["performance_profiles"].get(profile_name)
        return None
    
    def get_ui_response_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get predefined UI response configuration profile"""
        common_settings = self.load_common_settings()
        if "ui_response_profiles" in common_settings:
            return common_settings["ui_response_profiles"].get(profile_name)
        return None


# Create global instance
common_settings_loader = CommonSettingsLoader()
