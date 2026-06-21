
import requests
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

def test_analyze_image():
    image = fr"src\tests\models\sample\large_img\small_Mute.jpg"
    
    # Original message: Count people in image
    message_count_people = (
        "Please analyze this image and count how many people are visible in it. "
        "Look carefully at the entire image and identify each person. "
        "Output the result in this format: "
        "Number of people: X (where X is the actual number) "
        "Description: Brief description of what you see"
    )
    
    # New message: Analyze calling success
    # message_calling_success = "Analyze if 'Start a calling' was successful. Check: 1) Is 'calling...' text visible? 2) Are Mute, Share, Keypad, More buttons present? 3) Is there a blue focus ring on Mute button? Output format: If call connected (no 'calling...' text, all buttons present, blue focus ring on Mute), respond '✅Success. Call connected with all controls and focus ring on Mute.' If still connecting ('calling...' visible), respond '⏳Connecting. Call in progress.' If failed or missing elements, respond '❌Failed. [What's wrong].' Only output emoji and 1-2 sentences."
    message_calling_success = (
        "Analyze this Webex meeting window screenshot and verify TWO independent conditions:\n"
        "Condition 1: The main center area of the window is displaying the content of slide 2 (the second page). "
        "You can confirm this by checking which thumbnail is highlighted/selected in the left sidebar — it should be slide 2.\n"
        "Condition 2: The orange 'Presenter' tag/badge is visible on the thumbnail of slide 1 (the first page) in the left sidebar. "
        "This is the EXPECTED and CORRECT state — the presenter tag stays on slide 1 even when slide 2 is being viewed. "
        "Do NOT treat this as a mismatch or failure.\n"
        "Both conditions must be TRUE for success.\n"
        "Output: ✅Success or ❌Failure. Reasoning: <brief explanation of each condition result>"
    )
    
    # Choose which message to use
    message = message_count_people  # Change this to message_calling_success to test calling analysis

    client = OpenAIClient()
    client.ai_analyze_image(image, message=message)
    

if __name__ == "__main__":
    test_analyze_image()
    LOGGER_INFO("Image analysis completed successfully.")
