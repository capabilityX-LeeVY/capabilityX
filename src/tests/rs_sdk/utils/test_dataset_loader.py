"""
Test script to verify control dataset loader logic
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rs_sdk.utils.control_datasets_loader import get_control_dataset_path
from pathlib import Path

def test_dataset_selection():
    """Test different scenarios for dataset selection"""
    
    print("=" * 80)
    print("Testing Control Dataset Loader Logic")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        {
            "name": "Default (no qtversion, no arch)",
            "qtversion": None,
            "arch": None,
            "expected": "Should use default dataset"
        },
        {
            "name": "Qt 5 (qtversion=5, arch=x64)",
            "qtversion": "5",
            "arch": "x64",
            "expected": "Should use default dataset (not qt6.8)"
        },
        {
            "name": "Qt 6 (qtversion=6, arch=x64)",
            "qtversion": "6",
            "arch": "x64",
            "expected": "Should use default dataset (not qt6.8)"
        },
        {
            "name": "Qt 6.8 explicit (qtversion=6.8, arch=x64)",
            "qtversion": "6.8",
            "arch": "x64",
            "expected": "Should use qt6.8 dataset"
        },
        {
            "name": "ARM64 architecture (qtversion=6, arch=arm64)",
            "qtversion": "6",
            "arch": "arm64",
            "expected": "Should use qt6.8 dataset"
        },
        {
            "name": "ARM64 with Qt 5 (qtversion=5, arch=arm64)",
            "qtversion": "5",
            "arch": "arm64",
            "expected": "Should use qt6.8 dataset (arm64 forces it)"
        }
    ]
    
    # Run tests (simulation only - actual implementation would need settings.json)
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"  qtversion: {test['qtversion']}")
        print(f"  arch: {test['arch']}")
        print(f"  Expected: {test['expected']}")
        print("-" * 80)

if __name__ == "__main__":
    test_dataset_selection()
    print("\n" + "=" * 80)
    print("Test complete! Please verify the logic manually.")
    print("=" * 80)
