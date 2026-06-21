
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

def test_analyze_image_comparison():
    reference_image = fr"src\tests\models\sample\vbg_01_ref.png"
    target_image = fr"src\tests\models\sample\vbg_01.png"
    message = (
    "Task: Verify if the correct virtual background image was successfully applied in the meeting. Compare the reference image (first) with the meeting screenshot (second). Focus ONLY on: 1) Overall color scheme and palette 2) General visual style and aesthetic 3) Basic compositional elements. DO NOT analyze text orientation, logo direction, or any specific element positioning - these are irrelevant due to video processing effects. If the meeting screenshot shows the same general visual theme, colors, and style as the reference image, consider it a SUCCESS regardless of any mirroring, rotation, or orientation differences. Ignore all people and foreground elements. Output: ✅Success or ❌Failure. Reasoning: <brief explanation focusing only on color/style match>"
    )

    if not os.path.exists(reference_image):
        raise FileNotFoundError(f"Reference image not found: {reference_image}")
    if not os.path.exists(target_image):
        raise FileNotFoundError(f"Target image not found: {target_image}")

    client = OpenAIClient()
    client.ai_analyze_image_comparison(reference_image, target_image, message=message)


if __name__ == "__main__":
    test_analyze_image_comparison()
    print("Image comparison analysis completed successfully.")
