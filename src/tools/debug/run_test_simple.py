"""
run_test_simple.py

Universal Simple Test Runner
============================

Generic test runner that can handle any test case type.
This script automatically detects the test type and provides appropriate feedback.

Usage:
    python src/tools/debug/run_test_simple.py --case meetings/interaction/test_single_reaction_thumbs_up
    python src/tools/debug/run_test_simple.py --case meetings/share/test_basic_screen_sharing
    python src/tools/debug/run_test_simple.py --case meetings/chat/test_chat_in_pmr_meeting
"""

import pythoncom
import argparse
import sys
import os

# Modify sys.argv before any imports to prevent conflicts
def setup_args(case_name):
    """Setup arguments for the system to use"""
    sys.argv = [
        'run_test_simple.py',
        '--test_suite', case_name,
        '--mode', 'case', 
        '--keepApp'  # Always keep app to prevent installation
    ]

def parse_debug_args():
    """Parse our simple debug arguments"""
    parser = argparse.ArgumentParser(
        description='Universal Simple Test Runner',
        add_help=False  # Disable help to avoid conflicts
    )
    parser.add_argument('--case', '-c', 
                       # Universal test cases - can handle any test type:
                       default='meetings/interaction/test_single_reaction_thumbs_up',
                       help='Test case to run (any type: interaction, share, chat, etc.)')
    
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


class UniversalTestRunner:
    """
    Universal test runner for debugging any type of test
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
        LOGGER_INFO("🚀 Starting minimal test initialization (skipping database cleanup)", "CYAN")
        
        # Initialize settings only (skip database cleanup)
        from common.startup.startup_initializer import StartupInitializer
        startup = StartupInitializer.__new__(StartupInitializer)  # Create without calling __init__
        startup.settings_init()  # Only initialize settings
        
        # Initialize output folders only
        from common.startup.output_initializer import OutputInitializer
        output_initializer = OutputInitializer()
        output_initializer.setup()
        
        LOGGER_INFO("✅ Minimal initialization complete - database cleanup skipped", "GREEN")
    
    def _detect_test_type(self):
        """Detect test type based on case name"""
        if "/interaction/" in self.case_name:
            if "reaction" in self.case_name:
                if "thumbs_up" in self.case_name:
                    return "🧪", "👍 Thumbs Up Reaction Test"
                elif "complete" in self.case_name:
                    return "🧪", "😊 Complete Reactions Test"
                else:
                    return "🧪", "😊 Reaction Test"
            elif "raise_hand" in self.case_name:
                if "basic" in self.case_name:
                    return "🧪", "✋ Basic Raise Hand Test"
                else:
                    return "🧪", "✋↓ Raise/Lower Hand Test"
            else:
                return "🧪", "🎭 Interaction Test"
        elif "/share/" in self.case_name:
            if "basic" in self.case_name:
                return "📺", "📺 Basic Screen Sharing Test (Start → Stop)"
            elif "complete" in self.case_name:
                return "📺", "📺 Complete Screen Sharing Test (Start → Pause/Resume → Stop)"
            else:
                return "📺", "📺 Screen Sharing Test"
        elif "/chat/" in self.case_name:
            return "💬", "💬 Chat Test"
        elif "/audio_setting/" in self.case_name or "/mute/" in self.case_name:
            return "🔇", "🔇 Audio/Mute Test"
        elif "/video_setting/" in self.case_name or "/video/" in self.case_name:
            return "📹", "📹 Video Test"
        elif "/layout/" in self.case_name:
            return "🖼️", "🖼️ Layout Test"
        else:
            return "🧪", f"🧪 Test Case: {self.case_name.split('/')[-1]}"
    
    def _apply_debug_settings(self):
        """Apply debug-friendly settings"""
        # Disable features not needed for debugging
        FeatureToggle.features['installer'] = False      # No Webex install
        FeatureToggle.features['upload_output'] = False  # No upload
        
        # Set basic settings
        settings.set('openai', False)  # Disable AI by default
        settings.set('jira', False)    # Disable JIRA
        
        # Detect test type
        icon, test_type = self._detect_test_type()
        
        LOGGER_INFO(f"{icon} UNIVERSAL DEBUG: Running test case '{self.case_name}'", "CYAN")
        LOGGER_INFO("   ✅ Webex installation: DISABLED", "GREEN")
        LOGGER_INFO("   ✅ Report upload: DISABLED", "GREEN")
        LOGGER_INFO("   ✅ Reports saved locally only", "GREEN")
        LOGGER_INFO(f"🎯 Test Type: {test_type}", "BLUE")
    
    def run(self):
        """Run the test case"""
        try:
            icon, test_type = self._detect_test_type()
            
            LOGGER_INFO("=" * 50, "BLUE")
            LOGGER_INFO(f"🚀 Starting {test_type.split()[1]} Test Execution", "BLUE")
            LOGGER_INFO("=" * 50, "BLUE")
            
            # Execute test case
            nav_report, perf_report = self.test_runner.run_test_suite(
                self.case_name, mode="case"
            )
            
            if nav_report and perf_report:
                LOGGER_INFO("=" * 50, "BLUE")
                LOGGER_INFO(f"✅ {test_type.split()[1]} Test Completed Successfully!", "GREEN")
                LOGGER_INFO(f"📝 Navigation Report: {nav_report}", "GREEN")
                LOGGER_INFO(f"⚡ Performance Report: {perf_report}", "GREEN")
                LOGGER_INFO("=" * 50, "BLUE")
                
                print(f"\n🎉 Test '{self.case_name}' completed!")
                print(f"📊 Reports saved to:")
                print(f"   📝 {nav_report}")
                print(f"   ⚡ {perf_report}")
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
        # Create and run test
        runner = UniversalTestRunner()
        success = runner.run()
        
        if not success:
            print(f"❌ Test '{runner.case_name}' failed!")
            exit(1)
        else:
            print(f"🎉 Test '{runner.case_name}' completed successfully!")
            
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        exit(1)
