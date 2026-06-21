"""
API Configuration Manager

Centralized management for API configurations and templates.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG
from config.paths import API_CONFIG_PATH


class ApiConfigManager:
    """Manages API configurations and provides utilities for API calls"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Use centralized path configuration
            config_path = str(API_CONFIG_PATH)
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load API configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
                LOGGER_DEBUG(f"Loaded API config with {len(config)} entries")
                return config
        except FileNotFoundError:
            LOGGER_ERROR(f"API config file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"Invalid JSON in API config: {e}")
            return {}
        except Exception as e:
            LOGGER_ERROR(f"Failed to load API config: {e}")
            return {}
    
    def get_api_config(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific API"""
        return self._config.get(api_name)
    
    def list_available_apis(self) -> list:
        """Get list of available API names"""
        return list(self._config.keys())
    
    def add_api_config(self, api_name: str, config: Dict[str, Any]) -> bool:
        """Add new API configuration"""
        try:
            self._config[api_name] = config
            self._save_config()
            LOGGER_INFO(f"Added API configuration: {api_name}")
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to add API config: {e}")
            return False
    
    def update_api_config(self, api_name: str, config: Dict[str, Any]) -> bool:
        """Update existing API configuration"""
        if api_name not in self._config:
            LOGGER_ERROR(f"API config not found: {api_name}")
            return False
        
        try:
            self._config[api_name].update(config)
            self._save_config()
            LOGGER_INFO(f"Updated API configuration: {api_name}")
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to update API config: {e}")
            return False
    
    def remove_api_config(self, api_name: str) -> bool:
        """Remove API configuration"""
        if api_name not in self._config:
            LOGGER_ERROR(f"API config not found: {api_name}")
            return False
        
        try:
            del self._config[api_name]
            self._save_config()
            LOGGER_INFO(f"Removed API configuration: {api_name}")
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to remove API config: {e}")
            return False
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            LOGGER_ERROR(f"Failed to save API config: {e}")
            raise
    
    def validate_config(self) -> Dict[str, list]:
        """Validate all API configurations"""
        issues = {"errors": [], "warnings": []}
        
        for api_name, config in self._config.items():
            # Check required fields
            if not config.get("url"):
                issues["errors"].append(f"{api_name}: Missing required 'url' field")
            
            if not config.get("method"):
                issues["warnings"].append(f"{api_name}: Missing 'method' field, will default to GET")
            
            # Check method validity
            method = config.get("method", "GET").upper()
            valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            if method not in valid_methods:
                issues["errors"].append(f"{api_name}: Invalid method '{method}'")
        
        return issues


# Global instance
api_config_manager = ApiConfigManager()
