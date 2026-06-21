"""
test_job_orchestrator.py

Orchestrates the complete test job workflow including test execution, 
screen reader analysis, performance analysis, and result upload.
"""

import os
import sys

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from common.startup.startup_initializer import StartupInitializer
from common.utils.featureToggle import FeatureToggle
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_WARNING, LOGGER_INFO, LOGGER_DEBUG
from common.finalizer import archive_processor, notifier
from config.paths import (
    FEATURE_TOGGLE_CONFIG_PATH,
    REMOTE_STORAGE_CONFIG_PATH
)



class TestUploadReport:
    
    def __init__(self):
        # Initialize the system FIRST before accessing any settings
        StartupInitializer()
        FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
        
        # Import settings AFTER initialization is complete
        from config.global_settings import settings
        self.settings = settings
        self.remote_storage = DynamicConfig(REMOTE_STORAGE_CONFIG_PATH)

    
    
    def upload_results(self):
        """Upload test results if enabled"""
        if not FeatureToggle.isEnabled('upload_output'):
            LOGGER_INFO("Result upload skipped (disabled)", "YELLOW")
            return None
        
        LOGGER_INFO("Uploading test results...", "CYAN")
        try:
            from pathlib import Path
            directory = Path(r"C:\devagent\deepNavigation\WebexRegressSheild\src\tests\models\sample\Settings-Ready")
            output_url = archive_processor.RemoteArchiveProcessor().upload_archive(local_folder=directory)
            LOGGER_INFO(f"Result upload completed successfully! {output_url}", "GREEN")
            return output_url
        except Exception as e:
            LOGGER_WARNING(f"Result upload failed: {str(e)}", "YELLOW")
            return None

   
if __name__ == "__main__":
    TestUploadReport().upload_results()
