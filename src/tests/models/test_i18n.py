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

API_URL = "http://wrs.qa.webex.com:9902/api/chat_image/"

IMAGE_PATH = r"src/tests/models/sample/i18n_si.png"
OUTPUT_MD_PATH = r"src/tests/models/results/i18n/i18n_report.md"

def send_image(image_path):
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        response = requests.post(API_URL, files=files)
    print(response.status_code, response.text)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        markdown_content = data.get("result", "")  # Extract the 'result' field

        # Convert the image path to a relative path for Markdown
        image_filename = os.path.basename(image_path)

        # Add the image reference to the Markdown file
        markdown_header = f"# Localization Analysis Report\n\n"
        markdown_image = f"![Analyzed Image]({image_filename})\n\n"
        
        # Combine all Markdown content
        full_markdown_content = markdown_header + markdown_image + markdown_content

        # Save the response and image reference to a Markdown file
        with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as md_file:
            md_file.write(full_markdown_content)

        print(f"✅ Markdown file saved: {OUTPUT_MD_PATH}")
    else:
        print(f"❌ Request failed, status code: {response.status_code}, response: {response.text}")

send_image(IMAGE_PATH)
