import requests
import os
import sys
from pathlib import Path

# Import settings for dynamic parameter retrieval
try:
    from config.global_settings import settings
except ImportError:
    # Fallback if import fails
    settings = None

def send_stress_message_to_webex(markdown_message=None, duration=300):
    """
    Sends a stress test message to a Webex bot space.

    Parameters:
    - markdown_message: str, the message to send in markdown format (optional)
    - duration: int, duration to wait after sending message (default: 300 seconds)

    Returns:
    - str: Success or error message
    """
    # Default bot token and room details - these should ideally be in config
    bot_token = "YTk3MGM2NzEtODAzNi00MGVlLTg2NzItYjliMGY0MzY5ZDE4NDYyMzY0YWItZWY2_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
    room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vNGQzYzI0MzAtOTJmMy0xMWVmLTkzNzYtNDNmMGYwMjA1OTBm"
    
    # Default stress test message if not provided
    if markdown_message is None:
        markdown_message = "<@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com audio=off video=on send_reactions=on send_chat=on with 10 ucf_api duration 3"
    
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "roomId": room_id,
        "markdown": markdown_message
    }

    try:
        print('=============================================================')
        print(f"Sending stress test message: {markdown_message}")
        print(f"Duration: {duration} seconds")
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = f"Stress test message sent successfully! Waiting {duration} seconds..."
            print(result)
            print('=============================================================')
            
            # Wait for the specified duration (simulating stress test time)
            import time
            time.sleep(duration)
            
            return f"Stress test completed successfully after {duration} seconds"
        else:
            error_msg = f"Failed to send message. Status code: {response.status_code}\nResponse: {response.text}"
            print(error_msg)
            print('=============================================================')
            return error_msg
    except Exception as e:
        error_msg = f"An error occurred during stress test: {str(e)}"
        print(error_msg)
        print('=============================================================')
        return error_msg


def send_stress_message_to_webex_dynamic():
    """
    Sends a stress test message to Webex bot space using dynamic parameters from settings.
    This function reads all parameters from the global settings to avoid YAML hardcoded values.
    
    Returns:
    - str: Success or error message
    """
    try:
        # Get dynamic parameters from settings
        if settings is None:
            return "Error: Settings module not available"
        
        # Retrieve parameters set by the API with proper defaults
        participants = settings.get('stress_participants', 20)
        duration_minutes = settings.get('stress_duration', 3)
        audio_setting = settings.get('stress_audio', 'off')
        video_setting = settings.get('stress_video', 'on')
        chat_setting = settings.get('stress_chat', 'on')
        reactions_setting = settings.get('stress_reactions', 'on')
        
        # Ensure duration_minutes is a valid number
        if duration_minutes is None:
            duration_minutes = 3
        
        # Convert duration from minutes to seconds for the sleep function
        duration_seconds = int(duration_minutes) * 60
        
        # Build dynamic markdown message
        markdown_message = f"<@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com audio={audio_setting} video={video_setting} send_reactions={reactions_setting} send_chat={chat_setting} with {participants} ucf_api duration {duration_minutes}"
        
        # Bot token and room details
        bot_token = "YTk3MGM2NzEtODAzNi00MGVlLTg2NzItYjliMGY0MzY5ZDE4NDYyMzY0YWItZWY2_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
        room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vNGQzYzI0MzAtOTJmMy0xMWVmLTkzNzYtNDNmMGYwMjA1OTBm"
        
        url = "https://webexapis.com/v1/messages"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "roomId": room_id,
            "markdown": markdown_message
        }

        print('=============================================================')
        print(f"Dynamic stress test with parameters:")
        print(f"  Participants: {participants}")
        print(f"  Duration: {duration_minutes} minutes ({duration_seconds} seconds)")
        print(f"  Audio: {audio_setting}")
        print(f"  Video: {video_setting}")
        print(f"  Chat: {chat_setting}")
        print(f"  Reactions: {reactions_setting}")
        print(f"Sending message: {markdown_message}")
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = f"Dynamic stress test message sent successfully! Waiting 60 seconds for bot to process..."
            print(result)
            print('=============================================================')
            
            # Wait 60 seconds for bot to process the command, then continue with chat tests
            import time
            time.sleep(60)
            
            return f"Dynamic stress test initiated successfully with {participants} participants for {duration_minutes} minutes"
        else:
            error_msg = f"Failed to send dynamic message. Status code: {response.status_code}\nResponse: {response.text}"
            print(error_msg)
            print('=============================================================')
            return error_msg
            
    except Exception as e:
        error_msg = f"An error occurred during dynamic stress test: {str(e)}"
        print(error_msg)
        print('=============================================================')
        return error_msg
