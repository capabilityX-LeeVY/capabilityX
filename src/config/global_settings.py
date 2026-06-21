"""
Global Settings Accessor
Provides global access to application settings using DynamicConfig.
Enhanced with explicit initialization control for better robustness.
"""

from typing import Optional
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH
from common.utils.deviceInfo import getHostName, getIP, getOSInfo
from common.utils.logger import LOGGER_WARNING, LOGGER_INFO, LOGGER_DEBUG


class GlobalSettings:
    """
    Global Settings Accessor - Singleton with explicit initialization
    Provides easy access to application settings with better error handling.
    """
    _instance: Optional['GlobalSettings'] = None
    _config: Optional[DynamicConfig] = None
    _initialization_source: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalSettings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # Don't initialize DynamicConfig here - do it lazily in get() method
        self._initialized = True
    
    def set(self, key: str, value):
        """Set a setting value by key."""
        if GlobalSettings._config is None:
            # Auto-initialize if not done yet
            GlobalSettings._config = DynamicConfig(SETTINGS_PATH)
            GlobalSettings._initialization_source = "auto_set"
        return GlobalSettings._config.set(key, value)
    
    def get(self, key: str, default=None):
        """Get a setting value by key."""
        if GlobalSettings._config is None:
            # Auto-initialize if not done yet, but warn about it
            GlobalSettings._config = DynamicConfig(SETTINGS_PATH)
            LOGGER_INFO(f"[Initialized][GlobalSettings][SETTINGS: {GlobalSettings._config.get(key, default=default)}].")
            GlobalSettings._initialization_source = "auto-initialization"
        return GlobalSettings._config.get(key, default=default)
    
    def reload(self):
        """Reload settings from file."""
        if GlobalSettings._config:
            GlobalSettings._config.loadConfig()
        else:
            # Initialize if not done yet
            GlobalSettings._config = DynamicConfig(SETTINGS_PATH)
            if GlobalSettings._initialization_source is None:
                GlobalSettings._initialization_source = "auto-reload"
    
    
    @property
    def initialization_info(self) -> str:
        """Get information about how settings were initialized"""
        if GlobalSettings._initialization_source:
            return f"Initialized by: {GlobalSettings._initialization_source}"
        else:
            return "Not initialized yet"

    # Property accessors for common settings
    @property
    def environment(self) -> str:
        """Get environment setting."""
        return str(self.get('environment', 'BTS'))
    
    @property
    def test_suite(self) -> str:
        """Get test_suite setting."""
        return str(self.get('test_suite', 'default_suite'))
    
    @property
    def test_case(self) -> str:
        """Get test_case setting."""
        return str(self.get('test_case', ''))
    
    @property
    def test_batch(self) -> str:
        """Get test_batch setting."""
        return str(self.get('test_batch', ''))
    
    @property
    def mode(self) -> str:
        """Get mode setting."""
        return str(self.get('mode', 'suite'))
    
    @property
    def openai(self) -> bool:
        """Get openai setting."""
        return bool(self.get('openai', False))
    
    @property
    def recording(self) -> bool:
        """Get recording setting."""
        return bool(self.get('recording', False))
    
    @property
    def language(self) -> str:
        """Get language setting."""
        return str(self.get('language', 'en_US'))
    
    @property
    def appVersion(self) -> str:
        """Get appVersion setting."""
        return str(self.get('appVersion', 'Unknown'))
    
    @property
    def jira(self) -> bool:
        """Get jira setting."""
        return bool(self.get('jira', False))
    
    @property
    def continueRun(self) -> bool:
        """Get continueRun setting."""
        return bool(self.get('continueRun', False))
    
    @property
    def workflow(self) -> str:
        """Get workflow setting."""
        return str(self.get('workflow', ''))
    
    @property
    def fileName(self) -> str:
        """Get fileName setting."""
        return str(self.get('fileName', ''))
    
    @property
    def osInfo(self) -> str:
        """Get osInfo setting."""
        return str(self.get('osInfo', ''))
    
    @property
    def screenReaderFileName(self) -> str:
        """Get screenReaderFileName setting."""
        return str(self.get('screenReaderFileName', 'WCAG_Screen_Reader_overall_report.md'))
    
    @property
    def fileNBugs(self) -> int:
        """Get fileNBugs setting."""
        result = self.get('fileNBugs', 5)
        return int(result) if result is not None else 5
    
    @property
    def installOptions(self) -> dict:
        """Get installOptions setting."""
        result = self.get('installOptions', {})
        return result if isinstance(result, dict) else {}
    
    @property
    def account(self) -> str:
        """Get account setting."""
        return str(self.get('account', ''))

    @property
    def botRoomId(self) -> str:
        """Get botRoomId setting."""
        return str(self.get('botRoomId', ''))

    @property
    def onNewVersion(self) -> bool:
        """Whether to trigger the job upon new app version detection."""
        return bool(self.get('onNewVersion', False))
    
    @property
    def device_name(self) -> str:
        """Get device_name setting."""
        return str(self.get('device_name', getHostName()))
    
    @property
    def device_ip(self) -> str:
        """Get device_ip setting."""
        return str(self.get('device_ip', getIP()))
    
    @property
    def device_os(self) -> str:
        """Get device_os setting."""
        return str(self.get('device_os', getOSInfo()))


# ============================================================================
# Observation Feature Configuration
# ============================================================================

# Global switches for AI observation feature
ENABLE_OBSERVATION_MODE = True  # Master switch - set to True to enable observation globally
OBSERVATION_TIMEOUT = 5.0  # Maximum time (seconds) to wait for GPT Vision analysis
OBSERVATION_FALLBACK = True  # If True, fallback to standard logic when observation fails
OBSERVATION_CONFIDENCE_THRESHOLD = 80  # Minimum confidence percentage to trust observation result

# Observation debug settings
OBSERVATION_DEBUG = False  # Enable verbose logging for observation process
OBSERVATION_SAVE_SCREENSHOTS = True  # Save screenshots used for observation analysis


# Lazy global instance creation
_settings_instance = None

def get_settings():
    """Get the global settings instance (creates it if needed)"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = GlobalSettings()
    return _settings_instance

# For backward compatibility, create a property-like access
class SettingsProxy:
    """Proxy class to provide property-like access to settings"""
    def __getattr__(self, name):
        return getattr(get_settings(), name)
    
    def reload(self):
        return get_settings().reload()
    
    def get(self, key, default=None):
        return get_settings().get(key, default)
    
    def set(self, key, value):
        return get_settings().set(key, value)
    
    @property
    def initialization_info(self):
        return get_settings().initialization_info

settings = SettingsProxy()
