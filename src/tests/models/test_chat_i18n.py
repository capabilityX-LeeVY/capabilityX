
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

def test_chat_i18n():
    image_path = fr"src/tests/models/sample/i18n_si.png"
    message = (
        "Task: Analyze this screenshot for internationalization (i18n) issues. "
        "Check for: 1) Text truncation or overflow 2) Improper character encoding "
        "3) UI layout issues with different languages 4) Missing translations "
        "5) Cultural appropriateness. "
        "Output: ✅Success if no i18n issues found, or ❌Failure with specific issues identified. "
        "Reasoning: <brief explanation of findings>"
    )

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    client = OpenAIClient()
    result = client.chat_i18n(image_path, message=message)
    print(f"I18n Analysis Result: {result}")
    return result


if __name__ == "__main__":
    test_chat_i18n()
    print("I18n analysis completed successfully.")
