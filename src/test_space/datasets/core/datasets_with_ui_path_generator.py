import os
import sys
import json

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from rs_sdk.utils.control_handler import ControlHandler
from rs_sdk.utils.control_db import ControlDB
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from config.paths import PROJECT_ROOT_PATH, CONTROL_DATASET_WITH_UI_PATH, TEST_CONTROL_DATASET_FOLDER_PATH
from pathlib import Path


class ControlUIPathGenerator:
    """
    Generate control dataset with UI path information.
    
    This class generates control data including:
    - control_name: Name of the control
    - control_id: Automation ID of the control
    - control_type: Type ID of the control
    - control_type_name: Type name of the control
    - window_name: Window name where the control is located
    - control_ui_path: UI path to navigate to the control
    """
    
    def __init__(self, datasets_path=None):
        """
        Initialize the generator with database path.
        
        Args:
            datasets_path (str): Path to the database file containing control information
        """
        # Convert relative path to absolute path based on project root
        if datasets_path is None:
            # Use the database path in test_space/datasets/data
            datasets_path = TEST_CONTROL_DATASET_FOLDER_PATH / "data" / "ControlINFO.db"
        
        # If it's a relative path, make it absolute
        if not os.path.isabs(datasets_path):
            datasets_path = str(PROJECT_ROOT_PATH / datasets_path)
        
        self.datasets_path = Path(datasets_path)
        
        if not self.datasets_path.exists():
            LOGGER_ERROR(f"Database file not found: {self.datasets_path}")
            raise FileNotFoundError(f"Database file not found: {self.datasets_path}")
        
        # Initialize ControlDB with the correct database path
        self.control_db = ControlDB(db_path=self.datasets_path)
        
        # Initialize ControlHandler and override its control_db
        self.control_handler = ControlHandler()
        self.control_handler.control_db = self.control_db
        
        LOGGER_INFO(f"Initialized ControlUIPathGenerator with database: {self.datasets_path}")
    
    def get_all_hierarchical_levels(self, control_name, control_id=None):
        """
        Get all hierarchical levels for a given control name and optionally control_id.
        
        Args:
            control_name (str): Name of the control
            control_id (str): AutomationId of the control (optional, for precise matching, can be None)
            
        Returns:
            list: List of hierarchical level strings, e.g., ['2.1.1.2.34.2.1.2.6.14.9', '2.1.1.2.34.2.1.4.4.30']
        """
        if control_id is not None:
            # If control_id is provided (even if empty string), match both name and id
            query = """
            SELECT HierarchicalLevel 
            FROM ControlINFO 
            WHERE Description = ? AND (AutomationId = ? OR (AutomationId IS NULL AND ? IS NULL))
            AND HierarchicalLevel IS NOT NULL AND HierarchicalLevel != ''
            """
            results = self.control_db._execute_query(query, (control_name, control_id, control_id))
        else:
            # Otherwise, match by name only (backward compatibility)
            query = """
            SELECT HierarchicalLevel 
            FROM ControlINFO 
            WHERE Description = ? AND HierarchicalLevel IS NOT NULL AND HierarchicalLevel != ''
            """
            results = self.control_db._execute_query(query, (control_name,))
        
        hierarchical_levels = [row[0] for row in results if row[0]]
        LOGGER_DEBUG(f"Found {len(hierarchical_levels)} hierarchical levels for control '{control_name}'" + (f" (ID: {control_id if control_id else 'NULL'})" if control_id is not None else ""))
        
        return hierarchical_levels
    
    def find_shortest_path(self, hierarchical_levels):
        """
        Find the shortest hierarchical path from a list of paths.
        If multiple paths have the same length, choose the one with smallest last element.
        
        Args:
            hierarchical_levels (list): List of hierarchical level strings
            
        Returns:
            str: The shortest hierarchical level string
        """
        if not hierarchical_levels:
            return None
        
        # Find minimum length
        min_length = min(len(x.split('.')) for x in hierarchical_levels)
        
        # Get all paths with minimum length
        shortest_paths = [x for x in hierarchical_levels if len(x.split('.')) == min_length]
        
        # If multiple shortest paths, compare by last element (smaller is better)
        if len(shortest_paths) > 1:
            def sort_key(path):
                parts = path.split('.')
                # Return tuple: (length, last_element_as_int)
                try:
                    return (len(parts), int(parts[-1]))
                except (ValueError, IndexError):
                    return (len(parts), float('inf'))
            
            shortest = min(shortest_paths, key=sort_key)
            LOGGER_DEBUG(f"Multiple shortest paths found, selected: {shortest} (last element: {shortest.split('.')[-1]})")
        else:
            shortest = shortest_paths[0]
            LOGGER_DEBUG(f"Shortest path: {shortest} (length: {len(shortest.split('.'))})")
        
        return shortest
    
    def generate_ui_path(self, hierarchical_level, start_index=None):
        """
        Generate UI path from hierarchical level.
        
        Args:
            hierarchical_level (str): Hierarchical level string, e.g., '2.1.1.2.34.2.1.4.4.30'
            start_index (int): Optional start index to slice the path. 
                              If provided, returns path starting from this index.
                              E.g., start_index=8 means starting from 8th element.
            
        Returns:
            tuple: (full_ui_path, sliced_ui_path, sliced_hierarchical_level)
                   full_ui_path: Complete UI path list
                   sliced_ui_path: UI path starting from start_index (or None)
                   sliced_hierarchical_level: Hierarchical level from start_index (or None)
        """
        if not hierarchical_level:
            return [], None, None
        
        # Get full UI path using the control_db method
        full_ui_path = self.control_db.fetch_ui_path_by_index(hierarchical_level)
        LOGGER_DEBUG(f"Full UI path for '{hierarchical_level}': {full_ui_path}")
        
        sliced_ui_path = None
        sliced_hierarchical_level = None
        
        # If start_index is provided, slice the path
        if start_index is not None and start_index > 0:
            if start_index <= len(full_ui_path):
                sliced_ui_path = full_ui_path[start_index - 1:]
                
                # Also slice the hierarchical level
                level_parts = hierarchical_level.split('.')
                if start_index <= len(level_parts):
                    sliced_hierarchical_level = '.'.join(level_parts[start_index - 1:])
                    LOGGER_DEBUG(f"Sliced UI path from index {start_index}: {sliced_ui_path}")
                    LOGGER_DEBUG(f"Sliced hierarchical level: {sliced_hierarchical_level}")
            else:
                LOGGER_WARNING(f"start_index {start_index} exceeds path length {len(full_ui_path)}")
        
        return full_ui_path, sliced_ui_path, sliced_hierarchical_level
    
    def get_control_metadata(self, control_name, control_id=None):
        """
        Get control metadata from database.
        
        Args:
            control_name (str): Name of the control
            control_id (str): AutomationId of the control (optional, for precise matching)
            
        Returns:
            dict: Control metadata including control_id, control_type, window_name, etc.
        """
        if control_id is not None:
            # If control_id is provided, match both name and id (handle NULL)
            query = """
            SELECT AutomationId, ControlType, WindowName, WindowLevel2Name, WindowAutomationId
            FROM ControlINFO 
            WHERE Description = ? AND (AutomationId = ? OR (AutomationId IS NULL AND ? IS NULL))
            LIMIT 1
            """
            results = self.control_db._execute_query(query, (control_name, control_id, control_id))
        else:
            # Otherwise, just match by name (backward compatibility)
            query = """
            SELECT AutomationId, ControlType, WindowName, WindowLevel2Name, WindowAutomationId
            FROM ControlINFO 
            WHERE Description = ?
            LIMIT 1
            """
            results = self.control_db._execute_query(query, (control_name,))
        
        if not results:
            LOGGER_WARNING(f"No metadata found for control '{control_name}'")
            return None
        
        row = results[0]
        metadata = {
            "control_id": row[0] or "",
            "control_type": row[1] or "",
            "window_name": row[2] or "",
            "window_level2_name": row[3] or "",
            "window_id": row[4] or ""
        }
        
        return metadata
    
    def get_control_type_name(self, control_type):
        """
        Map control type ID to control type name.
        
        Args:
            control_type (int or str): Control type ID
            
        Returns:
            str: Control type name
        """
        # Common UI Automation control type mappings
        control_type_map = {
            50000: "button",
            50001: "calendar",
            50002: "check_box",
            50003: "combo_box",
            50004: "edit",
            50005: "hyperlink",
            50006: "image",
            50007: "list_item",
            50008: "list",
            50009: "menu",
            50010: "menu_bar",
            50011: "menu_item",
            50012: "progress_bar",
            50013: "radio_button",
            50014: "scroll_bar",
            50015: "slider",
            50016: "spinner",
            50017: "status_bar",
            50018: "tab",
            50019: "tab_item",
            50020: "text",
            50021: "tool_bar",
            50022: "tool_tip",
            50023: "tree",
            50024: "tree_item",
            50025: "custom",
            50026: "group",
            50027: "thumb",
            50028: "data_grid",
            50029: "data_item",
            50030: "document",
            50031: "split_button",
            50032: "window",
            50033: "pane",
            50034: "header",
            50035: "header_item",
            50036: "table",
            50037: "title_bar",
            50038: "separator"
        }
        
        try:
            control_type_int = int(control_type) if control_type else 0
            return control_type_map.get(control_type_int, "custom")
        except (ValueError, TypeError):
            return "custom"
    
    def generate_control_dataset(self, control_name, start_index=None, platform="windows", control_id=None):
        """
        Generate complete control dataset with UI path information.
        
        Args:
            control_name (str): Name of the control to generate data for
            start_index (int): Optional start index for slicing UI path
            platform (str): Platform name, default is "windows"
            control_id (str): Optional AutomationId for precise matching
            
        Returns:
            dict: Complete control dataset in the required format
        """
        LOGGER_INFO(f"Generating dataset for control: '{control_name}'" + (f" (ID: {control_id})" if control_id else ""))
        
        # Step 1: Get all hierarchical levels
        hierarchical_levels = self.get_all_hierarchical_levels(control_name, control_id)
        
        if not hierarchical_levels:
            LOGGER_ERROR(f"No hierarchical levels found for control '{control_name}'")
            return None
        
        LOGGER_INFO(f"Found {len(hierarchical_levels)} hierarchical levels:")
        for idx, level in enumerate(hierarchical_levels, 1):
            LOGGER_INFO(f"  Level {idx}: {level}")
        
        # Step 2: Find shortest path
        shortest_level = self.find_shortest_path(hierarchical_levels)
        LOGGER_INFO(f"Shortest hierarchical level: {shortest_level}")
        
        # Step 3: Generate UI path
        full_ui_path, sliced_ui_path, sliced_hierarchical_level = self.generate_ui_path(
            shortest_level, start_index
        )
        
        # Step 4: Get control metadata
        metadata = self.get_control_metadata(control_name, control_id)
        
        if not metadata:
            LOGGER_ERROR(f"Failed to get metadata for control '{control_name}'")
            return None
        
        # Step 5: Get control type name
        control_type_name = self.get_control_type_name(metadata["control_type"])
        
        # Step 6: Build the dataset
        dataset = {
            "name": control_name,
            "metadata": {
                platform: {
                    "control_name": control_name,
                    "control_id": metadata["control_id"],
                    "control_type": metadata["control_type"],
                    "control_type_name": control_type_name,
                    "window_name": metadata["window_name"],
                    "window_id": metadata["window_id"],
                    "control_ui_path": full_ui_path,
                    "all_hierarchical_levels": hierarchical_levels,
                    "shortest_hierarchical_level": shortest_level
                }
            }
        }
        
        # Add sliced path information if start_index is provided
        if start_index is not None and sliced_ui_path is not None:
            dataset["metadata"][platform]["meeting_ui_path"] = sliced_ui_path
            dataset["metadata"][platform]["sliced_hierarchical_level"] = sliced_hierarchical_level
            dataset["metadata"][platform]["start_index"] = start_index
        
        LOGGER_INFO(f"Generated dataset successfully for '{control_name}'")
        
        return dataset
    
    def generate_all_datasets(self, control_items, start_index=None, platform="windows"):
        """
        Generate datasets for multiple controls.
        
        Args:
            control_items (list): List of control names (str) or (name, id) tuples
            start_index (int): Starting index for slicing the UI path
            platform (str): Platform name (default: "windows")
            
        Returns:
            list: List of control datasets
        """
        datasets = []
        
        for item in control_items:
            # Support both string names and (name, id) tuples
            if isinstance(item, tuple):
                control_name, control_id = item
                dataset = self.generate_control_dataset(control_name, start_index=start_index, platform=platform, control_id=control_id)
            else:
                dataset = self.generate_control_dataset(item, start_index=start_index, platform=platform)
            if dataset:
                datasets.append(dataset)
        
        LOGGER_INFO(f"Generated {len(datasets)} datasets out of {len(control_items)} controls")
        
        return datasets
    
    def save_to_json(self, datasets, output_file):
        """
        Save datasets to JSON file.
        
        Args:
            datasets (list): List of control datasets
            output_file (str): Output file path
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(datasets, f, ensure_ascii=False, indent=4)
            
            LOGGER_INFO(f"Saved {len(datasets)} datasets to {output_file}")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to save datasets to {output_file}: {str(e)}")
    
    def get_all_control_names(self):
        """
        Get all control name and id combinations from the database.
        Each unique (Description, AutomationId) pair is treated as a separate control.
        Includes controls even if AutomationId is NULL.
        
        Returns:
            list: List of (control_name, control_id) tuples that have HierarchicalLevel
        """
        # Query to get all controls with valid hierarchical levels
        # Now includes controls with NULL AutomationId
        query = """
        SELECT DISTINCT Description, AutomationId
        FROM ControlINFO 
        WHERE Description IS NOT NULL 
        AND Description != '' 
        AND HierarchicalLevel IS NOT NULL 
        AND HierarchicalLevel != ''
        ORDER BY Description, AutomationId
        """
        results = self.control_db._execute_query(query)
        control_items = [(row[0], row[1]) for row in results]
        
        LOGGER_INFO(f"Found {len(control_items)} unique control (name, id) combinations in database")
        
        # Additional check: Query total controls with hierarchical levels for verification
        verify_query = """
        SELECT COUNT(DISTINCT Description || '|' || COALESCE(AutomationId, 'NULL'))
        FROM ControlINFO 
        WHERE HierarchicalLevel IS NOT NULL 
        AND HierarchicalLevel != ''
        AND Description IS NOT NULL 
        """
        verify_result = self.control_db._execute_query(verify_query)
        total_count = verify_result[0][0] if verify_result else 0
        
        if total_count != len(control_items):
            LOGGER_WARNING(f"Mismatch detected: Query returned {len(control_items)} items, but total count is {total_count}")
        else:
            LOGGER_INFO(f"Verification passed: All {total_count} controls will be exported")
        
        return control_items
    
    def export_all_controls(self, output_file=None, start_index=None, platform="windows"):
        """
        Export all controls from the database to JSON file.
        
        Args:
            output_file (str): Output file path, if None will use default
            start_index (int): Optional start index for slicing UI path
            platform (str): Platform name, default is "windows"
            
        Returns:
            list: List of all control datasets
        """
        LOGGER_INFO("Starting full database export...")
        
        # Get all control (name, id) combinations
        control_items = self.get_all_control_names()
        
        if not control_items:
            LOGGER_WARNING("No controls found in database")
            return []
        
        # Generate datasets for all controls
        datasets = []
        success_count = 0
        failed_controls = []
        
        for idx, item in enumerate(control_items, 1):
            try:
                if isinstance(item, tuple):
                    control_name, control_id = item
                    LOGGER_INFO(f"Processing {idx}/{len(control_items)}: '{control_name}' (ID: {control_id})")
                    dataset = self.generate_control_dataset(control_name, start_index, platform, control_id)
                else:
                    LOGGER_INFO(f"Processing {idx}/{len(control_items)}: '{item}'")
                    dataset = self.generate_control_dataset(item, start_index, platform)
                
                if dataset:
                    datasets.append(dataset)
                    success_count += 1
                else:
                    failed_controls.append(item)
                    
            except Exception as e:
                LOGGER_ERROR(f"Failed to generate dataset for '{item}': {str(e)}")
                failed_controls.append(item)
        
        # Summary
        LOGGER_INFO(f"\n{'='*80}")
        LOGGER_INFO(f"Export Summary:")
        LOGGER_INFO(f"  Total controls: {len(control_items)}")
        LOGGER_INFO(f"  Successfully exported: {success_count}")
        LOGGER_INFO(f"  Failed: {len(failed_controls)}")
        LOGGER_INFO(f"{'='*80}")
        
        if failed_controls:
            LOGGER_WARNING(f"Failed controls: {failed_controls[:10]}")  # Show first 10
            if len(failed_controls) > 10:
                LOGGER_WARNING(f"... and {len(failed_controls) - 10} more")
        
        # Save to file
        if output_file is None:
            output_file = TEST_CONTROL_DATASET_FOLDER_PATH / "all_control_datasets.json"
        
        self.save_to_json(datasets, output_file)
        
        return datasets


def main():
    """
    Main function to demonstrate usage.
    """
    # Initialize generator
    generator = ControlUIPathGenerator()
    
    # Example 1: Generate dataset for a single control with full path
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Example 1: Generate dataset with full UI path")
    LOGGER_INFO("="*80)
    
    control_name = "Max camera resolution"
    dataset = generator.generate_control_dataset(control_name)
    
    if dataset:
        print("\nGenerated Dataset:")
        print(json.dumps(dataset, indent=4, ensure_ascii=False))
    
    # Example 2: Generate dataset with sliced path (starting from index 8)
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Example 2: Generate dataset with sliced UI path (start_index=8)")
    LOGGER_INFO("="*80)
    
    dataset_sliced = generator.generate_control_dataset(control_name, start_index=8)
    
    if dataset_sliced:
        print("\nGenerated Dataset with Sliced Path:")
        print(json.dumps(dataset_sliced, indent=4, ensure_ascii=False))
    
    # Example 3: Generate datasets for multiple controls
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Example 3: Generate datasets for multiple controls")
    LOGGER_INFO("="*80)
    
    control_names = [
        "Max camera resolution",
        " Sign in",
        "Email address"
    ]
    
    datasets = generator.generate_all_datasets(control_names, start_index=8)
    
    # Save to file
    output_file = TEST_CONTROL_DATASET_FOLDER_PATH / "generated_control_datasets.json"
    generator.save_to_json(datasets, output_file)
    
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Generation completed!")
    LOGGER_INFO("="*80)


def export_all(start_index=None):
    """
    Export all controls from database.
    
    Args:
        start_index (int): Optional start index for slicing UI path
    """
    # Initialize generator
    generator = ControlUIPathGenerator()
    
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Export All Controls from Database")
    if start_index is not None:
        LOGGER_INFO(f"Using start_index: {start_index}")
    LOGGER_INFO("="*80)
    
    # Export all controls
    output_file = CONTROL_DATASET_WITH_UI_PATH
    generator.export_all_controls(output_file=output_file, start_index=start_index)
    
    LOGGER_INFO("\n" + "="*80)
    LOGGER_INFO("Full database export completed!")
    LOGGER_INFO("="*80)


if __name__ == "__main__":
    import sys
    
    # Check if user wants to export all
    if len(sys.argv) > 1 and sys.argv[1] == "--export-all":
        # Parse optional start_index parameter
        start_index = None
        if len(sys.argv) > 3 and sys.argv[2] == "--start-index":
            try:
                start_index = int(sys.argv[3])
            except ValueError:
                LOGGER_ERROR(f"Invalid start_index value: {sys.argv[3]}")
                sys.exit(1)
        
        export_all(start_index=start_index)
    else:
        main()
