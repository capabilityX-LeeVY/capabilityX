import requests
import os

API_URL = "http://wrs.qa.webex.com:9902/api/demo_vision/"

IMAGE_PATH = r"src\tests\models\result\02.jpg"
OUTPUT_MD_PATH = r"src/tests/models/result/demo_vision.md"

def send_image(image_path, message):
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        data = {"message": message}
        response = requests.post(API_URL, files=files, data=data)
    print(response.status_code, response.text)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        markdown_content = data.get("result", "")  # Extract the 'result' field

        # Convert the image path to a relative path for Markdown
        image_filename = os.path.basename(image_path)

        # Add the image reference to the Markdown file
        # markdown_header = f"# Localization Analysis Report\n\n"
        # markdown_image = f"![Analyzed Image]({image_filename})\n\n"
        
        # Combine all Markdown content
        # full_markdown_content = markdown_header + markdown_image + markdown_content

        # Save the response and image reference to a Markdown file
        with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)

        print(f"✅ Markdown file saved: {OUTPUT_MD_PATH}")
    else:
        print(f"❌ Request failed, status code: {response.status_code}, response: {response.text}")

send_image(IMAGE_PATH, message="please describe the image")
