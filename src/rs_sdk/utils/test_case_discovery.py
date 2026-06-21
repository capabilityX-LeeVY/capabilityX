"""
Test Case Discovery Utility
Automatically discovers and scans test cases in test_space/test_cases directory
"""
import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Union
import yaml


class TestCaseDiscovery:
    """Utility class to discover and manage test cases"""
    
    def __init__(self, test_cases_root: Optional[Union[str, Path]] = None):
        """
        Initialize test case discovery
        
        Args:
            test_cases_root: Root directory of test cases. 
                           If None, uses default src/test_space/test_cases
        """
        if test_cases_root is None:
            # Get the src directory
            current_file = Path(__file__).resolve()
            src_dir = current_file.parent.parent.parent
            test_cases_root = src_dir / "test_space" / "test_cases"
        
        self.test_cases_root = Path(test_cases_root)
        self._test_cases_cache = None
        
    def get_all_test_cases(self, exclude_dirs: Optional[Set[str]] = None) -> List[Dict[str, str]]:
        """
        Get all test cases from test_cases directory
        
        Args:
            exclude_dirs: Set of directory names to exclude (e.g., {'agent'})
            
        Returns:
            List of test case dictionaries with name, path, and relative_path
        """
        if exclude_dirs is None:
            exclude_dirs = {'agent'}  # Default exclude agent directory
            
        test_cases = []
        
        for yaml_file in self._scan_yaml_files(self.test_cases_root, exclude_dirs):
            relative_path = yaml_file.relative_to(self.test_cases_root)
            # Convert path to test case name format (e.g., jmt/basic/start_pmr_meeting)
            test_case_name = str(relative_path.with_suffix('')).replace('\\', '/')
            
            test_cases.append({
                'name': test_case_name,
                'path': str(yaml_file),
                'relative_path': str(relative_path)
            })
            
        return test_cases
    
    def _scan_yaml_files(self, directory: Path, exclude_dirs: Set[str]) -> List[Path]:
        """
        Recursively scan for YAML files
        
        Args:
            directory: Directory to scan
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            List of Path objects for YAML files
        """
        yaml_files = []
        
        try:
            for item in directory.iterdir():
                # Skip if directory name is in exclude list
                if item.is_dir():
                    if item.name not in exclude_dirs and not item.name.startswith('.'):
                        yaml_files.extend(self._scan_yaml_files(item, exclude_dirs))
                elif item.is_file() and item.suffix.lower() in ['.yaml', '.yml']:
                    yaml_files.append(item)
        except PermissionError:
            pass  # Skip directories we can't access
            
        return yaml_files
    
    def get_test_case_info(self, test_case_name: str) -> Dict:
        """
        Get detailed information about a specific test case
        
        Args:
            test_case_name: Test case name (e.g., 'jmt/basic/start_pmr_meeting')
            
        Returns:
            Dictionary with test case details including metadata from YAML
        """
        test_case_path = self.test_cases_root / f"{test_case_name}.yaml"
        
        if not test_case_path.exists():
            # Try .yml extension
            test_case_path = self.test_cases_root / f"{test_case_name}.yml"
            
        if not test_case_path.exists():
            raise FileNotFoundError(f"Test case not found: {test_case_name}")
        
        # Read YAML metadata
        try:
            with open(test_case_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                
            test_case_data = yaml_content.get('test_case', {})
            
            return {
                'name': test_case_name,
                'path': str(test_case_path),
                'owner': test_case_data.get('owner', 'unknown'),
                'account': test_case_data.get('account', ''),
                'description': test_case_data.get('description', ''),
                'expect_result': test_case_data.get('expect_result', ''),
                'pre_conditions': test_case_data.get('pre_conditions', []),
                'steps_count': len(test_case_data.get('steps', []))
            }
        except Exception as e:
            return {
                'name': test_case_name,
                'path': str(test_case_path),
                'error': str(e)
            }
    
    def is_valid_test_case(self, test_case_name: str) -> bool:
        """
        Check if a test case exists and is valid
        
        Args:
            test_case_name: Test case name to validate
            
        Returns:
            True if test case exists
        """
        test_case_path = self.test_cases_root / f"{test_case_name}.yaml"
        
        if not test_case_path.exists():
            test_case_path = self.test_cases_root / f"{test_case_name}.yml"
            
        return test_case_path.exists()
    
    def list_test_cases_by_category(self, exclude_dirs: Optional[Set[str]] = None) -> Dict[str, List[str]]:
        """
        List test cases grouped by category (top-level directory)
        
        Args:
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            Dictionary mapping category to list of test case names
        """
        if exclude_dirs is None:
            exclude_dirs = {'agent'}
            
        categories = {}
        all_test_cases = self.get_all_test_cases(exclude_dirs)
        
        for test_case in all_test_cases:
            # Get the top-level category
            parts = test_case['name'].split('/')
            if parts:
                category = parts[0]
                if category not in categories:
                    categories[category] = []
                categories[category].append(test_case['name'])
                
        return categories
    
    def search_test_cases(self, keyword: str, exclude_dirs: Optional[Set[str]] = None) -> List[Dict[str, str]]:
        """
        Search test cases by keyword in name or path
        
        Args:
            keyword: Search keyword
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            List of matching test case dictionaries
        """
        all_test_cases = self.get_all_test_cases(exclude_dirs)
        keyword_lower = keyword.lower()
        
        return [
            tc for tc in all_test_cases 
            if keyword_lower in tc['name'].lower()
        ]


# Global discovery instance
test_case_discovery = TestCaseDiscovery()
