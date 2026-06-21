#!/usr/bin/env python3
"""
Test Batch Importer for importing YAML test batch files to database
This tool imports test batch configuration files from src/test_space/test_batches
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

class TestBatchImporter:
    def __init__(self):
        """Initialize the test batch importer"""
        self.db_connection = None
        
    def connect_db(self):
        """Connect to database using get_db_connection"""
        try:
            self.db_connection = get_db_connection(TEST_CASE_DB)
            if self.db_connection:
                print(f"Successfully connected to database")
                # Create table if not exists
                self._create_table_if_not_exists()
            else:
                raise Exception("Failed to get database connection")
        except Exception as err:
            print(f"Database connection failed: {err}")
            raise
    
    def _create_table_if_not_exists(self):
        """Create TestBatches table if it doesn't exist"""
        try:
            cursor = self.db_connection.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS TestBatches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                team VARCHAR(100),
                owner VARCHAR(100),
                platform VARCHAR(50),
                languages JSON,
                test_cases JSON,
                file_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_team (team),
                INDEX idx_platform (platform)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_query)
            self.db_connection.commit()
            print("TestBatches table ensured to exist")
            
        except Exception as e:
            print(f"Error creating TestBatches table: {e}")
            raise
        finally:
            cursor.close()
            
    def disconnect_db(self):
        """Disconnect from database"""
        if self.db_connection:
            self.db_connection.close()
            print("Database connection closed")

    def _ensure_connection(self):
        """Ensure database connection exists"""
        if not self.db_connection:
            raise Exception("No database connection. Call connect_db() first.")

    def parse_test_batch_yaml(self, yaml_file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a test batch YAML file and extract information
        
        Args:
            yaml_file_path: Path to the YAML file
            
        Returns:
            Dictionary containing test batch information or None if parsing fails
        """
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file)
                
            # Support both 'test_batch' and 'test_case_batch' keys
            if not content:
                print(f"Warning: Empty YAML file {yaml_file_path}")
                return None
            
            test_batch = None
            if 'test_case_batch' in content:
                test_batch = content['test_case_batch']
            elif 'test_batch' in content:
                test_batch = content['test_batch']
            else:
                print(f"Warning: Invalid test batch format in {yaml_file_path}")
                return None
            
            # Extract required and optional fields
            batch_data = {
                'name': test_batch.get('name', ''),
                'team': test_batch.get('team', ''),
                'owner': test_batch.get('owner', ''),
                'platform': test_batch.get('platform', ''),
                'languages': test_batch.get('language', []),
                'test_cases': test_batch.get('test_cases', []),
                'file_path': str(yaml_file_path.relative_to(Path.cwd()))
            }
            
            # Validate required fields
            if not batch_data['name']:
                print(f"Warning: Test batch name is missing in {yaml_file_path}")
                return None
                
            return batch_data
            
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {yaml_file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error reading file {yaml_file_path}: {e}")
            return None

    def insert_test_batch(self, batch_data: Dict[str, Any]) -> bool:
        """
        Insert test batch data into database
        
        Args:
            batch_data: Dictionary containing test batch information
            
        Returns:
            True if successful, False otherwise
        """
        self._ensure_connection()
        
        try:
            cursor = self.db_connection.cursor()
            
            # Convert lists to JSON strings
            languages_json = json.dumps(batch_data['languages'])
            test_cases_json = json.dumps(batch_data['test_cases'])
            
            # Insert or update test batch
            query = """
            INSERT INTO TestBatches (name, team, owner, platform, languages, test_cases, file_path)
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
                batch_data['name'],
                batch_data['team'],
                batch_data['owner'],
                batch_data['platform'],
                languages_json,
                test_cases_json,
                batch_data['file_path']
            )
            
            cursor.execute(query, values)
            self.db_connection.commit()
            
            if cursor.rowcount > 0:
                print(f"✓ Imported test batch: {batch_data['name']}")
                return True
            else:
                print(f"- No changes for test batch: {batch_data['name']}")
                return True
                
        except Exception as e:
            print(f"✗ Error inserting test batch {batch_data['name']}: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()

    def import_test_batch_file(self, yaml_file_path: Path) -> bool:
        """
        Import a single test batch YAML file
        
        Args:
            yaml_file_path: Path to the YAML file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Processing: {yaml_file_path.name}")
        
        batch_data = self.parse_test_batch_yaml(yaml_file_path)
        if not batch_data:
            return False
            
        return self.insert_test_batch(batch_data)

    def import_all_test_batches(self, test_batches_dir: Path) -> Dict[str, int]:
        """
        Import all test batch YAML files from a directory
        
        Args:
            test_batches_dir: Directory containing test batch YAML files
            
        Returns:
            Dictionary with import statistics
        """
        self._ensure_connection()
        
        # Find all YAML files recursively
        yaml_files = []
        for root, dirs, files in os.walk(test_batches_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    yaml_files.append(os.path.join(root, file))
        
        if not yaml_files:
            print(f"No YAML files found in {test_batches_dir}")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        print(f"Found {len(yaml_files)} test batch files to import")
        print("=" * 50)
        
        stats = {'total': len(yaml_files), 'success': 0, 'failed': 0}
        
        for yaml_file in sorted(yaml_files):
            yaml_path = Path(yaml_file)
            if self.import_test_batch_file(yaml_path):
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        print("=" * 50)
        print(f"Import completed: {stats['success']} successful, {stats['failed']} failed")
        
        return stats

    def show_imported_test_batches(self) -> None:
        """Show all imported test batches from database"""
        self._ensure_connection()
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT name, team, owner, platform, file_path, created_at FROM TestBatches ORDER BY name")
            
            results = cursor.fetchall()
            if not results:
                print("No test batches found in database")
                return
            
            print(f"\nImported Test Batches ({len(results)} total):")
            print("-" * 80)
            print(f"{'Name':<25} {'Team':<15} {'Owner':<15} {'Platform':<10} {'File':<20}")
            print("-" * 80)
            
            for row in results:
                name, team, owner, platform, file_path, created_at = row
                file_name = Path(file_path).name if file_path else 'N/A'
                print(f"{name:<25} {team:<15} {owner:<15} {platform:<10} {file_name:<20}")
            
        except Exception as e:
            print(f"Error querying test batches: {e}")
        finally:
            cursor.close()

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import test batch YAML files to database")
    parser.add_argument(
        '--test-batches-dir',
        default='../test_batches',
        help='Test batches directory path (default: ../test_batches)'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Show imported test batches from database'
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
    test_batches_dir = Path(args.test_batches_dir)
    if not test_batches_dir.is_absolute():
        # If relative path, resolve from current working directory
        test_batches_dir = Path.cwd() / test_batches_dir
        # Fallback: if not found, try relative to script directory
        if not test_batches_dir.exists():
            test_batches_dir = current_path / args.test_batches_dir
    
    # Check if directory exists
    if not args.show and not test_batches_dir.exists():
        print(f"Error: Test batches directory does not exist: {test_batches_dir}")
        sys.exit(1)
    
    # Initialize importer
    importer = TestBatchImporter()
    
    try:
        importer.connect_db()
        
        if args.show:
            importer.show_imported_test_batches()
        else:
            # Show files to be imported
            if args.dry_run:
                yaml_files = []
                for root, dirs, files in os.walk(test_batches_dir):
                    for file in files:
                        if file.endswith('.yaml') or file.endswith('.yml'):
                            yaml_files.append(os.path.join(root, file))
                print(f"Found {len(yaml_files)} test batch files:")
                for yaml_file in sorted(yaml_files):
                    print(f"  - {Path(yaml_file).name}")
            else:
                # Import test batches
                stats = importer.import_all_test_batches(test_batches_dir)
                print(f"\nFinal results: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        importer.disconnect_db()

if __name__ == "__main__":
    main()
