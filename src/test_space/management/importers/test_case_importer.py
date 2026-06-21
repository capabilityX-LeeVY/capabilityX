#!/usr/bin/env python3
"""
Test case importer for importing YAML test case files to database
"""

import os
import yaml
import json
import glob
import sys

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from pathlib import Path
from typing import Optional

# Add path to find the database handler
import sys
current_path = Path(__file__).parent
test_space_path = current_path.parent.parent
src_path = test_space_path.parent
sys.path.insert(0, str(test_space_path))
sys.path.insert(0, str(src_path))  # For db.handlers and config modules

from db.handlers import get_db_connection
from config.config import TEST_CASE_DB

class TestCaseImporter:
    def __init__(self):
        """Initialize the importer"""
        self.db_connection = None
        
    def connect_db(self):
        """Connect to database using get_db_connection"""
        try:
            self.db_connection = get_db_connection(TEST_CASE_DB)
            if self.db_connection:
                print(f"Successfully connected to database")
            else:
                raise Exception("Failed to get database connection")
        except Exception as err:
            print(f"Database connection failed: {err}")
            raise
            
    def disconnect_db(self):
        """Disconnect from database"""
        if self.db_connection:
            self.db_connection.close()
            print("Database connection closed")

    def _ensure_connection(self):
        """Ensure database connection exists"""
        if not self.db_connection:
            raise Exception("Database not connected, please call connect_db() first")
        # Type assertion to help static analysis
        assert self.db_connection is not None
            
    def test_case_exists(self, name, module_path):
        """Check if test case already exists"""
        self._ensure_connection()
        assert self.db_connection is not None  # Type assertion for static analysis
        cursor = self.db_connection.cursor()
        query = "SELECT id FROM TestCase WHERE name = %s AND module_path = %s"
        cursor.execute(query, (name, module_path))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
        
    def insert_test_case(self, test_case_data, module_path):
        """Insert test case main table data"""
        self._ensure_connection()
        test_case = test_case_data['test_case']
        
        # Check if already exists
        existing_id = self.test_case_exists(test_case['name'], module_path)
        if existing_id:
            print(f"Test case already exists, skipping: {test_case['name']} (ID: {existing_id})")
            return existing_id
            
        cursor = self.db_connection.cursor()  # type: ignore
        
        # Insert main table data
        insert_query = """
        INSERT INTO TestCase (name, team, owner, description, expect_result, 
                             execution_duration, execution_count, module_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            test_case['name'],
            test_case.get('team', ''),
            test_case.get('owner', ''),
            test_case.get('description', ''),  # Note: keeping original typo from YAML
            test_case.get('expect_result', ''),
            test_case.get('execution_duration', 0),
            test_case.get('execution_count', 0),
            module_path
        )
        
        cursor.execute(insert_query, values)
        testcase_id = cursor.lastrowid
        
        print(f"Inserted new test case: {test_case['name']} (ID: {testcase_id})")
        
        cursor.close()
        return testcase_id
        
    def insert_pre_conditions(self, testcase_id, pre_conditions):
        """Insert pre-conditions"""
        if not pre_conditions:
            return
            
        self._ensure_connection()
        cursor = self.db_connection.cursor()  # type: ignore
        
        for condition in pre_conditions:
            insert_query = "INSERT INTO PreCondition (testcase_id, condition_text) VALUES (%s, %s)"
            cursor.execute(insert_query, (testcase_id, condition))
            
        cursor.close()
        
    def insert_post_conditions(self, testcase_id, post_conditions):
        """Insert post-conditions"""
        if not post_conditions:
            return
            
        self._ensure_connection()
        cursor = self.db_connection.cursor()  # type: ignore
        
        for condition in post_conditions:
            insert_query = "INSERT INTO PostCondition (testcase_id, condition_text) VALUES (%s, %s)"
            cursor.execute(insert_query, (testcase_id, condition))
            
        cursor.close()
        
    def insert_steps(self, testcase_id, steps):
        """Insert step data"""
        if not steps:
            return
            
        self._ensure_connection()
        cursor = self.db_connection.cursor()  # type: ignore
        
        for i, step in enumerate(steps):
            # Insert step
            step_query = """
            INSERT INTO Step (testcase_id, name, action_type, action_value, 
                             expect_state, step_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            action = step.get('action', {})
            step_values = (
                testcase_id,
                step.get('name', ''),
                action.get('type', ''),
                action.get('value', ''),
                step.get('expect_state', ''),
                i + 1
            )
            
            cursor.execute(step_query, step_values)
            step_id = cursor.lastrowid
            
            # Insert AI check (if exists)
            if 'ai_check' in step:
                ai_check = step['ai_check']
                ai_query = "INSERT INTO AICheck (step_id, prompt, reference) VALUES (%s, %s, %s)"
                ai_values = (
                    step_id,
                    ai_check.get('prompt', ''),
                    ai_check.get('reference', '')
                )
                cursor.execute(ai_query, ai_values)
                
        cursor.close()
        
    def insert_check_points(self, testcase_id, check_points):
        """Insert check points"""
        if not check_points:
            return
            
        self._ensure_connection()
        cursor = self.db_connection.cursor()  # type: ignore
        
        for point in check_points:
            insert_query = "INSERT INTO CheckPoint (testcase_id, point) VALUES (%s, %s)"
            cursor.execute(insert_query, (testcase_id, point))
            
        cursor.close()
        
    def process_yaml_file(self, yaml_file_path):
        """Process a single YAML file"""
        try:
            self._ensure_connection()
            with open(yaml_file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data or 'test_case' not in data:
                print(f"Skipping invalid YAML file: {yaml_file_path}")
                return
                
            # Get module path relative to test_cases directory  
            workspace_root = Path(__file__).parent.parent.parent
            test_cases_dir = workspace_root / "test_space" / "test_cases"
            # Resolve paths to handle any relative components like '..'
            test_cases_dir = test_cases_dir.resolve()
            yaml_path = Path(yaml_file_path).resolve()
            
            try:
                relative_path = yaml_path.relative_to(test_cases_dir)
                # Get directory path only (without filename)
                module_path = str(relative_path.parent).replace('\\', '/')
                # Handle case where file is directly in test_cases root
                if module_path == '.':
                    module_path = ''
            except ValueError:
                # If cannot calculate relative path, try to extract meaningful path
                yaml_path_str = str(yaml_path)
                if 'test_cases' in yaml_path_str:
                    # Extract path after 'test_cases'
                    parts = yaml_path_str.split('test_cases')
                    if len(parts) > 1:
                        after_test_cases = parts[1].strip('/\\')
                        module_path = str(Path(after_test_cases).parent).replace('\\', '/')
                        if module_path == '.':
                            module_path = ''
                    else:
                        module_path = ''
                else:
                    module_path = ''
            
            # Insert test case
            testcase_id = self.insert_test_case(data, module_path)
            
            test_case = data['test_case']
            
            # Insert related data
            self.insert_pre_conditions(testcase_id, test_case.get('pre_conditions'))
            self.insert_post_conditions(testcase_id, test_case.get('post_conditions'))
            self.insert_steps(testcase_id, test_case.get('steps'))
            self.insert_check_points(testcase_id, test_case.get('check_point'))
            
            # Commit transaction
            self.db_connection.commit()  # type: ignore
            
        except Exception as e:
            print(f"Error processing file {yaml_file_path}: {e}")
            if self.db_connection:
                self.db_connection.rollback()
                
    def import_all_test_cases(self, test_cases_dir):
        """Import all test cases"""
        yaml_pattern = os.path.join(test_cases_dir, "**", "*.yaml")
        yaml_files = glob.glob(yaml_pattern, recursive=True)
        
        print(f"Found {len(yaml_files)} YAML files")
        
        for yaml_file in yaml_files:
            print(f"Processing file: {yaml_file}")
            self.process_yaml_file(yaml_file)
            
        print("Import completed!")

def main():
    """Main function"""
    # Configuration paths
    current_dir = Path(__file__).parent
    test_cases_dir = current_dir.parent / "test_cases"
    
    # Create importer (no need for db_config_path anymore)
    importer = TestCaseImporter()
    
    try:
        # Connect to database
        importer.connect_db()
        
        # Import test cases
        importer.import_all_test_cases(test_cases_dir)
        
    except Exception as e:
        print(f"Error during import process: {e}")
        
    finally:
        # Disconnect database
        importer.disconnect_db()

if __name__ == "__main__":
    main()
