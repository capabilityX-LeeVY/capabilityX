#!/usr/bin/env python3
"""
Test Suite Importer for importing YAML test suite files to database
This tool imports test suite configuration files from src/test_space/test_suites
"""

import os
import yaml
import json
import glob
import sys
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from pathlib import Path
from typing import Optional, List, Dict, Any

# Add src directory to Python path
current_path = Path(__file__).parent
src_path = current_path.parent.parent.parent
sys.path.insert(0, str(src_path))

# Add test_space path to find db handler
test_space_path = current_path.parent.parent
sys.path.insert(0, str(test_space_path))

from db.handlers import get_db_connection
from config.config import TEST_CASE_DB

class TestSuiteImporter:
    def __init__(self):
        """Initialize the test suite importer"""
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
            raise Exception("No database connection. Call connect_db() first.")

    def parse_test_suite_yaml(self, yaml_file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a test suite YAML file and extract information
        
        Args:
            yaml_file_path: Path to the YAML file
            
        Returns:
            Dictionary containing test suite information or None if parsing fails
        """
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file)
                
            if not content or 'test_suite' not in content:
                print(f"Warning: Invalid test suite format in {yaml_file_path}")
                return None
                
            test_suite = content['test_suite']
            
            # Extract required and optional fields
            suite_data = {
                'name': test_suite.get('name', ''),
                'team': test_suite.get('team', ''),
                'owner': test_suite.get('owner', ''),
                'platform': test_suite.get('platform', ''),
                'languages': test_suite.get('language', []),
                'test_cases': test_suite.get('test_cases', []),
                'file_path': str(yaml_file_path.relative_to(Path.cwd()))
            }
            
            # Validate required fields
            if not suite_data['name']:
                print(f"Warning: Test suite name is missing in {yaml_file_path}")
                return None
                
            return suite_data
            
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {yaml_file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error reading file {yaml_file_path}: {e}")
            return None

    def insert_test_suite(self, suite_data: Dict[str, Any]) -> bool:
        """
        Insert test suite data into database
        
        Args:
            suite_data: Dictionary containing test suite information
            
        Returns:
            True if successful, False otherwise
        """
        self._ensure_connection()
        
        try:
            cursor = self.db_connection.cursor() # type: ignore
            
            # Convert lists to JSON strings
            languages_json = json.dumps(suite_data['languages'])
            test_cases_json = json.dumps(suite_data['test_cases'])
            
            # Insert or update test suite
            query = """
            INSERT INTO TestSuites (name, team, owner, platform, languages, test_cases, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                team = VALUES(team),
                owner = VALUES(owner),
                platform = VALUES(platform),
                languages = VALUES(languages),
                test_cases = VALUES(test_cases),
                file_path = VALUES(file_path),
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                suite_data['name'],
                suite_data['team'],
                suite_data['owner'],
                suite_data['platform'],
                languages_json,
                test_cases_json,
                suite_data['file_path']
            )
            
            cursor.execute(query, values)
            self.db_connection.commit() # type: ignore
            
            if cursor.rowcount > 0:
                print(f"✓ Imported test suite: {suite_data['name']}")
                return True
            else:
                print(f"- No changes for test suite: {suite_data['name']}")
                return True
                
        except Exception as e:
            print(f"✗ Error inserting test suite {suite_data['name']}: {e}")
            self.db_connection.rollback() # type: ignore
            return False
        finally:
            cursor.close()

    def import_test_suite_file(self, yaml_file_path: Path) -> bool:
        """
        Import a single test suite YAML file
        
        Args:
            yaml_file_path: Path to the YAML file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Processing: {yaml_file_path.name}")
        
        suite_data = self.parse_test_suite_yaml(yaml_file_path)
        if not suite_data:
            return False
            
        return self.insert_test_suite(suite_data)

    def import_all_test_suites(self, test_suites_dir: Path) -> Dict[str, int]:
        """
        Import all test suite YAML files from a directory
        
        Args:
            test_suites_dir: Directory containing test suite YAML files
            
        Returns:
            Dictionary with import statistics
        """
        self._ensure_connection()
        
        # Find all YAML files
        yaml_pattern = os.path.join(test_suites_dir, "*.yaml")
        yaml_files = glob.glob(yaml_pattern)
        
        if not yaml_files:
            print(f"No YAML files found in {test_suites_dir}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        print(f"Found {len(yaml_files)} test suite files to import")
        print("=" * 50)
        
        stats = {'total': len(yaml_files), 'success': 0, 'failed': 0}
        
        for yaml_file in sorted(yaml_files):
            yaml_path = Path(yaml_file)
            if self.import_test_suite_file(yaml_path):
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        print("=" * 50)
        print(f"Import completed: {stats['success']} successful, {stats['failed']} failed")
        
        return stats

    def show_imported_test_suites(self) -> None:
        """Show all imported test suites from database"""
        self._ensure_connection()
        
        try:
            cursor = self.db_connection.cursor() # type: ignore
            cursor.execute("SELECT name, team, owner, platform, file_path, created_at FROM TestSuites ORDER BY name")
            
            results = cursor.fetchall()
            if not results:
                print("No test suites found in database")
                return
            
            print(f"\nImported Test Suites ({len(results)} total):")
            print("-" * 80)
            print(f"{'Name':<25} {'Team':<15} {'Owner':<15} {'Platform':<10} {'File':<20}")
            print("-" * 80)
            
            for row in results:
                name, team, owner, platform, file_path, created_at = row
                file_name = Path(file_path).name if file_path else 'N/A'
                print(f"{name:<25} {team:<15} {owner:<15} {platform:<10} {file_name:<20}")
            
        except Exception as e:
            print(f"Error querying test suites: {e}")
        finally:
            cursor.close()

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import test suite YAML files to database")
    parser.add_argument(
        '--test-suites-dir',
        default='../test_suites',
        help='Test suites directory path (default: ../test_suites)'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Show imported test suites from database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only show files to be imported, don\'t actually import'
    )
    
    args = parser.parse_args()
    
    # Get current script directory
    current_path = Path(__file__).parent
    
    # Convert to absolute path
    test_suites_dir = Path(args.test_suites_dir)
    if not test_suites_dir.is_absolute():
        test_suites_dir = current_path / test_suites_dir
    
    # Check if directory exists
    if not args.show and not test_suites_dir.exists():
        print(f"Error: Test suites directory does not exist: {test_suites_dir}")
        sys.exit(1)
    
    # Initialize importer
    importer = TestSuiteImporter()
    
    try:
        importer.connect_db()
        
        if args.show:
            importer.show_imported_test_suites()
        else:
            # Show files to be imported
            if args.dry_run:
                yaml_pattern = os.path.join(test_suites_dir, "*.yaml")
                yaml_files = glob.glob(yaml_pattern)
                print(f"Found {len(yaml_files)} test suite files:")
                for yaml_file in sorted(yaml_files):
                    print(f"  - {Path(yaml_file).name}")
            else:
                # Import test suites
                stats = importer.import_all_test_suites(test_suites_dir)
                print(f"\nFinal results: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        importer.disconnect_db()

if __name__ == "__main__":
    main()
