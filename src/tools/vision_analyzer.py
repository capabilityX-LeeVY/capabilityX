"""
Vision Analyzer Tool
====================

Tool for analyzing screenshots using OpenAI GPT-4 Vision API.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from openai import AzureOpenAI
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING, LOGGER_DEBUG


def get_openai_client():
    """Get configured OpenAI client"""
    try:
        from agent.openai_config import get_client
        return get_client()
    except Exception as e:
        LOGGER_ERROR(f"Failed to get OpenAI client: {e}")
        return None


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Encode image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string or None if failed
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        LOGGER_ERROR(f"Failed to encode image: {e}")
        return None


def analyze_screenshot_with_openai(
    screenshot_path: str,
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 1000
) -> Optional[Dict[str, Any]]:
    """
    Analyze a screenshot using OpenAI GPT-4 Vision API.
    
    Args:
        screenshot_path: Path to the screenshot file
        prompt: Analysis prompt/question
        model: Model to use (default: gpt-4o for vision)
        max_tokens: Maximum tokens in response
        
    Returns:
        Parsed JSON response or None if failed
    """
    LOGGER_INFO(f"🔍 Analyzing screenshot: {screenshot_path}")
    
    # Verify file exists
    if not os.path.exists(screenshot_path):
        LOGGER_ERROR(f"Screenshot file not found: {screenshot_path}")
        return None
    
    # Encode image to base64
    base64_image = encode_image_to_base64(screenshot_path)
    if not base64_image:
        return None
    
    # Try with automatic token refresh on 401 error
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Get OpenAI client (may be refreshed on retry)
            if attempt > 0:
                LOGGER_INFO(f"🔄 Retry attempt {attempt + 1}/{max_retries} with refreshed token...")
                from agent.openai_config import get_client
                client = get_client(force_refresh=True)
            else:
                client = get_openai_client()
            
            if not client:
                LOGGER_ERROR("OpenAI client not available")
                return None
            
            LOGGER_DEBUG(f"Sending vision API request with prompt length: {len(prompt)} chars")
            
            # Call GPT-4 Vision API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.0  # Use deterministic response for analysis
            )
            
            # Success - break retry loop
            break
            
        except Exception as e:
            error_str = str(e)
            # Check if it's a 401 token expired error
            if "401" in error_str and "expired" in error_str.lower():
                if attempt < max_retries - 1:
                    LOGGER_WARNING(f"⚠️ Token expired (401), refreshing and retrying...")
                    continue
                else:
                    LOGGER_ERROR(f"Failed to analyze after token refresh: {e}")
                    return None
            else:
                # Other error, don't retry
                LOGGER_ERROR(f"Failed to analyze screenshot with OpenAI: {e}")
                return None
    
    try:
        
        # Extract response content
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            LOGGER_DEBUG(f"Received response: {content[:200]}...")
            
            # Try to parse as JSON
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                result = json.loads(content)
                LOGGER_INFO(f"✅ Successfully analyzed screenshot")
                
                # Ensure 'success' field is present in result
                if 'success' not in result:
                    result['success'] = True
                    
                # For observation feature compatibility, wrap result if needed
                if 'ui_type' in result or 'confidence' in result:
                    # This is an observation analysis result
                    return {
                        'success': True,
                        'analysis': result
                    }
                
                return result
            except json.JSONDecodeError as e:
                LOGGER_WARNING(f"Response is not JSON, returning as text: {e}")
                return {
                    "success": True,
                    "raw_response": content
                }
        else:
            LOGGER_ERROR("Empty response from OpenAI Vision API")
            return None
            
    except Exception as e:
        LOGGER_ERROR(f"Failed to analyze screenshot with OpenAI: {e}")
        return None


def analyze_meeting_status(screenshot_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to analyze if user has joined a Webex meeting.
    
    Args:
        screenshot_path: Path to meeting window screenshot
        
    Returns:
        Analysis result with joined status
    """
    prompt = """Please analyze this Webex meeting screenshot and determine if the user has successfully joined the meeting.

Look for these indicators:
1. Meeting window is open and visible
2. Meeting controls (Mute, Stop video, End meeting buttons) are present
3. Video/participant views are visible
4. Meeting room name or participant names are shown
5. Either in the meeting lobby waiting for host, or actively in the meeting

Respond in JSON format:
{
    "joined": true/false,
    "status": "in_meeting" | "waiting_for_host" | "failed" | "unknown",
    "confidence": 0.0-1.0,
    "details": "Brief explanation of what you see"
}"""
    
    return analyze_screenshot_with_openai(screenshot_path, prompt)


if __name__ == "__main__":
    # Test the vision analyzer
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vision_analyzer.py <screenshot_path> [prompt]")
        sys.exit(1)
    
    screenshot_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Describe what you see in this image."
    
    result = analyze_screenshot_with_openai(screenshot_path, prompt)
    
    if result:
        print("\n=== Analysis Result ===")
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed")
