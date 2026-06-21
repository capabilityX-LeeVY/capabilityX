"""
Test JIRA Comment Operations

This test file contains tests for JIRA comment operations including:
- Adding comments
- Getting comments
- Deleting comments

Usage:
    python src/tests/tools/Jira/test_jira_comments.py
"""

import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from tools.Jira.jira_handler import JiraHandler


def test_add_comment():
    """Test adding a comment to JIRA issue"""
    print("\n" + "=" * 60)
    print("🧪 Test 1: Adding a comment")
    print("=" * 60)
    
    test_jira_id = input("Enter JIRA ID to test (e.g., SPARK-123456): ").strip()
    
    if not test_jira_id:
        print("❌ No JIRA ID provided. Test cancelled.")
        return None
    
    try:
        comment_body = "🧪 Test comment added by automated test script."
        JiraHandler.add_comments(test_jira_id, comment_body)
        print(f"✅ Successfully added comment to {test_jira_id}")
        return test_jira_id
    except Exception as e:
        print(f"❌ Failed to add comment: {e}")
        return None


def test_get_comments(jira_id):
    """Test getting all comments from JIRA issue"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Getting all comments")
    print("=" * 60)
    
    try:
        comments = JiraHandler.get_comments(jira_id)
        
        if not comments:
            print(f"⚠️  No comments found in {jira_id}")
            return None
        
        print(f"✅ Found {len(comments)} comment(s) in {jira_id}:")
        print("-" * 60)
        
        test_comment_id = None
        for i, comment in enumerate(comments, 1):
            print(f"\nComment #{i}:")
            print(f"  ID: {comment['id']}")
            print(f"  Author: {comment['author']}")
            print(f"  Created: {comment['created']}")
            print(f"  Body: {comment['body'][:80]}...")
            
            # Find our test comment
            if "🧪 Test comment added by automated test script" in comment['body']:
                test_comment_id = comment['id']
                print(f"  >>> This is our test comment! <<<")
        
        return test_comment_id
        
    except Exception as e:
        print(f"❌ Failed to get comments: {e}")
        return None


def test_delete_comment(jira_id, comment_id):
    """Test deleting a comment from JIRA issue"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Deleting a comment")
    print("=" * 60)
    
    if not comment_id:
        print("❌ No comment ID provided. Cannot test deletion.")
        return False
    
    print(f"Comment ID to delete: {comment_id}")
    confirmation = input("Proceed with deletion? (yes/no): ").strip().lower()
    
    if confirmation != 'yes':
        print("❌ Deletion cancelled by user.")
        return False
    
    try:
        success = JiraHandler.delete_comment(jira_id, comment_id)
        
        if success:
            print(f"✅ Successfully deleted comment {comment_id} from {jira_id}")
            return True
        else:
            print(f"❌ Failed to delete comment {comment_id}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to delete comment: {e}")
        return False


def test_verify_deletion(jira_id, deleted_comment_id):
    """Verify that the comment was actually deleted"""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Verifying deletion")
    print("=" * 60)
    
    try:
        # Wait a moment for JIRA to process the deletion
        time.sleep(2)
        
        comments = JiraHandler.get_comments(jira_id)
        
        # Check if the deleted comment still exists
        still_exists = any(c['id'] == deleted_comment_id for c in comments)
        
        if still_exists:
            print(f"⚠️  Warning: Comment {deleted_comment_id} still exists in {jira_id}!")
            return False
        else:
            print(f"✅ Comment {deleted_comment_id} successfully removed from {jira_id}!")
            print(f"   Current comment count: {len(comments)}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to verify deletion: {e}")
        return False


def run_all_tests():
    """Run all comment operation tests"""
    print("\n" + "=" * 60)
    print("🚀 Starting JIRA Comment Operations Test Suite")
    print("=" * 60)
    
    # Test 1: Add a comment
    jira_id = test_add_comment()
    if not jira_id:
        print("\n❌ Test suite aborted: Failed to add comment")
        return
    
    # Wait a moment for JIRA to process
    time.sleep(2)
    
    # Test 2: Get all comments
    comment_id = test_get_comments(jira_id)
    if not comment_id:
        print("\n⚠️  Warning: Could not find the test comment we just added.")
        print("   You can still manually test deletion with a known comment ID.")
        
        manual_id = input("\nEnter comment ID to test deletion (or press Enter to skip): ").strip()
        if manual_id:
            comment_id = manual_id
        else:
            print("\n❌ Test suite completed with warnings")
            return
    
    # Test 3: Delete the comment
    deleted = test_delete_comment(jira_id, comment_id)
    if not deleted:
        print("\n❌ Test suite completed with failures")
        return
    
    # Test 4: Verify deletion
    verified = test_verify_deletion(jira_id, comment_id)
    
    # Summary
    print("\n" + "=" * 60)
    if verified:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️  Tests completed with warnings")
    print("=" * 60)


if __name__ == "__main__":
    # run_all_tests()
    # test_get_comments("SPARK-715622")
    test_delete_comment("SPARK-715622", "8377981")