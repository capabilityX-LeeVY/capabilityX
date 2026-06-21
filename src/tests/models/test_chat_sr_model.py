import requests
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

from rs_sdk.utils.model_handler import ModelHandler

def test_chat():
    """Simple chat test"""
    report_id = 'f834f6d4-d82b-42ad-9069-1db42cc64c19'
    model_handler = ModelHandler()
    result = model_handler.handle_screen_reader_analysis(report_id=report_id, test_suite='smoke')

    print(f"📩 Running screen reader analysis for report ID: {report_id}")
    # print(f"🤖 Response: {result}")

if __name__ == "__main__":
    print("🚀 Starting Simple Chat Test...")
    test_chat()
