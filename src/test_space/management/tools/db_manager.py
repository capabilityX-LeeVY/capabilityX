#!/usr/bin/env python3
"""
Database Manager Tool
Comprehensive database management tool for test cases and test suites.

This tool provides unified operations for:
1. Import test cases and test suites from YAML files
2. Clean and reset database tables with foreign key handling
3. Database structure verification and data statistics
4. Complete database lifecycle management

Usage:
python db_manager.py [operation] [options]

Operations:
import               Import YAML files to database
clean                Clean database tables
reset                Reset auto-increment IDs
verify               Verify database structure
stats                Show database statistics
full-reset           Complete cleanup (clean + reset + import)

Import Options:
--test-cases PATH    Specify test cases directory path (default: ../../test_cases)
--test-suites PATH   Specify test suites directory path (default: ../../test_suites)
--suites-only       Only import test suites, skip test cases
--cases-only        Only import test cases, skip test suites
--dry-run           Only show files to be imported, don't actually import
--show-suites       Show imported test suites from database

Clean Options:
--fast              Use TRUNCATE with FK handling (faster, default)
--safe              Use DELETE with dependency order (safer for production)

Global Options:
--force             Skip confirmation prompts
--help              Show help information

Examples:
python db_manager.py stats                    # Show current database status
python db_manager.py import --dry-run         # Preview import without executing
python db_manager.py clean --fast             # Quick database cleanup
python db_manager.py full-reset --force       # Complete database reset
python db_manager.py import --cases-only      # Import only test cases
python db_manager.py verify                   # Verify database structure
"""

import argparse
import sys
import os
from pathlib import Path

# Add necessary paths for modules
current_path = Path(__file__).parent
test_space_path = current_path.parent.parent
src_path = test_space_path.parent
sys.path.insert(0, str(src_path))  # For common, config modules
sys.path.insert(0, str(test_space_path))  # For management, db modules

from management.importers.test_case_importer import TestCaseImporter
from management.importers.test_suite_importer import TestSuiteImporter
from db.handlers import get_db_connection
from config.config import TEST_CASE_DB

class DatabaseManager:
    def __init__(self):
        """Initialize the database manager"""
        self.db_connection = None
        
        # Tables in dependency order (child tables first)
        self.tables = [
            'AICheck',
            'CheckPoint', 
            'PostCondition',
            'PreCondition',
            'Step',
            'TestCase',
            'TestSuites'
        ]
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.db_connection = get_db_connection(TEST_CASE_DB)
            if self.db_connection:
                print("✓ Database connection successful")
                return True
            else:
                print("✗ Database connection failed")
                return False
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def disconnect_db(self):
        """Disconnect from database"""
        try:
            if self.db_connection:
                self.db_connection.close()
                print("✓ Database connection closed")
        except Exception as e:
            print(f"Warning: Error closing database connection: {e}")
    
    # ===================== DATABASE STATISTICS =====================
    
    def show_table_counts(self):
        """Show current record counts for all tables"""
        print("\n=== Database Statistics ===")
        assert self.db_connection is not None
        cursor = self.db_connection.cursor()
        
        total_records = 0
        for table in self.tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                total_records += count
                print(f"{table:15}: {count:>6} records")
            except Exception as e:
                print(f"{table:15}: Error - {e}")
        
        cursor.close()
        print(f"{'Total':15}: {total_records:>6} records")
        print()
    
    def verify_table_structure(self):
        """Verify that all required tables exist"""
        print("\n=== Database Structure Verification ===")
        assert self.db_connection is not None
        cursor = self.db_connection.cursor()
        
        missing_tables = []
        for table in self.tables:
            try:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                result = cursor.fetchone()
                if result:
                    print(f"✓ {table}")
                else:
                    print(f"✗ {table} - NOT FOUND")
                    missing_tables.append(table)
            except Exception as e:
                print(f"✗ {table} - Error: {e}")
                missing_tables.append(table)
        
        cursor.close()
        
        if missing_tables:
            print(f"\n⚠ Warning: Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("\n✓ All tables found")
            return True
    
    # ===================== DATABASE CLEANUP =====================
    
    def clear_database_safe(self):
        """Clear database using DELETE with proper order (safer for production)"""
        print("\n=== Clearing Database (Safe Mode) ===")
        assert self.db_connection is not None
        cursor = self.db_connection.cursor()
        
        try:
            for table in self.tables:
                print(f"Clearing {table}...")
                cursor.execute(f"DELETE FROM {table}")
                affected_rows = cursor.rowcount
                print(f"  → Deleted {affected_rows} records")
            
            self.db_connection.commit()
            print("✓ Database cleared successfully (safe mode)")
            return True
            
        except Exception as e:
            self.db_connection.rollback()
            print(f"✗ Error clearing database: {e}")
            return False
        finally:
            cursor.close()
    
    def clear_database_fast(self):
        """Clear database using TRUNCATE with foreign key handling (faster)"""
        print("\n=== Clearing Database (Fast Mode) ===")
        assert self.db_connection is not None
        cursor = self.db_connection.cursor()
        
        try:
            print("Disabling foreign key checks...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            for table in self.tables:
                print(f"Truncating {table}...")
                cursor.execute(f"TRUNCATE TABLE {table}")
            
            print("Re-enabling foreign key checks...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            self.db_connection.commit()
            print("✓ Database cleared successfully (fast mode)")
            return True
            
        except Exception as e:
            self.db_connection.rollback()
            try:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                self.db_connection.commit()
            except:
                pass
            print(f"✗ Error clearing database: {e}")
            return False
        finally:
            cursor.close()
    
    def reset_auto_increment(self):
        """Reset auto-increment IDs for all tables"""
        print("\n=== Resetting Auto-Increment IDs ===")
        assert self.db_connection is not None
        cursor = self.db_connection.cursor()
        
        try:
            for table in self.tables:
                print(f"Resetting {table} auto-increment...")
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
            
            self.db_connection.commit()
            print("✓ Auto-increment IDs reset successfully")
            return True
            
        except Exception as e:
            self.db_connection.rollback()
            print(f"✗ Error resetting auto-increment: {e}")
            return False
        finally:
            cursor.close()
    
    # ===================== IMPORT OPERATIONS =====================
    
    def show_files_to_import(self, test_cases_dir):
        """Show list of test case files to be imported"""
        import glob
        
        yaml_pattern = os.path.join(test_cases_dir, "**", "*.yaml")
        yaml_files = glob.glob(yaml_pattern, recursive=True)
        
        print(f"Found {len(yaml_files)} test case YAML files:")
        for yaml_file in sorted(yaml_files):
            relative_path = Path(yaml_file).relative_to(test_cases_dir)
            print(f"  - {relative_path}")
        
        return yaml_files
    
    def show_test_suites_to_import(self, test_suites_dir):
        """Show list of test suite files to be imported"""
        import glob
        
        yaml_pattern = os.path.join(test_suites_dir, "*.yaml")
        yaml_files = glob.glob(yaml_pattern)
        
        print(f"Found {len(yaml_files)} test suite YAML files:")
        for yaml_file in sorted(yaml_files):
            relative_path = Path(yaml_file).relative_to(test_suites_dir)
            print(f"  - {relative_path}")
        
        return yaml_files
    
    def import_data(self, test_cases_dir, test_suites_dir, import_test_cases=True, import_test_suites=True, dry_run=False):
        """Import test cases and test suites"""
        print("\n=== Import Operation ===")
        
        # Show files to be imported
        yaml_files = []
        suite_files = []
        
        if import_test_cases:
            print("Scanning test case files...")
            yaml_files = self.show_files_to_import(test_cases_dir)
            print()
        
        if import_test_suites:
            print("Scanning test suite files...")
            suite_files = self.show_test_suites_to_import(test_suites_dir)
            print()
        
        if not yaml_files and not suite_files:
            print("No YAML files found to import")
            return False
        
        if dry_run:
            print("Dry run mode - no data will be actually imported")
            return True
        
        # Execute imports
        print("Starting import...")
        
        try:
            if import_test_cases and yaml_files:
                print("\n--- Importing Test Cases ---")
                case_importer = TestCaseImporter()
                case_importer.connect_db()
                case_importer.import_all_test_cases(test_cases_dir)
                case_importer.disconnect_db()
            
            if import_test_suites and suite_files:
                print("\n--- Importing Test Suites ---")
                suite_importer = TestSuiteImporter()
                suite_importer.connect_db()
                stats = suite_importer.import_all_test_suites(test_suites_dir)
                suite_importer.disconnect_db()
                print(f"Test suite import stats: {stats}")
            
            print("\n✓ All imports completed!")
            return True
            
        except Exception as e:
            print(f"✗ Import failed: {e}")
            return False
    
    def show_imported_test_suites(self):
        """Show imported test suites"""
        try:
            suite_importer = TestSuiteImporter()
            suite_importer.connect_db()
            suite_importer.show_imported_test_suites()
            suite_importer.disconnect_db()
            return True
        except Exception as e:
            print(f"Error showing test suites: {e}")
            return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Database Manager - Unified tool for test case database operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Main operation (positional argument)
    parser.add_argument(
        'operation',
        nargs='?',
        choices=['import', 'clean', 'reset', 'verify', 'stats', 'full-reset'],
        default='stats',
        help='Operation to perform (default: stats)'
    )
    
    # Import options
    parser.add_argument(
        '--test-cases',
        default='../../test_cases', 
        help='Test cases directory path (default: ../../test_cases)'
    )
    
    parser.add_argument(
        '--test-suites',
        default='../../test_suites',
        help='Test suites directory path (default: ../../test_suites)'
    )
    
    parser.add_argument(
        '--suites-only',
        action='store_true',
        help='Only import test suites, skip test cases'
    )
    
    parser.add_argument(
        '--cases-only',
        action='store_true',
        help='Only import test cases, skip test suites'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only show files to be imported, don\'t actually import'
    )
    
    parser.add_argument(
        '--show-suites',
        action='store_true',
        help='Show imported test suites from database'
    )
    
    # Clean options
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Use TRUNCATE with FK handling (faster, default for clean)'
    )
    
    parser.add_argument(
        '--safe',
        action='store_true',
        help='Use DELETE with dependency order (safer for production)'
    )
    
    # Global options
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create manager instance
    manager = DatabaseManager()
    
    # Connect to database
    if not manager.connect_db():
        print("Failed to connect to database. Please check configuration.")
        sys.exit(1)
    
    try:
        operation = args.operation
        
        if operation == 'stats':
            manager.show_table_counts()
        
        elif operation == 'verify':
            manager.verify_table_structure()
        
        elif operation == 'clean':
            # Show current state
            manager.show_table_counts()
            
            # Confirmation
            if not args.force:
                response = input("⚠ This will delete ALL data. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            # Choose clean method
            if args.safe:
                success = manager.clear_database_safe()
            else:
                success = manager.clear_database_fast()
            
            if success:
                manager.show_table_counts()
        
        elif operation == 'reset':
            if not args.force:
                response = input("Reset auto-increment IDs? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            manager.reset_auto_increment()
        
        elif operation == 'import':
            # Handle special case: show suites
            if args.show_suites:
                manager.show_imported_test_suites()
                return
            
            # Prepare paths
            test_cases_dir = Path(args.test_cases)
            if not test_cases_dir.is_absolute():
                test_cases_dir = current_path / test_cases_dir
                
            test_suites_dir = Path(args.test_suites)
            if not test_suites_dir.is_absolute():
                test_suites_dir = current_path / test_suites_dir
            
            # Check directories exist
            import_test_cases = not args.suites_only
            import_test_suites = not args.cases_only
            
            if import_test_cases and not test_cases_dir.exists():
                print(f"Error: Test cases directory does not exist: {test_cases_dir}")
                sys.exit(1)
                
            if import_test_suites and not test_suites_dir.exists():
                print(f"Error: Test suites directory does not exist: {test_suites_dir}")
                sys.exit(1)
            
            # Import data
            success = manager.import_data(
                test_cases_dir, test_suites_dir, 
                import_test_cases, import_test_suites, 
                args.dry_run
            )
            
            # Confirm import if not dry run
            if success and not args.dry_run and not args.force:
                response = input("Confirm importing files to database? (y/N): ")
                if response.lower() != 'y':
                    print("Import cancelled")
                    return
            
        elif operation == 'full-reset':
            # Show current state
            manager.show_table_counts()
            
            # Confirmation
            if not args.force:
                response = input("⚠ This will delete ALL data, reset IDs, and import fresh data. Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            # Step 1: Clean database
            print("\n🗑️ Step 1: Cleaning database...")
            if args.safe:
                success = manager.clear_database_safe()
            else:
                success = manager.clear_database_fast()
            
            if not success:
                print("Full reset failed at cleaning step")
                return
            
            # Step 2: Reset IDs
            print("\n🔄 Step 2: Resetting auto-increment IDs...")
            success = manager.reset_auto_increment()
            
            if not success:
                print("Full reset failed at reset IDs step")
                return
            
            # Step 3: Import data
            print("\n📥 Step 3: Importing fresh data...")
            test_cases_dir = Path(args.test_cases)
            if not test_cases_dir.is_absolute():
                test_cases_dir = current_path / test_cases_dir
                
            test_suites_dir = Path(args.test_suites)
            if not test_suites_dir.is_absolute():
                test_suites_dir = current_path / test_suites_dir
            
            import_test_cases = not args.suites_only
            import_test_suites = not args.cases_only
            
            success = manager.import_data(
                test_cases_dir, test_suites_dir, 
                import_test_cases, import_test_suites, 
                False  # Not dry run
            )
            
            if success:
                print("\n🎉 Full reset completed successfully!")
                manager.show_table_counts()
            else:
                print("Full reset failed at import step")
        
        else:
            print(f"Unknown operation: {operation}")
            sys.exit(1)
    
    finally:
        manager.disconnect_db()

if __name__ == "__main__":
    main()
