
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

def test_analyze_image():
    image = fr"src\tests\models\sample\font_size_issue_02.png"
    message = """
You are an accessibility and UI compliance auditor. 
Analyze the provided screenshot for **font size compliance** under WCAG 2.2 AA.

1. For each visible text element (labels, tooltips, subtitles, buttons, main UI text):
   - Estimate the font size in px/pt.
   - Compare against WCAG 2.2 AA requirements:
     - Normal text: at least ~16px (12pt).
     - Large text: ≥18pt regular or ≥14pt bold.
   - Check if text remains legible at 200% zoom (SC 1.4.4, SC 1.4.10).
   - Mark as Pass or Fail strictly.

2. Output results in a markdown table with columns:
   | Element | Font Size (approx) | WCAG 2.2 Requirement | Compliance | Suggested Resolution |

3. After the table, provide a **Final Summary**:
   - WCAG 2.2 Font Size Overall: [Pass/Fail]
   - Best Practice Overall: [Pass/Fail]
"""

    if not os.path.exists(image):
        raise FileNotFoundError(f"Target image not found: {image}")

    # Create results directory if it doesn't exist
    results_dir = os.path.join("src", "tests", "models", "results", "font_size")
    os.makedirs(results_dir, exist_ok=True)

    client = OpenAIClient()
    analysis_result = client.ai_analyze_image(image, message=message)
    
    # Check if we got a result
    if analysis_result is None:
        print("Failed to get analysis result from AI")
        return None
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = os.path.splitext(os.path.basename(image))[0]
    result_filename = f"accessibility_audit_{image_name}_{timestamp}.md"
    result_path = os.path.join(results_dir, result_filename)
    
    # Generate relative path from results directory to the image
    # From: src/tests/models/results/color_contrast/ to src/tests/models/sample/
    relative_image_path = f"..{os.sep}..{os.sep}sample{os.sep}{os.path.basename(image)}"
    
    # Save analysis result to markdown file
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(f"# Accessibility Audit Report\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Source Image:** {image}\n\n")
        f.write(f'<img src="{relative_image_path}" alt="{image_name}" style="max-width: 800px; height: auto;">\n\n')
        f.write("---\n\n")
        f.write(str(analysis_result))
    
    print(f"Analysis result saved to: {result_path}")
    return result_path


if __name__ == "__main__":
    test_analyze_image()
    print("Image analysis completed successfully.")
