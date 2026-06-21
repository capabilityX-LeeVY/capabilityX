
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from rs_sdk.utils.model_handler import ModelHandler
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR


def test_handle_analyze_performance():
    """
    Test the handle_analyze_performance method using a specific performance report file.
    """
    print("=== Testing ModelHandler.handle_analyze_performance ===")
    
    # Initialize the ModelHandler
    model_handler = ModelHandler()
    
    # Define the performance report path (using relative path from project root)
    performance_report_path = fr'C:\devagent\deepNavigation\wrs-output\Dell-XPS15-Inteli9-Utral-High_72RX2D3\20250729-094329\report\performance\performance-report-video_vbg.md'
    print(f"Performance report path: {performance_report_path}")
    
    # Check if the file exists    
    print(f"✅ Performance report file found: {os.path.basename(performance_report_path)}")
    
    try:
        # Test the handle_analyze_performance method
        print("\n--- Testing handle_analyze_performance ---")
        
        # Read original file content for comparison
        with open(performance_report_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        original_size = len(original_content)
        print(f"Original file size: {original_size} characters")
        
        # Call the method under test
        result = model_handler.handle_analyze_performance(performance_report_path)
        
        # Validate the result
        if result['success']:
            print("✅ Performance analysis successful!")
            print(f"Original path: {result['original_path']}")
            print(f"Updated path: {result['updated_path']}")
            
            # Check if the file was actually updated
            if os.path.exists(result['updated_path']):
                with open(result['updated_path'], 'r', encoding='utf-8') as f:
                    updated_content = f.read()
                
                updated_size = len(updated_content)
                print(f"Updated file size: {updated_size} characters")
                print(f"Content added: {updated_size - original_size} characters")
                
                # Check if analysis section was added
                if "# AI Performance Analysis" in updated_content:
                    print("✅ AI analysis section successfully appended!")
                else:
                    print("⚠️  Warning: AI analysis section not found in updated file")
                
                # Show the analysis result preview
                if 'analysis_result' in result and result['analysis_result']:
                    analysis_preview = result['analysis_result'][:200]
                    print(f"📊 Analysis preview: {analysis_preview}...")
                
            else:
                print("❌ Updated file not found!")
                return False
        else:
            print("❌ Performance analysis failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
        
        print("\n=== Test completed successfully! ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def main():
    """
    Main function to run the performance analysis test.
    """
    print("Starting ModelHandler Performance Analysis Test...")
    
    success = test_handle_analyze_performance()
    
    if success:
        print("\n🎉 Test passed!")
    else:
        print("\n💥 Test failed!")
    
    return success


if __name__ == "__main__":
    main()
