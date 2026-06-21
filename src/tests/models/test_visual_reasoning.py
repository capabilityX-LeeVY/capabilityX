"""
WebEx Visual Assistant for Visually Impaired Users

This module provides a simplified interface description and meeting action prediction
specifically designed for blind users using WebEx applications.
"""

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

def visual_reasoning(image_path=None):
    """
    Proactive WebEx assistant that offers to help perform actions for blind users
    
    Args:
        image_path (str): Path to WebEx screenshot, uses default if None
    
    Returns:
        str: Natural guidance ending with offer to help and permission request
    """
    if image_path is None:
        image_path = fr"src\tests\models\sample\reasoning\webex-04.png"
    
    # Optimized prompt with context-aware recommendations and priority logic
    visual_reasoning_prompt = """
You are a helpful WebEx assistant for blind users. Your goal is to help users start meetings and navigate WebEx efficiently.

Analyze this WebEx screenshot and provide a brief, natural response like a human assistant would give.

**Smart Priority Guidelines:**
1. **Initial Welcome Screen** (with "Sign In" and "Join a Meeting" options):
   - Prioritize "Sign In" and explain it gives full access to features
   
2. **Already Signed In Screens** (with "Start a Meeting" available):
   - Prioritize "Start a Meeting" over other sign-in prompts
   - Don't mention signing in benefits if user is already signed in
   
3. **Email/Password Input Screens**:
   - Focus on completing the current input step
   - No need to explain signing in benefits again
   
4. **Other Screens**:
   - Choose the most logical next action for meeting workflow

**Context-Aware Responses:**
- Only mention "signing in gives full access to features" on initial welcome screens
- If "Start a Meeting" is available, prioritize it over additional sign-in prompts
- For input fields (email/password), focus on completing the current step
- Keep responses natural and avoid repetitive explanations

**Output Format:**
Provide a single, natural paragraph (2-3 sentences) that includes:
1. What you see on the screen
2. Context-appropriate recommendation (no repetitive sign-in benefits)
3. Offer to help perform the action and ask for permission

**Example Styles:**

*Initial Welcome:* "I see the WebEx welcome screen with options to join a meeting or sign in. Signing in gives you full access to features like hosting and scheduling. I can help navigate to the 'Sign In' button and press Enter to proceed—would you like me to do that?"

*Email Input:* "I see the WebEx sign-in screen asking for your email address. I can help navigate to the email field and type in your email address, then press Enter to continue—would you like me to do that?"

*Already Signed In with Start Meeting:* "I see your WebEx dashboard with options to start, join, or schedule a meeting. I can help navigate to 'Start a Meeting' to begin hosting your meeting right away—would you like me to do that?"

Always end by offering to perform the action and asking for permission.
"""

    client = OpenAIClient()
    result = client.ai_analyze_image(image_path, message=visual_reasoning_prompt)
    
    if result:
        LOGGER_INFO("WebEx assistant guidance completed", "GREEN")
        print("\n" + "="*50)
        print("WebEx Assistant")
        print("="*50)
        print(result)
        print("="*50)
    else:
        LOGGER_ERROR("WebEx assistant guidance failed", "RED")
    
    return result

def test_different_scenarios():
    """
    Test visual reasoning with different WebEx scenarios to show context-aware responses
    """
    print("\n" + "="*60)
    print("Testing Different WebEx Scenarios")
    print("="*60)
    
    scenarios = [
        ("webex-01.png", "Initial Welcome Screen"),
        ("webex-02.png", "Email Input Screen"), 
        ("webex-03.png", "Password Input Screen"),
        ("webex-04.png", "Signed In Dashboard")
    ]
    
    for image_name, description in scenarios:
        print(f"\n--- {description} ---")
        try:
            image_path = f"src/tests/models/sample/reasoning/{image_name}"
            visual_reasoning(image_path)
        except:
            print(f"Image {image_name} not found, using default")
            visual_reasoning()
        print("-" * 50)

if __name__ == "__main__":
    print("WebEx Assistant - Ready to help you sign in and start meetings")
    print("Analyzing current screen...")
    
    # Run the main visual reasoning function
    visual_reasoning()
    
    # Optionally run scenario tests
    # test_different_scenarios()
    
    print("\nGuidance provided!")

# Usage Examples:
"""
Context-Aware WebEx Assistant - Smart Priority Recommendations

Usage:
1. Run directly: python test_visual_reasoning.py
2. Specify image: visual_reasoning("webex_screenshot.jpg")
3. Import in programs:
   from test_visual_reasoning import visual_reasoning
   guidance = visual_reasoning("image.png")

Smart Features:
- Context-aware responses based on screen type
- Only mentions sign-in benefits on initial welcome screens
- Prioritizes "Start a Meeting" when user is already signed in
- Avoids repetitive explanations about signing in
- Natural, efficient guidance for each workflow stage

Response Examples:
- Welcome Screen: Explains sign-in benefits and recommends signing in
- Email/Password: Focuses on completing current input step
- Dashboard: Prioritizes "Start a Meeting" over additional sign-ins
- Perfect for blind users who need context-appropriate assistance
"""
