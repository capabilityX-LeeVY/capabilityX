"""
Test Data Processor for preparing and organizing test execution data.

This module is responsible for:
- Preparing test execution data based on mode (suite/case/batch)
- Resolving test case paths from database or local files
- Organizing test suites and test cases for execution
- Reading pre_conditions to determine initialization requirements
"""

import yaml
from pathlib import Path
from rs_sdk.utils.workflow_loader import WorkflowLoader
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR, LOGGER_DEBUG
from config.paths import TEST_CASES_PATH, TEST_SUITE_PATH


class TestDataProcessor:
    """Processes and prepares test data for execution."""

    def __init__(self):
        self.workflow_loader = WorkflowLoader()

    def prepare_test_execution_data(self, test_suites_or_cases, mode):
        """
        Prepare test execution data based on mode.
        
        Args:
            test_suites_or_cases (list): List of test suite names, test case names, or test batch names
            mode (str): 'case' for individual test cases, 'suite' for test suites, 'batch' for test batches
            
        Returns:
            list: Prepared test execution data
        """
        if mode == "case":
            return self._prepare_test_case_data(test_suites_or_cases)
        elif mode == "batch":
            return self._prepare_test_batch_data(test_suites_or_cases)
        else:
            return self._prepare_test_suite_data(test_suites_or_cases)

    def _prepare_test_case_data(self, test_cases):
        """Prepare individual test case data."""
        test_cases_data = []
        
        for test_case_name in test_cases:
            test_case_path_str = self._resolve_from_local_files(test_case_name)

            if test_case_path_str is None:
                continue  # Skip if test case not found

            # Read need_initialization from YAML to determine initialization requirement
            need_initialization = self._should_initialize_from_test_case(test_case_path_str)
            
            # Read check_points and custom_dataset from test case YAML
            test_case_yaml_path = TEST_CASES_PATH / f"{test_case_path_str}.yaml"
            check_points = self.workflow_loader.get_test_case_check_points(test_case_yaml_path)
            if check_points:
                LOGGER_INFO(f"Test case '{test_case_name}' has check_points: {check_points}", "CYAN")
            else:
                LOGGER_INFO(f"Test case '{test_case_name}' has no check_points, all features enabled by default", "CYAN")
            
            # Read custom_dataset from test case YAML
            custom_dataset = None
            sr_prompt = None
            try:
                with open(test_case_yaml_path, 'r', encoding='utf-8') as f:
                    test_case_config = yaml.safe_load(f)
                    if test_case_config and 'test_case' in test_case_config:
                        custom_dataset = test_case_config['test_case'].get('custom_dataset')
                        if custom_dataset:
                            LOGGER_INFO(f"Test case '{test_case_name}' uses custom_dataset: {custom_dataset}", "CYAN")
                        sr_prompt = test_case_config['test_case'].get('sr_prompt')
                        if sr_prompt:
                            LOGGER_INFO(f"Test case '{test_case_name}' uses sr_prompt: {sr_prompt}", "CYAN")
            except Exception as e:
                LOGGER_WARNING(f"Failed to read custom_dataset from {test_case_yaml_path}: {str(e)}", "YELLOW")

            message_bot = self.workflow_loader.get_test_case_message_room(test_case_yaml_path)
            if message_bot:
                LOGGER_INFO(f"Test case '{test_case_name}' has message_bot targets: {message_bot}", "CYAN")

            test_cases_data.append({
                'test_case_name': test_case_name,
                'test_case_path_str': test_case_path_str,
                'language': 'en',  # Default language for individual test cases
                'need_initialization': need_initialization,
                'check_points': check_points,  # Add check_points from test case
                'custom_dataset': custom_dataset,  # Add custom_dataset from test case
                'sr_prompt': sr_prompt,  # Add sr_prompt from test case
                'message_bot': message_bot
            })
            
        return test_cases_data

    def _prepare_test_suite_data(self, test_suites):
        """Prepare test suite data."""
        test_suites_data = []
        
        for test_suite in test_suites:
            test_suite_path = TEST_SUITE_PATH / f"{test_suite}.yaml"

            if not test_suite_path.exists():
                LOGGER_ERROR(f"Test suite file not found: {test_suite_path}", "RED")
                LOGGER_ERROR(f"Please check if test suite '{test_suite}' exists in directory: {TEST_SUITE_PATH}", "RED")
                continue

            LOGGER_INFO(f"Found test suite file: {test_suite_path}", "GREEN")

            try:
                langs = self.workflow_loader.get_test_suite_languages(test_suite_path)
                check_points = self.workflow_loader.get_test_suite_check_points(test_suite_path)

                test_suites_data.append({
                    'test_suite': test_suite,
                    'test_suite_path': test_suite_path,
                    'languages': langs,
                    'check_points': check_points
                })
            except Exception as e:
                LOGGER_ERROR(f"Failed to load test suite '{test_suite}': {str(e)}", "RED")
                continue
                
        return test_suites_data

    def _resolve_from_local_files(self, test_case_name):
        """Resolve test case path from local YAML files."""
        LOGGER_DEBUG(f"Trying to find local YAML file for test case '{test_case_name}'.", "CYAN")

        # Remove .yaml extension if present to avoid double extension
        if test_case_name.endswith('.yaml'):
            test_case_name = test_case_name[:-5]
        
        # Try to find the test case YAML file in TEST_CASES_PATH (including subdirectories)
        test_case_yaml_files = list(TEST_CASES_PATH.rglob(f"{test_case_name}.yaml"))

        if test_case_yaml_files:
            # Found at least one matching file, use the first one
            found_file = test_case_yaml_files[0]
            # Calculate relative path from TEST_CASES_PATH
            relative_path = found_file.relative_to(TEST_CASES_PATH)
            # Remove the .yaml extension to get the test case path
            test_case_path_str = str(relative_path.with_suffix(''))

            LOGGER_DEBUG(f"Found local test case file: {found_file}", "GREEN")
            LOGGER_DEBUG(f"Using test case path: {test_case_path_str}", "CYAN")

            if len(test_case_yaml_files) > 1:
                LOGGER_WARNING(f"Multiple files found for '{test_case_name}', using: {relative_path}", "YELLOW")
                
            return test_case_path_str
        else:
            # Neither database nor local file found, skip this test case
            LOGGER_DEBUG(f"Test case '{test_case_name}' not found in database or local files. please check test case directory: {TEST_CASES_PATH}.", "RED")
            return None

    def create_case_data_for_suite(self, test_case, language, test_suite_name, test_suite_path=None, check_points=None):
        """
        Create case data structure for suite execution.
        
        Args:
            test_case: Test case name
            language: Language code
            test_suite_name: Test suite name
            test_suite_path: Path to test suite YAML file (optional)
            check_points: List of enabled check points from test suite (optional)
            
        Returns:
            dict: Case data with test suite path for account resolution
        """
        # Read need_initialization from YAML to determine initialization requirement
        need_initialization = self._should_initialize_from_test_case(test_case)
        test_case_yaml_path = TEST_CASES_PATH / f"{test_case}.yaml"
        message_bot = self.workflow_loader.get_test_case_message_room(test_case_yaml_path)
        
        return {
            'test_case_name': test_case,
            'test_case_path_str': test_case,
            'language': language,
            'test_suite_name': test_suite_name,
            'test_suite_path': test_suite_path,  # Add test_suite_path for account resolution
            'need_initialization': need_initialization,
            'check_points': check_points,  # Add check_points configuration
            'message_bot': message_bot
        }

    def _should_initialize_from_test_case(self, test_case_path):
        """
        Read test case YAML file and determine if initialization is needed.
        
        Logic: Check the 'need_initialization' field in test case YAML
               - If need_initialization: false → need_initialization = False
               - If need_initialization: true or not specified → need_initialization = True (default)
        
        Args:
            test_case_path (str): Path to the test case YAML file
            
        Returns:
            bool: True if initialization is needed, False otherwise
        """
        try:
            # Convert relative path to absolute path if needed
            if not test_case_path.startswith('/') and not test_case_path.startswith('C:'):
                yaml_path = TEST_CASES_PATH / f"{test_case_path}.yaml"
            else:
                yaml_path = Path(test_case_path)
            
            if not yaml_path.exists():
                LOGGER_WARNING(f"Test case YAML file not found: {yaml_path}. Using default initialization.")
                return True  # Default to requiring initialization
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                test_case_data = yaml.safe_load(f)
            
            test_case_info = test_case_data.get('test_case', {})
            need_initialization = test_case_info.get('need_initialization')
            
            # If need_initialization is explicitly set to false, return False
            if need_initialization is False:
                LOGGER_DEBUG(f"Test case {test_case_path}: need_initialization=false, skipping initialization", "CYAN")
                return False
            else:
                # Default behavior: require initialization (True or not specified)
                LOGGER_DEBUG(f"Test case {test_case_path}: need_initialization={need_initialization} (default: true), requiring initialization", "CYAN")
                return True
                
        except Exception as e:
            LOGGER_ERROR(f"Error reading need_initialization from {test_case_path}: {e}. Using default initialization.")
            return True  # Default to requiring initialization

    def _prepare_test_batch_data(self, test_batches):
        """
        Prepare test batch data by reading batch configuration files.
        
        This method supports flexible batch file naming:
        1. First tries: {test_batch}_batch.yaml
        2. Then tries: {test_batch}.yaml
        
        Args:
            test_batches (list): List of test batch names
            
        Returns:
            list: Prepared test case data from all batch files
        """
        test_cases_data = []
        
        for test_batch in test_batches:
            batch_file_path = self._find_batch_file(test_batch)
            
            if batch_file_path is None:
                LOGGER_ERROR(f"Test batch file not found for '{test_batch}'", "RED")
                LOGGER_ERROR(f"Tried looking for: {test_batch}_batch.yaml and {test_batch}.yaml in {TEST_CASES_PATH.parent / 'test_batch'}", "RED")
                continue
                
            LOGGER_INFO(f"Found test batch file: {batch_file_path}", "GREEN")
            
            try:
                batch_cases = self._load_batch_configuration(batch_file_path, test_batch)
                test_cases_data.extend(batch_cases)
                    
            except Exception as e:
                LOGGER_ERROR(f"Failed to load test batch '{test_batch}': {str(e)}", "RED")
                continue
                
        return test_cases_data
    
    def _find_batch_file(self, test_batch):
        """
        Find batch configuration file using flexible naming convention.
        
        Supports multiple naming patterns:
        1. Direct naming: {test_batch}.yaml (if test_batch already has '_batch' suffix)
        2. Auto suffix: {test_batch}_batch.yaml (if test_batch doesn't have '_batch' suffix)
        3. Legacy: {test_batch}.yaml (fallback for compatibility)
        
        Args:
            test_batch (str): Name of the test batch
            
        Returns:
            Path: Path to the batch file or None if not found
        """
        batch_dir = TEST_CASES_PATH.parent / "test_batch"
        
        # Pattern 1: Direct naming - if test_batch already ends with '_batch', use it directly
        if test_batch.endswith('_batch'):
            batch_file_path = batch_dir / f"{test_batch}.yaml"
            if batch_file_path.exists():
                LOGGER_INFO(f"Using direct batch file naming: {batch_file_path.name}", "GREEN")
                return batch_file_path
        
        # Pattern 2: Auto suffix - try adding '_batch' suffix
        batch_file_path = batch_dir / f"{test_batch}_batch.yaml"
        if batch_file_path.exists():
            LOGGER_INFO(f"Using batch file with '_batch' suffix: {batch_file_path.name}", "CYAN")
            return batch_file_path
        
        # Pattern 3: Legacy support - try without any suffix modification
        batch_file_path = batch_dir / f"{test_batch}.yaml"
        if batch_file_path.exists():
            LOGGER_INFO(f"Using batch file with legacy naming: {batch_file_path.name}", "YELLOW")
            return batch_file_path
        
        return None
    
    def _load_batch_configuration(self, batch_file_path, test_batch):
        """
        Load and process batch configuration file.
        
        Args:
            batch_file_path (Path): Path to the batch configuration file
            test_batch (str): Name of the test batch
            
        Returns:
            list: List of prepared test case data
        """
        test_cases_data = []
        
        with open(batch_file_path, 'r', encoding='utf-8') as f:
            batch_data = yaml.safe_load(f)
        
        test_case_batch_info = batch_data.get('test_case_batch', {})
        test_cases = test_case_batch_info.get('test_cases', [])
        
        if not test_cases:
            LOGGER_WARNING(f"No test cases found in batch '{test_batch}'", "YELLOW")
            return test_cases_data
        
        LOGGER_INFO(f"Test batch '{test_batch}' contains {len(test_cases)} test cases: {test_cases}", "CYAN")
        
        # Read batch-level check_points (takes priority over individual case check_points)
        batch_check_points = test_case_batch_info.get('check_points', None)
        if batch_check_points is not None:
            LOGGER_INFO(f"Test batch '{test_batch}' has batch-level check_points: {batch_check_points}", "CYAN")
        
        # Process each test case in the batch
        for test_case_name in test_cases:
            try:
                test_case_data = self._process_batch_test_case(test_case_name, test_batch)
                if test_case_data:
                    # Batch-level check_points override individual case check_points
                    if batch_check_points is not None:
                        test_case_data['check_points'] = batch_check_points
                    test_cases_data.append(test_case_data)
            except Exception as e:
                LOGGER_ERROR(f"Failed to process test case '{test_case_name}' in batch '{test_batch}': {str(e)}", "RED")
                continue
        
        return test_cases_data
    
    def _process_batch_test_case(self, test_case_name, test_batch):
        """
        Process a single test case from batch configuration.
        
        Priority order for test case resolution:
        1. First try to find in database
        2. If not found in DB, try to find in local files
        
        Args:
            test_case_name (str): Full path of the test case (e.g., "meetings/video/vbg_static")
            test_batch (str): Name of the test batch
            
        Returns:
            dict: Test case data or None if processing failed
        """
        # Use the full path for lookup to avoid matching wrong test cases with the same filename
        # (e.g., "feature_test/Merak_Apptastic/.../guest_join_PMR_new" must not resolve to
        #  "acc_regression/promote_channel/guest_join/guest_join_PMR_new")
        test_case_path_str = self._resolve_from_local_files(test_case_name)

        if test_case_path_str is None:
            LOGGER_ERROR(f"Test case '{test_case_name}' not found in local files. Skipping.", "RED")
            return None
        
        # For batch mode, each test case is independent, so each needs initialization
        # Read the initialization requirement from the test case YAML
        need_initialization = self._should_initialize_from_test_case(test_case_path_str)
        
        # Read check_points from test case YAML if defined
        test_case_yaml_path = TEST_CASES_PATH / f"{test_case_path_str}.yaml"
        check_points = self.workflow_loader.get_test_case_check_points(test_case_yaml_path)
        message_bot = self.workflow_loader.get_test_case_message_room(test_case_yaml_path)
        if check_points:
            LOGGER_INFO(f"Test case '{test_case_name}' has check_points: {check_points}", "CYAN")
        if message_bot:
            LOGGER_INFO(f"Test case '{test_case_name}' has message_bot targets: {message_bot}", "CYAN")
        
        LOGGER_INFO(f"Processed batch test case: {test_case_name} -> {test_case_path_str} (need_init: {need_initialization})", "CYAN")
        
        return {
            'test_case_name': test_case_name,
            'test_case_path_str': test_case_path_str,
            'language': 'en',  # Default language for batch test cases
            'need_initialization': need_initialization,
            'test_batch_name': test_batch,
            'check_points': check_points,  # Add check_points from test case
            'message_bot': message_bot
        }
