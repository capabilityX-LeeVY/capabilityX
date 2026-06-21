import os
import json
import sqlite3
import re
import base64
from common.utils.logger import LOGGER_INFO

class ControlDatasetsGenerator:
    def __init__(self):
        pass

    def generate_control_metadata(self, db_path, output_json_path, custom_path, dataset_path):
        # Generate base metadata from database
        self.generate_control_metadata_from_dataset(db_path, output_json_path)
        
        # Clean up names and handle special cases
        self.refine_control_metadata(output_json_path, output_json_path)

        # Merge with custom metadata and save to final path
        self.append_custom_metadata(output_json_path, custom_path, dataset_path)



        LOGGER_INFO(f"Final control datasets saved to: {dataset_path}")

    def generate_control_metadata_from_dataset(self, db_path, output_json_path, use_key_value_format=True):
        """
        Generate control metadata from database
        
        Args:
            db_path (str): Path to the database file
            output_json_path (str): Path to save the output JSON
            use_key_value_format (bool): If True, use key-value format. If False, use array format.
        """
        exclude_from_control = (
            "Start", " Apply", "Back", " Back", "Pop in panel", "Show meeting controls (Ctrl + Shift + H)",
            "Stop recording", "Resume recording", "Save", " Done", " Back to sharing settings", "Connect",
            "Meeting, Lock meeting, Toggle button, off, 1 of 10", "Open whiteboard for all", "Close whiteboard",
            " Cancel", " Discard", "Page tab list. Use left/right arrow key to navigate, Everyone",
            "Page tab list. Use left/right arrow key to navigate, Files content tab. To activate press space bar",
            "Back to meeting", "Layout, Grid view", "Stop annotation", "Stop sharing (Ctrl + Shift + Z)"
        )
        exclude_automation_id = ("DisclaimerWidget.contentContainer.DisclaimerContentView.textWidget",)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to join ControlINFO with ControlActionHistory to get image data
        # Also get WindowName and WindowAutomationId
        cursor.execute(f"""
            SELECT DISTINCT 
                ci."Description", 
                ci."AutomationId", 
                ci."ControlType", 
                ci."ControlLocalizedType",
                cah."Image",
                ci."WindowName",
                ci."WindowAutomationId"
            FROM "ControlINFO" ci
            LEFT JOIN "ControlActionHistory" cah 
                ON ci."Description" = cah."Description" 
                AND ci."AutomationId" = cah."AutomationId"
            WHERE ci."Description" IS NOT NULL
              AND TRIM(ci."Description") != ''
              AND (ci."FromControl" IS NULL OR ci."FromControl" NOT IN ({','.join(['?']*len(exclude_from_control))}))
              AND (ci."AutomationId" IS NULL OR ci."AutomationId" NOT IN ({','.join(['?']*len(exclude_automation_id))}))
        """, exclude_from_control + exclude_automation_id)

        result = []
        for desc, auto_id, control_type, control_type_name, image_blob, window_name, window_id in cursor.fetchall():
            # Strip leading and trailing spaces from the name only, keep control_name original
            cleaned_name = desc.strip() if desc else desc
            
            # Create metadata entry with image if available
            metadata_entry = {
                "control_name": desc,  # Keep original control_name with spaces
                "control_id": auto_id,
                "control_type": control_type,  # Control type ID from ControlType
                "control_type_name": control_type_name,  # Localized control type name from ControlLocalizedType
                "window_name": window_name if window_name else None,
                "window_id": window_id if window_id else None
            }
            
            # Add image field if image data exists
            if image_blob is not None:
                # Convert BLOB to base64 string for JSON storage
                metadata_entry["image"] = base64.b64encode(image_blob).decode('utf-8')
            
            entry = {
                "name": cleaned_name,
                "metadata": {
                    "windows": metadata_entry
                }
            }
            result.append(entry)

        conn.close()

        # Convert to key-value format if requested
        if use_key_value_format:
            result_dict = {}
            for entry in result:
                name = entry.pop("name")
                result_dict[name] = entry
            output_data = result_dict
            LOGGER_INFO(f"Using key-value format (dict)")
        else:
            output_data = result
            LOGGER_INFO(f"Using array format (list)")

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        LOGGER_INFO(f"Generated: {output_json_path}, total: {len(result)}")

    def append_custom_metadata(self, base_path, custom_path, output_path=None):
        with open(base_path, "r", encoding="utf-8") as f:
            base_data = json.load(f)
        with open(custom_path, "r", encoding="utf-8") as f:
            custom_data = json.load(f)

        # Create a dictionary to merge data by name
        merged_dict = {}
        
        # Add base data - use exact name matching (case-sensitive)
        for entry in base_data:
            name = entry["name"].strip() if entry["name"] else entry["name"]
            entry["name"] = name  # Update the entry with cleaned name
            # Use name as key directly to preserve case sensitivity
            merged_dict[name] = entry
        
        # Merge or add custom data - use exact name matching (case-sensitive)
        for custom_entry in custom_data:
            name = custom_entry["name"].strip() if custom_entry["name"] else custom_entry["name"]
            custom_entry["name"] = name  # Update the custom entry with cleaned name
            # Use exact name matching to distinguish "Sign in" from "Sign In"
            if name in merged_dict:
                # Merge metadata for existing name
                existing_metadata = merged_dict[name]["metadata"]
                custom_metadata = custom_entry["metadata"]
                
                # If custom has platform structure, merge platforms
                if any(platform in custom_metadata for platform in ["windows", "mac", "linux"]):
                    # Convert existing metadata to platform structure if needed
                    if not any(platform in existing_metadata for platform in ["windows", "mac", "linux"]):
                        # Convert old format to new platform format
                        old_metadata = existing_metadata.copy()
                        existing_metadata.clear()
                        existing_metadata["windows"] = old_metadata
                    
                    # Merge platform-specific metadata
                    for platform, platform_data in custom_metadata.items():
                        existing_metadata[platform] = platform_data
                else:
                    # Old format, merge directly
                    existing_metadata.update(custom_metadata)
            else:
                # Add new entry
                merged_dict[name] = custom_entry
        
        # Convert back to list
        merged_data = list(merged_dict.values())

        save_path = output_path if output_path else base_path
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)

        LOGGER_INFO(f"Merged {len(custom_data)} records from {custom_path} with {len(base_data)} base records to {save_path}")
        LOGGER_INFO(f"Total entries in merged file: {len(merged_data)}")


    def refine_control_metadata(self, input_path, output_path):
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            if "name" in entry:
                name = entry["name"].strip()
                
                # rule 1: Strip "Tree item Selected X of Y" pattern
                # Example: "Level 1 General Tree item Selected 1 of 15" -> "Level 1 General"
                if re.search(r"\s+Tree item Selected \d+ of \d+$", name, re.IGNORECASE):
                    original_name = name
                    name = re.sub(r"\s+Tree item Selected \d+ of \d+$", "", name, flags=re.IGNORECASE).strip()
                    LOGGER_INFO(f"Cleaned tree item pattern: '{original_name}' -> '{name}'")
                
                # rule 2: Strip numbers and "of" from names (like "Control name, X of Y")
                elif re.search(r", \d+ of \d+", name):
                    match = re.match(r"^([^,]+)", name)
                    if match:
                        name = match.group(1).strip()
                
                entry["name"] = name

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        LOGGER_INFO(f"Stripped spaces and handled special names in 'name', saved to: {output_path}")

    def build_ui_path_by_name(self, control_name, json_path, platform="windows"):
        """
        Build UI path by name. Since hierarchical_level is no longer generated,
        this method will return empty results for newly generated metadata.
        This method is kept for backward compatibility with existing data.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            controls = json.load(f)

        level_to_name = {}
        name_to_level = {}
        for item in controls:
            name = item.get("name")
            metadata = item.get("metadata", {})
            
            # Handle both old and new platform-specific format
            if platform in metadata:
                level = metadata[platform].get("hierarchical_level")
            else:
                level = metadata.get("hierarchical_level")
                
            if name and level:
                level_to_name[level] = name
                name_to_level[name] = level

        result = []
        for item in controls:
            if item.get("name") == control_name:
                metadata = item.get("metadata", {})
                
                # Handle both old and new platform-specific format
                if platform in metadata:
                    level = metadata[platform].get("hierarchical_level")
                else:
                    level = metadata.get("hierarchical_level")
                    
                if not level:
                    # No hierarchical_level found (expected for new format)
                    LOGGER_INFO(f"No hierarchical_level found for '{control_name}' - this is expected for newly generated metadata")
                    continue
                parts = level.split('.')
                path_levels = []
                for i in range(1, len(parts)+1):
                    path_levels.append('.'.join(parts[:i]))
                ui_path = []
                for lvl in path_levels:
                    name = level_to_name.get(lvl)
                    if name:
                        ui_path.append(name)
                result.append(ui_path)
        LOGGER_INFO(f"Found {len(result)} UI paths for control name '{control_name}' on platform '{platform}'")
        return result
    