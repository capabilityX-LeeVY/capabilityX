# Database Manager Tool

Unified database management tool that integrates test case import and database cleanup functionality.

## Feature Overview

This tool provides the following features:
1. **Import Operations** - Import test cases and test suites from YAML files
2. **Database Cleanup** - Support both fast and safe cleanup modes
3. **Structure Verification** - Verify database table structure integrity
4. **Statistics** - Display current database record statistics
5. **Complete Reset** - One-click cleanup, reset, and import

## Basic Usage

```bash
# Display database statistics (default operation)
python db_manager.py
python db_manager.py stats

# Verify database structure
python db_manager.py verify

# Preview import files (without actual import)
python db_manager.py import --dry-run

# Import test cases and test suites
python db_manager.py import

# Clean database (fast mode, default)
python db_manager.py clean

# Clean database (safe mode)
python db_manager.py clean --safe

# Reset auto-increment IDs
python db_manager.py reset

# Complete reset (clean + reset + import)
python db_manager.py full-reset
```

## Advanced Usage

### Import Options

```bash
# Import only test cases
python db_manager.py import --cases-only

# Import only test suites
python db_manager.py import --suites-only

# Specify custom paths
python db_manager.py import --test-cases /path/to/cases --test-suites /path/to/suites

# Show imported test suites
python db_manager.py import --show-suites

# Force execution, skip confirmations
python db_manager.py import --force
```

### Cleanup Options

```bash
# Fast cleanup (use TRUNCATE, handle foreign key constraints)
python db_manager.py clean --fast

# Safe cleanup (use DELETE, dependency order)
python db_manager.py clean --safe

# Force cleanup, skip confirmations
python db_manager.py clean --force
```

### Complete Reset Options

```bash
# Complete reset of all data, import only test cases
python db_manager.py full-reset --cases-only

# Complete reset, use safe cleanup mode
python db_manager.py full-reset --safe

# Complete reset, skip all confirmations
python db_manager.py full-reset --force
```

## Operation Instructions

### Database Cleanup Modes

1. **Fast Mode (--fast)**
   - Uses `TRUNCATE TABLE` commands
   - Temporarily disables foreign key constraint checks
   - Faster speed, suitable for development environments
   - Default mode

2. **Safe Mode (--safe)**
   - Uses `DELETE FROM` commands
   - Cleans tables in dependency order
   - Safer, suitable for production environments
   - Requires explicit `--safe` parameter

### Table Cleanup Order

The tool cleans tables in the following order (child tables first):

1. AICheck
2. CheckPoint
3. PostCondition
4. PreCondition
5. Step
6. TestCase
7. TestSuites

### Error Handling

- Automatically exits when database connection fails
- Automatically rolls back transactions on operation failure
- Ensures foreign key constraints are re-enabled after cleanup operation failure

## Example Scenarios

### Daily Development
```bash
# Check current status
python db_manager.py stats

# Clean and re-import
python db_manager.py clean --force
python db_manager.py import --force
```

### Complete Reset

```bash
# One-click reset of all data
python db_manager.py full-reset --force
```

### Import Only New Test Suites

```bash
# Import only test suites, don't affect test cases
python db_manager.py import --suites-only
```

### Solve Foreign Key Constraint Issues

```bash
# Use fast mode cleanup (automatically handle foreign key constraints)
python db_manager.py clean --fast
```

## Migration Notes

This tool integrates the original two separate tools:

- `import_tool.py` - Import functionality
- `db_cleaner.py` - Database cleanup functionality

All features from the old tools have been integrated into `db_manager.py`, providing better user experience and error handling.

## Technical Details

- Supports MySQL database
- Automatically handles foreign key constraints
- Supports transaction rollback
- Provides detailed operation feedback
- Supports batch and individual operations
- Compatible with existing YAML test file formats

## Help Information

Use the `--help` parameter to view complete help information:

```bash
python db_manager.py --help
```
