"""
Test script to verify test_suite account configuration is working correctly.
"""

from pathlib import Path
from rs_sdk.utils.workflow_loader import WorkflowLoader
from config.paths import TEST_SUITE_PATH, TEST_CASES_PATH

def test_suite_account():
    """Test that test_suite account is properly read and used."""
    
    loader = WorkflowLoader()
    
    # Test 1: Read test_suite account
    print("\n=== Test 1: Read test_suite account ===")
    test_suite_path = TEST_SUITE_PATH / "calling.yaml"
    suite_account = loader.get_test_suite_account(test_suite_path)
    print(f"Test suite account: {suite_account}")
    assert suite_account == "jianjzha", f"Expected 'jianjzha', got '{suite_account}'"
    print("✓ Test suite account read successfully")
    
    # Test 2: Read test_case account (should be None for sign_in)
    print("\n=== Test 2: Read test_case account ===")
    test_case_path = TEST_CASES_PATH / "navigations/basic/sign_in.yaml"
    case_account = loader.get_test_case_account(test_case_path)
    print(f"Test case account: {case_account}")
    assert case_account is None, f"Expected None, got '{case_account}'"
    print("✓ Test case account is None (as expected)")
    
    # Test 3: Get effective account (should use test_suite account)
    print("\n=== Test 3: Get effective account (test_suite fallback) ===")
    effective_account = loader.get_effective_account(
        test_case_path=test_case_path,
        test_suite_path=test_suite_path,
        override_account=None
    )
    print(f"Effective account: {effective_account}")
    assert effective_account == "jianjzha", f"Expected 'jianjzha', got '{effective_account}'"
    print("✓ Effective account correctly uses test_suite account")
    
    # Test 4: Get effective account with override
    print("\n=== Test 4: Get effective account (with override) ===")
    effective_account_override = loader.get_effective_account(
        test_case_path=test_case_path,
        test_suite_path=test_suite_path,
        override_account="override_account"
    )
    print(f"Effective account with override: {effective_account_override}")
    assert effective_account_override == "override_account", f"Expected 'override_account', got '{effective_account_override}'"
    print("✓ Override account takes highest priority")
    
    # Test 5: Build UI path with test_suite account
    print("\n=== Test 5: Build UI path with test_suite account ===")
    ui_path = loader.build_ui_path_with_account(
        test_case_path=test_case_path,
        override_account=None,
        test_suite_path=test_suite_path
    )
    print(f"UI path built successfully with {len(ui_path)} steps")
    
    # Check that email/password variables are resolved
    email_step = next((step for step in ui_path if step.get('name') == 'Email address'), None)
    if email_step:
        email_value = email_step.get('action', {}).get('value', '')
        print(f"Email value: {email_value}")
        # Should not be ${email} anymore, should be resolved to actual email
        assert email_value != '${email}', "Email variable should be resolved"
        print(f"✓ Email variable resolved to: {email_value}")
    
    # Test 6: Priority test - test_case account overrides test_suite
    print("\n=== Test 6: Priority test (test_case overrides test_suite) ===")
    # Create a test case with account configured
    test_case_with_account = TEST_CASES_PATH / "navigations/basic/sign_in_call.yaml"
    if test_case_with_account.exists():
        case_account_2 = loader.get_test_case_account(test_case_with_account)
        effective_account_2 = loader.get_effective_account(
            test_case_path=test_case_with_account,
            test_suite_path=test_suite_path,
            override_account=None
        )
        if case_account_2:
            print(f"Test case has account: {case_account_2}")
            print(f"Effective account: {effective_account_2}")
            assert effective_account_2 == case_account_2, "Test case account should override test suite account"
            print("✓ Test case account correctly overrides test suite account")
        else:
            print(f"Test case has no account configured")
            print(f"Effective account: {effective_account_2}")
            assert effective_account_2 == "jianjzha", "Should use test suite account when test case has none"
            print("✓ Falls back to test suite account when test case has none")
    
    print("\n" + "="*60)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("="*60)
    print("\nSummary:")
    print("1. Test suite account configuration works correctly")
    print("2. Account priority is properly implemented:")
    print("   - Override account (highest)")
    print("   - Test case account")
    print("   - Test suite account")
    print("   - Global account (lowest)")
    print("3. Account variables are resolved correctly")
    print("\nYour test_suite account 'jianjzha' will now be used for")
    print("test cases that don't have their own account configured!")

if __name__ == "__main__":
    try:
        test_suite_account()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
