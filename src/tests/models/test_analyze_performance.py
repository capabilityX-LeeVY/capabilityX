
import requests
import os
import sys
import requests

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient


def test_analyze_performance():
    """
    Test the analyze_performance method using a sample performance report markdown file
    and save the result as a markdown file.
    """
    print("=== Testing Performance Analysis API ===")
    
    # Initialize the OpenAI client
    client = OpenAIClient()
    
    # Define the path to the sample markdown file
    sample_file_path = fr"src\tests\models\sample\performance-report-video_vbg.md"
    
    print(f"Sample file path: {sample_file_path}")
    
    # Check if the file exists
    if not os.path.exists(sample_file_path):
        print(f"❌ Error: Sample file not found at {sample_file_path}")
        return False
    
    print(f"✅ Sample file found: {os.path.basename(sample_file_path)}")
    
    try:
        # Analyze performance using file path
        print("\n--- Analyzing performance report ---")
        result = client.analyze_performance(file_path=sample_file_path)
        
        if result:
            print("✅ Analysis successful!")
            print(f"Response length: {len(result)} characters")
            
            # Save the result as markdown file
            output_file_path = fr"src\tests\models\sample\performance-analysis-result.md"
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write("# Performance Analysis Result\n\n")
                f.write(f"**Analysis Date:** {os.path.basename(sample_file_path)}\n\n")
                f.write("## AI Analysis Report\n\n")
                f.write(result)
            
            print(f"📄 Analysis result saved to: {output_file_path}")
            print(f"📊 Result preview:\n{result[:300]}...")
            
            return True
        else:
            print("❌ Analysis failed!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def main():
    """
    Main function to run the performance analysis test.
    """
    print("Starting Performance Analysis Test...")
    
    success = test_analyze_performance()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
    
    return success


if __name__ == "__main__":
    main()