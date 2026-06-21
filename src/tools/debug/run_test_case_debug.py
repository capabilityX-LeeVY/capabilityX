"""
run_test_case_debug.py

Simple Debug Test Case Runner
=============================

This file executes a single test case for debugging purposes with minimal setup:
- Only one parameter: --case (optional, defaults to stress/test_stress)
- No suite mode
- No Webex upgrade
- No report upload
- Local reports only

Usage:
    python src/run_test_case_debug.py --case meetings/video/vbg_none_in_meeting
    python src/run_test_case_debug.py  # Uses default: stress/test_stress
"""

import pythoncom
import argparse
import sys
import os

# Modify sys.argv before any imports to prevent conflicts
def setup_args(case_name):
    """Setup arguments for the system to use"""
    sys.argv = [
        'run_test_case_debug.py',
        '--test_suite', case_name,
        '--mode', 'case', 
        '--keepApp'  # Always keep app to prevent installation
    ]

def parse_debug_args():
    """Parse our simple debug arguments"""
    parser = argparse.ArgumentParser(
        description='Simple Debug Test Case Runner',
        add_help=False  # Disable help to avoid conflicts
    )
    parser.add_argument('--case', '-c', 
                       #default='stress/test_stress_debug',
                       default='stress/test_stress',
                       #default='meetings/audio_setting/test_audio_control_complete_workflow',
                       #default='meetings/video_setting/test_video_control_complete_workflow',
                       #default='meetings/video_setting/test_in_meeting_video_settings',
                       #default='meetings/video_setting/test_pre_meeting_video_settings',
                       #default='meetings/layout/test_layout_comprehensive',
                       #default='meetings/chat/test_chat_in_pmr_meeting',
                       #default='meetings/chat/test_chat_in_webex_meeting',
                       #default='meetings/chat/test_chat_with_popout_and_popin',
                       #default='meetings/chat/test_chat_and_layout_workflow',
                       #default='performance/test_share_only',
                       help='Test case to run (default: stress/test_stress_debug)')
    
    # Parse only our arguments, ignore the rest
    known_args, _ = parser.parse_known_args()
    return known_args

# Parse arguments first, before any system imports
if __name__ == "__main__":
    debug_args = parse_debug_args()
    setup_args(debug_args.case)

# Now import system modules
# Add parent directories to path for imports
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent  # Go up to src/
sys.path.insert(0, str(src_path))

from core.test_case_runner import TestCaseRunner
from common.startup.startup_initializer import StartupInitializer
from common.utils.featureToggle import FeatureToggle
from config.global_settings import settings
from common.utils.logger import LOGGER_INFO
from config.paths import FEATURE_TOGGLE_CONFIG_PATH


class SimpleDebugRunner:
    """
    Ultra-simple test case runner for debugging
    """
    
    def __init__(self):
        """Initialize with minimal setup, skipping database cleanup"""
        # Minimal startup initialization without database cleanup
        self._minimal_startup_init()
        FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
        settings.reload()
        
        # Get case name first
        self.case_name = settings.test_suite
        
        # Force debug settings
        self._apply_debug_settings()
        
        # Create runner
        self.test_runner = TestCaseRunner()
    
    def _minimal_startup_init(self):
        """Minimal startup initialization without database cleanup"""
        LOGGER_INFO("🚀 Starting minimal debug initialization (skipping database cleanup)", "CYAN")
        
        # Initialize settings only (skip database cleanup)
        from common.startup.startup_initializer import StartupInitializer
        startup = StartupInitializer.__new__(StartupInitializer)  # Create without calling __init__
        startup.settings_init()  # Only initialize settings
        
        # Initialize output folders only
        from common.startup.output_initializer import OutputInitializer
        output_initializer = OutputInitializer()
        output_initializer.setup()
        
        LOGGER_INFO("✅ Minimal initialization complete - database cleanup skipped", "GREEN")
    
    def _apply_debug_settings(self):
        """Apply debug-friendly settings"""
        # Disable features not needed for debugging
        FeatureToggle.features['installer'] = False      # No Webex install
        FeatureToggle.features['upload_output'] = False  # No upload
        
        # Set basic settings
        settings.set('openai', False)  # Disable AI by default
        settings.set('jira', False)    # Disable JIRA
        
        LOGGER_INFO(f"  DEBUG MODE: Running test case '{self.case_name}'", "CYAN")
        LOGGER_INFO("   ✅ Webex installation: DISABLED", "GREEN")
        LOGGER_INFO("   ✅ Report upload: DISABLED", "GREEN")
        LOGGER_INFO("   ✅ Reports saved locally only", "GREEN")
    
    def run(self):
        """Run the test case"""
        try:
            LOGGER_INFO("=" * 50, "BLUE")
            LOGGER_INFO("🚀 Starting Debug Test Execution", "BLUE")
            LOGGER_INFO("=" * 50, "BLUE")
            
            # Execute test case
            result = self.test_runner.run_test_suite(
                self.case_name, mode="case"
            )
            
            # Handle different return formats
            if isinstance(result, tuple) and len(result) == 3:
                nav_report, perf_report, stress_report = result
            elif isinstance(result, tuple) and len(result) == 2:
                nav_report, perf_report = result
                stress_report = None
            else:
                nav_report = perf_report = stress_report = None
            
            if nav_report:
                LOGGER_INFO("=" * 50, "BLUE")
                LOGGER_INFO("✅ Debug Test Completed Successfully!", "GREEN")
                LOGGER_INFO(f"📝 Navigation Report: {nav_report}", "GREEN")
                if perf_report:
                    LOGGER_INFO(f"⚡ Performance Report: {perf_report}", "GREEN")
                if stress_report:
                    LOGGER_INFO(f"🔥 Stress Report: {stress_report}", "GREEN")
                LOGGER_INFO("=" * 50, "BLUE")
                
                print(f"\n🎉 Test case '{self.case_name}' completed!")
                print(f"📊 Reports saved to:")
                print(f"   📝 Navigation: {nav_report}")
                if perf_report:
                    print(f"   ⚡ Performance: {perf_report}")
                if stress_report:
                    print(f"   🔥 Stress: {stress_report}")
                return True
            else:
                LOGGER_INFO("❌ Test execution failed", "RED")
                return False
                
        except Exception as e:
            LOGGER_INFO(f"❌ ERROR: {str(e)}", "RED")
            return False


if __name__ == "__main__":
    # Initialize COM
    pythoncom.CoInitialize()
    
    try:
        # Create and run debug test
        runner = SimpleDebugRunner()
        success = runner.run()
        
        if not success:
            print(f"❌ Test case '{runner.case_name}' failed!")
            exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        exit(1)
