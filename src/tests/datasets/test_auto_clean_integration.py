"""
Test script to verify auto-clean integration in datasets_generator.py
Tests that all three commands properly clean dynamic content from keys.
"""

import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from test_space.datasets.datasets_generator import clean_all_dynamic_patterns_from_key, clean_dataset_keys

def test_clean_patterns():
    """Test the cleaning function with various patterns"""
    
    test_cases = [
        # Generic patterns
        ("Audio Tree item, Selected, collapsed, Level 1", "Audio Tree item"),
        ("English, English, selected", "English, English"),
        ("German, Deutsch, not selected", "German, Deutsch"),
        ("Item 2 of 5", "Item"),
        ("Button, collapsed, Level 2, 3 of 10", "Button"),
        ("Normal Text", "Normal Text"),
        ("Text, 1 of 1", "Text"),
        ("Selected, Item", "Item"),
        
        # Date patterns (new)
        ("Wednesday, November 19, 2025 choose date", "choose date"),
        ("Today, Wednesday, November 19, 2025", "Today"),
        ("Monday, December 25, 2024 choose date", "choose date"),
        ("Today, Friday, January 1, 2026", "Today"),
        
        # Business-specific patterns (from clean_dynamic_controls.py)
        # Dynamic meeting names
        ("Invite and remind-bts tony2's meeting", "Invite and remind-Meeting window"),
        ("Mute all-John's meeting", "Mute all-Meeting window"),
        ("Close Participants (1) panel", "Close Participants panel"),
        ("Invite and remind-Participants (5) panel", "Invite and remind-Participants panel"),
        # Date patterns
        ("Wednesday, November 19, 2025 choose date", "choose date"),
        ("Today, Wednesday, November 19, 2025", "Today"),
        # URLs and links
        ("https://converged-bts.webex.com/meet/pr1234567890, Copy", "Meeting link, Copy"),
        ("Meeting link https://converged-bts.webex.com/meet/bts123 Copy meeting link", "Meeting link, Copy meeting link"),
        ("Personal Room number, 123 456 7890, Copy", "Personal Room number, Copy"),
        ("Video address, 123456789@webex.com, More information for Host PIN", "Video address, More information for Host PIN"),
        ("Activation Code, 1234-5678-9012, Copy activation code", "Activation Code, Copy activation code"),
        ("Activation Code, 1234-5678-9012, copied", "Activation Code, copied"),
        ("Meeting Duration, 45 minutes", "Meeting Duration"),
        ("Elapsed time: 59 seconds", "Elapsed time"),
        ("John Doe, Speaking, Video on, list item", "Speaking, Video on, list item"),
        ("Jane Smith, Muted, Video off, Stepped away, list item", "Muted, Video off, Stepped away, list item"),
        ("Bob Wilson, Video on, list item", "Video on, list item"),
        ("Message, You, 2:30 PM, Has hyperlinks. Hello world", "Message, You"),
        ("Settings, Menu item, selected, 3 of 8, to activate press SPACEBAR", "Settings, Menu item"),
        ("Help, Menu item, 5 of 8, to activate press SPACEBAR", "Help, Menu item"),
        ("AI Assistant, Menu item, 2 of 8, New feature available.", "AI Assistant, Menu item"),
        ("Profile, Menu item, 1 of 8", "Profile, Menu item"),
        ("Documents Tree item, Selected, expanded, 3 of 10, Level 2", "Documents Tree item"),
        ("Downloads Tree item, Selected, 5 of 12, Level 1", "Downloads Tree item"),
        ("Sharing content Tree item, 4 of 14, Level 1", "Sharing content Tree item"),
        ("General section, tree item, Level 1, 1 of 4, expanded, use Left Arrow...", "General section, tree item"),
        ("😎 emoji, list item, 11 of 14, use arrow key to navigate", "😎 emoji"),
        ("Language, combobox, English, Selected, 1 of 5", "Language, combobox"),
        ("2:30 PM, 15 of 48, not selected", "Time Slot"),
        ("Advanced settings, expanded, 3 of 8", "Advanced settings"),
        ("Notifications, collapsed,", "Notifications"),
        ("Light skin tone selected 2 of 6", "Light skin tone"),
        ("5 selected 5 of 10", "Number Option"),
        ("Participants group, 1 participant, Expanded, 1 of 1 level 1", "Participants group"),
        ("Close Participants (1) panel", "Close Participants panel"),
        ("Primary navigation menu Messaging menu item, 1 unread messages, 1 of 8, to activate press SPACEBAR", "Messaging menu item"),
        ("Some item, 3 of 10", "Some item"),
    ]
    
    print("🧪 Testing clean_all_dynamic_patterns_from_key function:")
    print("=" * 80)
    
    all_passed = True
    failed_tests = []
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = clean_all_dynamic_patterns_from_key(input_text)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✅" if passed else "❌"
        
        # Only show first 10 passed tests and all failed tests
        if not passed or i <= 10:
            print(f"{status} Test {i}:")
            print(f"   Input:    '{input_text}'")
            print(f"   Expected: '{expected}'")
            print(f"   Got:      '{result}'")
            if not passed:
                print(f"   FAILED!")
                failed_tests.append((i, input_text, expected, result))
            print()
    
    if len(test_cases) > 10 and all_passed:
        print(f"... and {len(test_cases) - 10} more tests passed ✅")
        print()
    
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {len(test_cases) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if all_passed:
        print("✅ All pattern cleaning tests passed!")
    else:
        print(f"❌ {len(failed_tests)} test(s) failed!")
        print("\nFailed tests summary:")
        for i, input_text, expected, result in failed_tests:
            print(f"  [{i}] '{input_text}' -> Expected: '{expected}', Got: '{result}'")
    print()
    
    return all_passed

def test_json_cleaning():
    """Test cleaning a JSON file"""
    
    # Create a test JSON file
    test_data = {
        "Audio Tree item, Selected, collapsed, Level 1": {"type": "tree", "value": "audio"},
        "English, English, selected": {"type": "option", "value": "en"},
        "German, Deutsch, not selected": {"type": "option", "value": "de"},
        "Item 2 of 5": {"type": "list_item", "value": "item2"},
        "Normal Button": {"type": "button", "value": "normal"},
    }
    
    expected_keys = [
        "Audio Tree item",
        "English, English",
        "German, Deutsch",
        "Item",
        "Normal Button",
    ]
    
    test_file = Path(__file__).parent / "test_clean_temp.json"
    
    print("🧪 Testing clean_dataset_keys function:")
    print("=" * 80)
    print(f"Test file: {test_file}")
    print()
    
    try:
        # Write test file
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=4)
        
        print(f"Original keys ({len(test_data)}):")
        for key in test_data.keys():
            print(f"   - '{key}'")
        print()
        
        # Clean the file
        changes_count = clean_dataset_keys(str(test_file), output_file=None, verbose=False)
        
        # Read cleaned file
        with open(test_file, 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        
        print(f"Cleaned keys ({len(cleaned_data)}):")
        for key in cleaned_data.keys():
            print(f"   - '{key}'")
        print()
        
        print(f"Changes made: {changes_count}")
        print()
        
        # Verify all expected keys are present
        all_passed = True
        for expected_key in expected_keys:
            if expected_key not in cleaned_data:
                print(f"❌ Expected key not found: '{expected_key}'")
                all_passed = False
        
        if all_passed:
            print("✅ All expected keys found in cleaned data!")
        
        print("=" * 80)
        print()
        
        return all_passed
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

def main():
    print("\n" + "=" * 80)
    print("🔍 Auto-Clean Integration Test Suite")
    print("=" * 80)
    print()
    
    # Test pattern cleaning
    pattern_test_passed = test_clean_patterns()
    
    # Test JSON file cleaning
    json_test_passed = test_json_cleaning()
    
    # Summary
    print("=" * 80)
    print("📊 Test Summary:")
    print("=" * 80)
    print(f"Pattern Cleaning: {'✅ PASSED' if pattern_test_passed else '❌ FAILED'}")
    print(f"JSON File Cleaning: {'✅ PASSED' if json_test_passed else '❌ FAILED'}")
    print("=" * 80)
    
    if pattern_test_passed and json_test_passed:
        print("✅ All tests passed! Integration ready.")
        return 0
    else:
        print("❌ Some tests failed! Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
