"""
ai_verify_current_state.py

Capture the foreground window screenshot and use AI vision
to verify the current UI state against a given prompt.
"""

import os
import sys

# from dotenv import load_dotenv
# load_dotenv()
# pythonpath = os.getenv("PYTHONPATH")
# if pythonpath:
#     full_path = os.path.abspath(pythonpath)
#     if full_path not in sys.path:
#         sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from rs_sdk.utils.control_recorder import ControlRecorder


DEFAULT_PROMPT = (
    "Analyze the current application state. "
    "Describe: 1) What window or screen is visible? "
    "2) Are the expected UI controls present? "
    "3) Is there any error message or unexpected state? "
    "Output format: "
    "If the state looks correct, respond '[SUCCESS]Success. [Brief description].' "
    "If something looks wrong, respond '[FAILURE]Failed. [What is wrong].' "
    "Only output 1 sentence."
)


def ai_verify_current_state(prompt: str = None) -> str:
    """
    Capture the current foreground window and use AI vision to verify
    the UI state matches the expected condition described in the prompt.

    Args:
        prompt: AI analysis prompt describing what to check.
                Uses a generic default when omitted.

    Returns:
        str: AI analysis result string, e.g. '[SUCCESS]Success. ...'
    """
    try:
        LOGGER_INFO("[ai_verify_current_state] Capturing foreground window ...", "BLUE")
        recorder = ControlRecorder()
        image_path, _ = recorder.capture_foreground_window_image()

        if not image_path or not os.path.exists(image_path):
            LOGGER_ERROR("[ai_verify_current_state] Failed to capture window screenshot", "RED")
            return "[FAILURE]Failed. Could not capture window screenshot."

        LOGGER_INFO(f"[ai_verify_current_state] Screenshot saved: {image_path}", "GREEN")

        analysis_prompt = prompt or DEFAULT_PROMPT
        LOGGER_INFO("[ai_verify_current_state] Sending to AI for analysis ...", "BLUE")

        client = OpenAIClient()
        result = client.ai_analyze_image(image_path, message=analysis_prompt)

        if result:
            LOGGER_INFO(f"[ai_verify_current_state] AI result: {result}", "GREEN")
        else:
            result = "[FAILURE]Failed. AI analysis returned no result."
            LOGGER_ERROR(f"[ai_verify_current_state] {result}", "RED")

        return result

    except Exception as e:
        LOGGER_ERROR(f"[ai_verify_current_state] Error: {e}", "RED")
        return f"[FAILURE]Failed. Error: {e}"
