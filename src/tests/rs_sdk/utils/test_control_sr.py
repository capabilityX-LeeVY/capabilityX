import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from core.processor.srText_processor import ScreenReaderDataProcessor
from models.openai_client import OpenAIClient
from rs_sdk.utils.report_handler import write_screen_reader_report  # Add this import
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from common.startup.startup_initializer import StartupInitializer


def test_srText_processor():
    report_id = '23c17b6f-eb1c-464f-aa15-a95825a4a834'
    initializer = StartupInitializer()
    initializer.setup()

    srText_processor = ScreenReaderDataProcessor()
    file_name_path = srText_processor.get_screen_reader_data_for_cloud(report_id)

    LOGGER_INFO(f"Control datasets Path: {file_name_path}", "GREEN")
    
    return file_name_path


def test_chat_sr():
    """Test chat_sr() method with screen reader data file"""
    
    # Get the file path from the existing test
    file_name_path = test_srText_processor()
    
    if not file_name_path or not os.path.exists(file_name_path):
        LOGGER_ERROR(f"Screen reader data file not found: {file_name_path}", "RED")
        return None
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAIClient()
        
        LOGGER_INFO(f"Testing chat_sr() with file: {file_name_path}", "CYAN")
        
        # Call chat_sr method
        result = openai_client.chat_sr(file_name_path)
        
        # Log the result
        if result:
            LOGGER_INFO(f"chat_sr() executed successfully", "GREEN")
            LOGGER_DEBUG(f"Result: {result}")
            
            # Write the result to screen reader report
            report_file_path = write_screen_reader_report(
                markdown_content=result,
                test_suite="sr_control_test",
                report_id="23c17b6f-eb1c-464f-aa15-a95825a4a834"
            )
            
            if report_file_path:
                LOGGER_INFO(f"Screen reader report saved to: {report_file_path}", "GREEN")
            else:
                LOGGER_WARNING("Failed to save screen reader report", "YELLOW")
            
            return result
        else:
            LOGGER_WARNING(f"chat_sr() returned empty result", "YELLOW")
            return None
            
    except Exception as e:
        LOGGER_ERROR(f"Error testing chat_sr(): {str(e)}", "RED")
        raise


def run_all_tests():
    """Run all tests"""
    LOGGER_INFO("Starting SR control tests...", "BLUE")
    
    try:
        # Test 1: SR Text Processor
        LOGGER_INFO("=" * 50, "BLUE")
        LOGGER_INFO("Test 1: SR Text Processor", "BLUE")
        test_srText_processor()
        
        # Test 2: OpenAI Chat SR
        LOGGER_INFO("=" * 50, "BLUE")  
        LOGGER_INFO("Test 2: OpenAI Chat SR", "BLUE")
        result = test_chat_sr()
        
        if result:
            LOGGER_INFO("Screen reader report generated and saved successfully!", "GREEN")
        
        LOGGER_INFO("=" * 50, "GREEN")
        LOGGER_INFO("All tests completed successfully!", "GREEN")
        
    except Exception as e:
        LOGGER_ERROR(f"Test suite failed: {str(e)}", "RED")


if __name__ == "__main__":
    run_all_tests()

