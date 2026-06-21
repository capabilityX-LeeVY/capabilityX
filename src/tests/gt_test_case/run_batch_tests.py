#!/usr/bin/env python3
"""
Webex RegressShield - GT Test Case Batch Execution Script
Python script to execute multiple test scenarios with enhanced features
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

def print_header():
    """Print script header"""
    print("=" * 50)
    print("  Webex RegressShield GT Test Case Runner")
    print("=" * 50)
    print()

def print_footer(start_time):
    """Print execution summary"""
    end_time = time.time()
    duration = end_time - start_time
    print("=" * 50)
    print("  GT Test Case Execution Summary")
    print("=" * 50)
    print(f"Total Execution Time: {duration / 60:.2f} minutes")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def run_test_command(description, command):
    """
    Run a test command with error handling and timing
    
    Args:
        description (str): Human readable description of the test
        command (str): Command to execute
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {description}")
    print(f"Command: {command}")
    print()
    
    start_time = time.time()
    
    try:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            cwd=get_project_root(),
            capture_output=False,  # Show real-time output
            text=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description} completed in {duration:.2f} seconds")
            return True
        else:
            print(f"❌ FAILED: {description} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ ERROR: {description} failed with exception: {str(e)}")
        return False
    
    finally:
        print()
        print("-" * 50)
        print()

def get_project_root():
    """Get the project root directory"""
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.parent.parent
    return str(project_root)

def main():
    """Main execution function"""
    print_header()
    
    # Set working directory to project root
    project_root = get_project_root()
    os.chdir(project_root)
    print(f"Project Root: {project_root}")
    print()
    
    # Define test scenarios
    tests = [
        {
            "description": "Test Suite: video_vbg with OpenAI",
            "command": 'uv run python src/run_test_case_job.py --test_suite "video_vbg" --openai'
        },
        {
            "description": "Test Case: vbg_static with OpenAI", 
            "command": 'uv run python src/run_test_case_job.py --test_case "vbg_static" --openai'
        },
        {
            "description": "Stress Test Case: test_stress",
            "command": 'uv run python src/run_test_case_job.py --test_case "stress/test_stress"'
        },
        {
            "description": "Test Batch: video_vbg_batch with OpenAI",
            "command": 'uv run python src/run_test_case_job.py --test_batch "video_vbg_batch" --openai'
        }
    ]
    
    # Track execution
    start_time = time.time()
    success_count = 0
    total_tests = len(tests)
    
    # Execute all tests
    for i, test in enumerate(tests, 1):
        print(f"Test {i}/{total_tests}:")
        success = run_test_command(test["description"], test["command"])
        if success:
            success_count += 1
    
    # Print summary
    print_footer(start_time)
    print(f"Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print(f"⚠️  {total_tests - success_count} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
