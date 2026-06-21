#!/usr/bin/env python3
"""
Stress Test API Call - With Custom Parameters

This script calls the stress test API with custom parameters to override defaults.
"""

from unittest import result
import requests
import json
import time
from datetime import datetime


def call_stress_api_with_params(
    stress_duration=120,           # Stress test duration (seconds)
    participant_count=10,          # Number of participants
    enable_chat_test=True,         # Whether to enable chat testing
    enable_video=False,            # Whether to enable video
    enable_audio=True,             # Whether to enable audio
    test_case_name="test_stress",  # Test case name
    platform="windows",           # Platform
    custom_message=None            # Custom message
):
    """
    Call stress test API - with custom parameters
    
    Args:
        stress_duration (int): Stress test duration in seconds, default 120s (2 minutes)
        participant_count (int): Number of participants, default 10
        enable_chat_test (bool): Whether to enable chat testing, default True → send_chat=on
        enable_video (bool): Whether to enable video, default False → video=off
        enable_audio (bool): Whether to enable audio, default True → audio=on
        test_case_name (str): Test case name, default "test_stress"
        platform (str): Running platform, default "windows"
        custom_message (str): Custom message, default None (auto-generated)
    """
    url = "http://localhost:9909/api/run_stress_test"
    
    # Build payload using input parameters
    payload = {
        "test_case_name": test_case_name,
        "platform": platform,
        "stress_duration": stress_duration,
        "participant_count": participant_count,
        "enable_chat_test": enable_chat_test,
        "enable_video": enable_video,
        "enable_audio": enable_audio,
        "custom_message": custom_message
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("🔧 Stress Test API Call - Custom Parameters")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL: {url}")
    print(f"📦 Request Parameters:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # Dynamically generate expected bot message
    audio_setting = "on" if enable_audio else "off"
    video_setting = "on" if enable_video else "off"
    chat_setting = "on" if enable_chat_test else "off"
    duration_minutes = stress_duration // 60
    
    print(f"\n🚀 Expected Bot Message:")
    print(f"   <@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com")
    print(f"   audio={audio_setting} video={video_setting} send_reactions=on send_chat={chat_setting} with {participant_count} ucf_api duration {duration_minutes}")
    
    try:
        print("\n📡 Sending API Request...")
        print("⏳ Waiting for test_stress.yaml execution (max 10 minutes)...")
        print("💡 Please be patient, stress test is running...")
        
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=600)  # 10 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request Duration: {duration:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Call Successful!")
            print(f"📄 Response Content:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Display key information
            if "execution_id" in result:
                print(f"\n🆔 Execution ID: {result['execution_id']}")
            if "estimated_duration" in result:
                print(f"⏰ Estimated Duration: {result['estimated_duration']} seconds")
            if "stress_config" in result:
                config = result["stress_config"]
                print(f"⚙️  Stress Test Configuration:")
                print(f"   - Duration: {config.get('duration', 'N/A')} seconds")
                print(f"   - Participants: {config.get('participants', 'N/A')}")
                print(f"   - Chat Enabled: {config.get('chat_enabled', 'N/A')}")
                print(f"   - Video Enabled: {config.get('video_enabled', 'N/A')}")
                print(f"   - Audio Enabled: {config.get('audio_enabled', 'N/A')}")
        else:
            print(f"❌ API Call Failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📄 Error Details:")
                print(json.dumps(error_detail, indent=2, ensure_ascii=False))
            except:
                print(f"📄 Error Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Unable to connect to API server")
        print("💡 Please ensure API server is running:")
        print("   cd src/functions/api")
        print("   python server.py")
        print("   (Server should be running on http://localhost:9909)")
    except requests.exceptions.Timeout:
        print("❌ Request Timeout: API response time exceeded 10 minutes")
        print("💡 This might mean:")
        print("   1. test_stress.yaml is running but needs more time")
        print("   2. API server encountered a problem")
        print("   3. Test case execution time exceeded expectations")
    except Exception as e:
        print(f"❌ Request Exception: {str(e)}")
    
    print("\n" + "=" * 60)


def print_parameter_comparison():
    """Display parameter comparison table"""
    print("\n📋 Parameter Comparison Table:")
    print("+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+")
    print("| Parameter          | Default Value | Custom Value  |")
    print("+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+")
    print("| audio              | off           | on            |")
    print("| video              | on            | off           |")
    print("| send_reactions     | on            | on            |")
    print("| send_chat          | off           | on            |")
    print("| participants       | 20            | 10            |")
    print("| duration (minutes) | 3             | 2             |")
    print("+" + "-" * 20 + "+" + "-" * 15 + "+" + "-" * 15 + "+")


def test_scenarios():
    """Test different parameter scenarios"""
    print("🎯 Stress Test API - Multiple Parameter Scenario Testing")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Scenario 1: High Intensity Test",
            "params": {
                "stress_duration": 300,      # 5 minutes
                "participant_count": 30,     # 30 participants
                "enable_chat_test": True,    # Enable chat
                "enable_video": True,        # Enable video
                "enable_audio": True         # Enable audio
            }
        },
        {
            "name": "Scenario 2: Lightweight Test", 
            "params": {
                "stress_duration": 60,       # 1 minute
                "participant_count": 5,      # 5 participants
                "enable_chat_test": False,   # Disable chat
                "enable_video": False,       # Disable video
                "enable_audio": False        # Disable audio
            }
        },
        {
            "name": "Scenario 3: Chat Focused Test",
            "params": {
                "stress_duration": 180,      # 3 minutes
                "participant_count": 15,     # 15 participants
                "enable_chat_test": True,    # Enable chat
                "enable_video": False,       # Disable video
                "enable_audio": False        # Disable audio
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*20} {scenario['name']} {'='*20}")
        choice = input(f"Run {scenario['name']}? (y/n): ").lower()
        if choice == 'y':
            call_stress_api_with_params(**scenario['params'])
            if i < len(scenarios):
                input("\nPress Enter to continue to next scenario...")


if __name__ == "__main__":
    print_parameter_comparison()
    
    print("\n🎯 Select Test Mode:")
    print("1. Use default parameters (audio=on, video=off, chat=on, 10 people, 2 minutes)")
    print("2. Multiple scenario testing")
    print("3. Custom parameter testing")
    
    choice = input("Please select (1/2/3): ").strip()
    
    if choice == "1":
        # Use default parameters
        call_stress_api_with_params()
    elif choice == "2":
        # Multiple scenario testing
        test_scenarios()
    elif choice == "3":
        # Custom parameter example
        print("\n📝 Custom Parameter Example:")
        print("call_stress_api_with_params(")
        print("    stress_duration=240,       # 4 minutes")
        print("    participant_count=25,      # 25 participants") 
        print("    enable_chat_test=True,     # Enable chat")
        print("    enable_video=True,         # Enable video")
        print("    enable_audio=False         # Disable audio")
        print(")")
        
        # Example call
        call_stress_api_with_params(
            stress_duration=240,
            participant_count=25,
            enable_chat_test=True       ,
            enable_video=True,
            enable_audio=False
        )
    else:
        print("Invalid selection, running with default parameters")
        call_stress_api_with_params()           