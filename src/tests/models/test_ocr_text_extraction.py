"""
OCR Text Extraction Test

This module tests the AI's ability to extract text from images while preserving
the original layout, formatting, and structure of the content.
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
from prompts.prompt_loader import OCRPrompts
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR


def test_extract_ui_elements_default():
    """
    Test extracting UI elements using the default template.
    
    Uses the predefined UI elements extraction template to identify
    all visible UI elements in the screenshot.
    """
    # Use absolute path from project root
    image_path = Path(__file__).parent / "sample" / "whiteboards.png"
    image = str(image_path)
    
    # Create client
    client = OpenAIClient()
    
    # Extract UI elements using default template
    LOGGER_INFO("Testing UI elements extraction with default template...", "BLUE")
    result = client.extract_ui_elements(image)
    
    if result:
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"ui_elements_default_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        LOGGER_INFO(f"✅ UI elements extracted successfully!", "GREEN")
        LOGGER_INFO(f"📂 Output saved to: {output_file}", "GREEN")
        print(f"\n{result}")
        return str(output_file)
    else:
        LOGGER_ERROR("❌ UI elements extraction failed", "RED")
        return None


def test_extract_ui_elements_custom_message():
    """
    Test extracting UI elements using a custom message.
    
    Demonstrates how to use a custom prompt without loading from template.
    """
    image_path = Path(__file__).parent / "sample" / "whiteboards.png"
    image = str(image_path)
    
    # Create client
    client = OpenAIClient()
    
    # Custom message for extracting only buttons
    custom_message = """
    Extract all button elements from this UI screenshot.
    
    Return a markdown table with columns:
    | Button Text | Position | Type |
    
    Type can be: Text Button, Icon Button, or Composite Button
    """
    
    LOGGER_INFO("Testing UI elements extraction with custom message...", "BLUE")
    result = client.extract_ui_elements(image, custom_message=custom_message)
    
    if result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_file = output_dir / f"ui_elements_custom_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        LOGGER_INFO(f"✅ Custom extraction completed!", "GREEN")
        LOGGER_INFO(f"📂 Output saved to: {output_file}", "GREEN")
        print(f"\n{result}")
        return str(output_file)
    else:
        LOGGER_ERROR("❌ Custom extraction failed", "RED")
        return None


def test_extract_text_simple():
    """
    Test simple text extraction from an image.
    
    Extracts all visible text while preserving layout and structure.
    """
    image_path = Path(__file__).parent / "sample" / "whiteboards.png"
    image = str(image_path)
    
    # Create client
    client = OpenAIClient()
    
    LOGGER_INFO("Testing simple text extraction...", "BLUE")
    result = client.extract_text_simple(image)
    
    if result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_file = output_dir / f"text_simple_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        LOGGER_INFO(f"✅ Text extracted successfully!", "GREEN")
        LOGGER_INFO(f"📂 Output saved to: {output_file}", "GREEN")
        print(f"\n{result}")
        return str(output_file)
    else:
        LOGGER_ERROR("❌ Text extraction failed", "RED")
        return None


def test_extract_text_with_layout():
    """
    Legacy test function - now calls the new API method.
    
    This test analyzes an image containing text and extracts all readable content
    while maintaining the original structure, hierarchy, and formatting.
    """
    LOGGER_WARNING("test_extract_text_with_layout is deprecated. Use test_extract_ui_elements_default instead.", "YELLOW")
    return test_extract_ui_elements_default()


if __name__ == "__main__":
    print("=" * 80)
    print("OCR Text Extraction Tests")
    print("=" * 80)
    
    # Test 1: Default UI elements extraction
    print("\n\n📋 Test 1: Extract UI Elements (Default Template)")
    print("-" * 80)
    test_extract_ui_elements_default()
    
    # Test 2: Custom message extraction
    # print("\n\n📋 Test 2: Extract UI Elements (Custom Message)")
    # print("-" * 80)
    # test_extract_ui_elements_custom_message()
    
    # Test 3: Simple text extraction
    # print("\n\n📋 Test 3: Simple Text Extraction")
    # print("-" * 80)
    # test_extract_text_simple()
    
    print("\n\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
