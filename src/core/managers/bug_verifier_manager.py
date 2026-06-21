import re
import requests
import urllib3
from typing import Optional, Dict, List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pathlib import Path
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR, LOGGER_WARNING
from tools.Jira.jira_handler import JiraHandler


class BugVerifier:
    """veify the bug status from markdown file"""
    
    def __init__(self, report_url: str):
        """
        Initialize the Bug Verifier
        
        Args:
            report_url: URL of the report directory
        """
        self.report_url = report_url
        self.markdown_content = None
        self.test_data = {}
    
    def parse_markdown_content(self, content: str) -> Dict:
        """
        Parse Markdown content and extract test data
        
        Markdown format:
        ## Test Case: [test_case_name]
        | Test Case | Step Num | Step Name | ... | KB Navigate | Focus Ring | Screen Reader | ... |
        
        Args:
            content: Text content of the Markdown file
        
        Returns:
            Dict: Format is {test_case: {step_num: {column_name: value}}}
        """
        test_data = {}
        
        try:
            lines = content.split('\n')
            
            current_test_case = None
            header_columns = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Detect test case title: ## Test Case: [navigations/basic/sign_in]
                if line.startswith('## Test Case:'):
                    match = re.search(r'\[([^\]]+)\]', line)
                    if match:
                        current_test_case = match.group(1)
                        test_data[current_test_case] = {}
                        continue
                
                # Detect header row
                if line.startswith('|') and 'Test Case' in line and 'Step Num' in line:
                    # Parse header columns
                    header_columns = [col.strip() for col in line.split('|')[1:-1]]
                    continue
                
                # Skip separator row
                if line.startswith('|') and '---' in line:
                    continue
                
                # Parse data row
                if line.startswith('|') and current_test_case and header_columns:
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    
                    if len(cells) >= len(header_columns):
                        # Get test case name and step number
                        test_case_col = cells[0] if len(cells) > 0 else ''
                        step_num_col = cells[1] if len(cells) > 1 else ''
                        
                        # Only process data for the current test case
                        if test_case_col == current_test_case:
                            try:
                                step_num = int(step_num_col)
                            except ValueError:
                                continue
                            
                            # Create step data dictionary
                            step_data = {}
                            for col_idx, col_name in enumerate(header_columns):
                                if col_idx < len(cells):
                                    step_data[col_name] = cells[col_idx]
                            
                            test_data[current_test_case][step_num] = step_data
            
            LOGGER_INFO(f"✅ Parse Markdown {len(test_data)} successfully")
            return test_data
            
        except Exception as e:
            LOGGER_ERROR(f"❌ Prase Markdown error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def download_markdown_from_url(self) -> bool:
        """
        URL find the first .md file and parse it
        
        Returns:
            bool: donwload and prase success return True, else return False
        """
        try:
            LOGGER_INFO(f"🔍Markdown file...")
            LOGGER_INFO(f"   URL: {self.report_url}")
            
            # Check if URL already points to a .md file
            if self.report_url.endswith('.md'):
                # Direct .md file URL - download immediately
                md_url = self.report_url
                md_filename = md_url.split('/')[-1]
                # Extract directory URL for fallback raw URL attempts
                report_url = md_url.rsplit('/', 1)[0] + '/'
                LOGGER_INFO(f"✅ Direct Markdown file URL detected: {md_filename}")
            else:
                # Directory URL - search for .md files
                LOGGER_INFO(f"   Directory URL detected, searching for .md files...")
                
                # Ensure URL ends with /
                report_url = self.report_url.rstrip('/') + '/'
                
                # Get directory page
                response = requests.get(report_url, timeout=30, verify=False)
                response.raise_for_status()
                
                # Find all .md file links
                content = response.text
                md_files = re.findall(r'href=["\']([^"\']*\.md)["\']', content)
                
                if not md_files:
                    LOGGER_ERROR(f"❌ [FAILURE] No .md files found in directory")
                    return False
                
                # use the first find .md file
                md_path = md_files[0]
                # only take the filename part (remove path)
                md_filename = md_path.split('/')[-1]
                # directly concatenate URL and filename
                md_url = report_url + md_filename
                LOGGER_INFO(f"✅ Found Markdown file: {md_filename}")
            
            LOGGER_INFO(f"📥 Downloading file...")
            LOGGER_INFO(f"   URL: {md_url}")
            
            # download markdown file
            md_response = requests.get(md_url, timeout=30, verify=False)
            md_response.raise_for_status()
            
            response_text = md_response.text
            
            # Check if the returned content is HTML (instead of actual Markdown)
            if response_text.strip().startswith('<!DOCTYPE html>') or response_text.strip().startswith('<html>'):
                LOGGER_WARNING(f"⚠️  Detected HTML page returned, attempting to fetch raw Markdown content...")
                
                # Try different raw file URLs
                raw_urls_to_try = [
                    f"{md_url}?raw=true",
                    f"{md_url}?raw=1", 
                    f"{md_url}?download=1",
                    report_url + 'raw/' + md_filename,
                    md_url.replace('/navigation/', '/navigation/raw/'),
                ]
                
                markdown_found = False
                for raw_url in raw_urls_to_try:
                    LOGGER_INFO(f"   Trying Raw URL: {raw_url}")
                    try:
                        raw_response = requests.get(raw_url, timeout=30, verify=False)
                        if raw_response.status_code == 200:
                            raw_text = raw_response.text
                            if not (raw_text.strip().startswith('<!DOCTYPE html>') or raw_text.strip().startswith('<html>')):
                                self.markdown_content = raw_text
                                LOGGER_INFO(f"   ✅ Successfully fetched Raw Markdown content")
                                markdown_found = True
                                break
                    except Exception as ex:
                        LOGGER_ERROR(f"   ❌ {raw_url} failed: {ex}")
                        continue
                
                if not markdown_found:
                    LOGGER_ERROR(f"❌ [FAILURE] Unable to extract Markdown content from HTML page")
                    LOGGER_ERROR(f"   Suggestion: Please provide a direct raw file URL or API endpoint")
                    return False
            else:
                self.markdown_content = response_text
            
            if not self.markdown_content:
                LOGGER_ERROR(f"❌ [FAILURE] Markdown content is empty")
                return False
                
            LOGGER_INFO(f"✅ File downloaded successfully! Total {len(self.markdown_content.split(chr(10)))} lines")
            
            # Parse the downloaded content
            self.test_data = self.parse_markdown_content(self.markdown_content)
            
            return True
            
        except requests.exceptions.RequestException as e:
            LOGGER_ERROR(f"❌ [FAILURE] Error: Unable to download file from URL")
            LOGGER_ERROR(f"   Request error: {str(e)}")
            return False
        except Exception as e:
            LOGGER_ERROR(f"❌ [FAILURE] Error downloading Markdown file: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_bug(self, 
                   test_suite: str, 
                   test_case: str, 
                   test_step: str, 
                   bug_type: str,
                   jira_id: Optional[str] = None) -> bool:
        """
        Verify if the bug is marked as ✅
        
        Args:
            test_suite: Test suite name (e.g., "regress", "smoke") - used to locate the markdown file
            test_case: Test case name (e.g., "navigations/basic/sign_in")
            test_step: Test step (can be step number like "1" or step name like "Sign in")
            bug_type: Bug type/column name (e.g., "Focus Ring", "Screen Reader", "KB Navigate")
            jira_id: Optional JIRA issue ID (e.g., "SPARK-123456"). If provided, will auto-update JIRA status based on verification result
            
        Returns:
            bool: Returns True if the bug is marked as ✅Success or ✅ Compliant, otherwise False
        """
        try:
            # Read Markdown file data
            if not self.test_data:
                # if no data yet, download and parse it first
                if not self.download_markdown_from_url():
                    LOGGER_ERROR(f"❌ [FAILURE] Error: Unable to download or parse Markdown file")
                    return False
            
            # Locate the specific test case
            if test_case not in self.test_data:
                LOGGER_WARNING(f"❌ Warning: Test case '{test_case}' not found")
                LOGGER_INFO(f"   Available test cases: {list(self.test_data.keys())}")
                return False
            
            case_data = self.test_data[test_case]
            
            # Try to convert test_step to an integer step number
            step_num = None
            if test_step.isdigit():
                step_num = int(test_step)
            else:
                # If not a digit, try to find by step name
                for num, step_data in case_data.items():
                    if step_data.get('Step Name', '').strip() == test_step.strip():
                        step_num = num
                        break
            
            # Locate the specific test step
            if step_num is None or step_num not in case_data:
                LOGGER_WARNING(f"❌ Warning: Test step '{test_step}' not found in test case '{test_case}'")
                LOGGER_INFO(f"   Available steps: {sorted(case_data.keys())}")
                return False
            
            step_data = case_data[step_num]
            
            # Check if bug type column exists
            if bug_type not in step_data:
                LOGGER_WARNING(f"❌ Warning: Column '{bug_type}' not found in step {step_num}")
                LOGGER_INFO(f"   Available columns: {list(step_data.keys())}")
                return False
            
            status_value = step_data[bug_type]
            
            # Check if verified
            # Accepted pass marks: ✅Success, ✅ Compliant, any value starting with ✅
            is_verified = status_value.startswith('✅')
            
            if is_verified:
                LOGGER_INFO(f"✅ Bug verification passed!")
                LOGGER_INFO(f"   Test Suite: {test_suite}")
                LOGGER_INFO(f"   Test Case: {test_case}")
                LOGGER_INFO(f"   Step Number: {step_num}")
                LOGGER_INFO(f"   Step Name: {step_data.get('Step Name', 'N/A')}")
                LOGGER_INFO(f"   Verification Type: {bug_type}")
                LOGGER_INFO(f"   Status Value: {status_value}")
            else:
                LOGGER_ERROR(f"❌ Bug verification failed!")
                LOGGER_ERROR(f"   Test Suite: {test_suite}")
                LOGGER_ERROR(f"   Test Case: {test_case}")
                LOGGER_ERROR(f"   Step Number: {step_num}")
                LOGGER_ERROR(f"   Step Name: {step_data.get('Step Name', 'N/A')}")
                LOGGER_ERROR(f"   Verification Type: {bug_type}")
                LOGGER_ERROR(f"   Status Value: {status_value}")
            
            # Update JIRA bug status if jira_id is provided
            if jira_id:
                self._update_jira_bug_status(jira_id, is_verified)
            
            return is_verified
                
        except Exception as e:
            LOGGER_ERROR(f"❌ Error during verification: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_all_test_cases(self) -> List[str]:
        """
        Get all test case names
        
        Returns:
            List[str]: List of test case names
        """
        if not self.test_data:
            self.download_markdown_from_url()
        return list(self.test_data.keys())
    
    def get_test_case_steps(self, test_case: str) -> List[int]:
        """
        Get all step numbers for a given test case
        
        Args:
            test_case: Name of the test case
            
        Returns:
            List[int]: List of step numbers
        """
        if not self.test_data:
            self.download_markdown_from_url()
        
        if test_case in self.test_data:
            return sorted(self.test_data[test_case].keys())
        return []
    
    def _update_jira_bug_status(self, jira_id: str, verification_success: bool) -> None:
        """
        Update JIRA bug status based on verification result and add report URL as comment
        
        Args:
            jira_id: JIRA issue ID (e.g., 'SPARK-123456')
            verification_success: True if verification passed (✅), False otherwise
        """
        try:
            jira_handler = JiraHandler(summary=None, description=None)
            
            if verification_success:
                # Verification success: Set status to Done with resolution Fixed
                result = jira_handler.update_status_for_issue(
                    issue_id=jira_id,
                    status_name="Done",
                    resolution="Resolved"
                )
                LOGGER_INFO(f"🎯 JIRA {jira_id} status updated to Done (Resolved)")
                LOGGER_INFO(f"   Result: {result}")
                
                # Add success comment with report URL
                comment = f"✅ Bug verification passed!\n\nVerification Report: {self.report_url}"
                jira_handler.add_comments(jira_id, comment)
                LOGGER_INFO(f"📝 Added success comment with report URL to JIRA {jira_id}")
            else:
                # Verification failed: Set status to New
                result = jira_handler.update_status_for_issue(
                    issue_id=jira_id,
                    status_name="New"
                )
                LOGGER_WARNING(f"⚠️  JIRA {jira_id} status updated to New")
                LOGGER_WARNING(f"   Result: {result}")
                
                # Add failure comment with report URL
                comment = f"❌ Bug verification failed!\n\nVerification Report: {self.report_url}\n\nPlease review the test results."
                jira_handler.add_comments(jira_id, comment)
                LOGGER_WARNING(f"📝 Added failure comment with report URL to JIRA {jira_id}")
                
        except Exception as e:
            LOGGER_ERROR(f"❌ Failed to update JIRA {jira_id} status: {e}")
            import traceback
            traceback.print_exc()
