import os
import sys
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
from core.managers.bug_verifier_manager import BugVerifier

report_url = "https://wrs.qa.webex.com/report/46.2.0/Dell-XPS15-Inteli9-Utral-High_72RX2D3/20251208-160929/report/navigation"

verifier = BugVerifier(report_url)

print("="*80)
print("🔍 Bug 验证工具 - 从 URL 下载并解析 MD 文件")
print("="*80)

# Example 1: Verify the Focus Ring of step 1 in navigations/basic/sign_in
print("\nExample 1: 验证 navigations/basic/sign_in 第 1 步的 Focus Ring")
print("-" * 80)
is_verified = verifier.verify_bug(
    test_suite="video_vbg",
    test_case="navigations/basic/sign_in",
    test_step="1",
    bug_type="Focus Ring"
)
print(f"结果: {'✅ 通过' if is_verified else '❌ 失败'}")

# Example 2: Verify using step name
# print("\nExample 2: 验证 navigations/basic/sign_in 的 'Sign in' 步骤的 Screen Reader")
# print("-" * 80)
# is_verified = verifier.verify_bug(
#     test_suite="regress",
#     test_case="navigations/basic/sign_in",
#     test_step="Sign in",
#     bug_type="Screen Reader"
# )
# print(f"结果: {'✅ 通过' if is_verified else '❌ 失败'}")

# # Example 3: Get all test cases
# print("\nExample 3: 所有测试用例")
# print("-" * 80)
# test_cases = verifier.get_all_test_cases()
# for tc in test_cases:
#     print(f"  - {tc}")

# print("\n" + "="*80)
