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

from models.openai_client import OpenAIClient

def test_chat():
    """Simple chat test"""
    message = "Hello, please say hi back to me."
    
    print(f"📩 Sending message: {message}")
    
    client = OpenAIClient()
    response = client.chat(message)
    
    if response:
        print(f"✅ Chat test successful!")
        print(f"🤖 Response: {response}")
        return True
    else:
        print("❌ Chat test failed - no response received")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Chat Test...")
    success = test_chat()
    
    if success:
        print("🎉 Test passed!")
    else:
        print("❌ Test failed!")
        sys.exit(1)
