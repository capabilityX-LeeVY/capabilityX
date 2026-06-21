import sqlite3
import pandas as pd
import os
import pymysql

from config.config import CONTROL_DB
from config.paths import DB_FOLDER, DB_PATH, SETTINGS_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from db.handlers import get_db_connection
from common.handler.settingsHandler import DynamicConfig

class ControlDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_db_connection(self):
        return get_db_connection(CONTROL_DB)

    def _execute_query(self, query, params=(), commit=False):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall() if not commit else None
            if commit:
                conn.commit()
            conn.close()
            return results if results is not None else []
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def _execute_query_as_df(self, query, params=()):
        '''Execute a query and return the result as a pandas DataFrame.'''
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            print(f"Database error: {e}")
            return pd.DataFrame()
        
    def db_initializer(self):
        if not self.db_path.exists():
            os.makedirs(DB_FOLDER, exist_ok=True)
        self._reset_control_info()
        self._reset_control_action_history()

    def reset_control_image_dataset(self):
        self._reset_control_action_history()

    def _delete_control_info(self):
        delete_data_query = 'DELETE FROM ControlINFO'
        reset_autoincrement_query = 'DELETE FROM sqlite_sequence WHERE name="ControlINFO"'
        self._execute_query(delete_data_query, commit=True)
        self._execute_query(reset_autoincrement_query, commit=True)

    def _reset_control_info(self):
        drop_table_query = 'DROP TABLE IF EXISTS ControlINFO'
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS ControlINFO (
            TabOrder INTEGER PRIMARY KEY AUTOINCREMENT,
            ReportId TEXT,
            Description TEXT,
            Level INTEGER,
            FromControl TEXT,
            HierarchicalLevel TEXT,
            Rule TEXT,
            control_path_hash TEXT,
            control_id_hash TEXT,
            RuntimeId TEXT,
            is_validated INTEGER DEFAULT 0,
            WindowName TEXT, 
            WindowAutomationId TEXT,
            WindowType INTEGER,
            WindowLevel2Name TEXT, 
            WindowLevel2AutomationId TEXT,
            WindowLevel2Type INTEGER,
            Parent TEXT,
            ParentType INTEGER,
            Pre TEXT,
            Next TEXT,
            ControlLocalizedType TEXT,
            ControlType INTEGER,
            ToggleState TEXT,
            AutomationId TEXT,
            FullDescription TEXT,
            AccessKey TEXT,
            AppVersion TEXT,
            Workflow TEXT,
            Language TEXT,
            QtVersion TEXT,
            Arch TEXT,
            JenkinsJob TEXT,
            MachineName TEXT,
            BoundingRectangles TEXT,          
            ClassName TEXT,
            Action TEXT,
            LegacyValue TEXT,
            CollapseState TEXT,
            IsEnabled INTEGER,
            IsKeyboardFocusable INTEGER,
            HasKeyboardFocus INTEGER,
            HelpText TEXT,
            LegacyRole INTEGER,
            LegacyState INTEGER,
            Image BLOB,
            PreControlImage BLOB,
            WindowImage BLOB,
            ProcessID INTEGER,
            ProcessName TEXT,
            ProjectID INTEGER,
            keyboardAction TEXT,
            Ancestors TEXT,
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
        )
        '''
        self._execute_query(drop_table_query, commit=True)
        self._execute_query(create_table_query, commit=True)

    def _reset_control_action_history(self):
        drop_table_query = 'DROP TABLE IF EXISTS ControlActionHistory'
        create_table_query = '''
        CREATE TABLE ControlActionHistory (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Description TEXT,
            ControlType TEXT,
            AutomationId TEXT,
            ImageName TEXT,
            Image BLOB,
            PreControlImage BLOB,
            WindowImage BLOB,
            ImageHash TEXT,
            Created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self._execute_query(drop_table_query, commit=True)
        self._execute_query(create_table_query, commit=True)

    def clean_control_info_db(self):
        self._delete_invalid_control()
    
    def _delete_invalid_control(self):
        """
        Delete all rows from ControlINFO where the Description column is empty or null,
        then optionally reset the autoincrement.
        """
        delete_data_query = 'DELETE FROM "ControlINFO" WHERE "Description" IS NULL OR TRIM("Description") = ""'
        self._execute_query(delete_data_query, commit=True)


    def fetch_all_control_hashes(self):
        query = 'SELECT DISTINCT "control_path_hash" FROM "ControlINFO"'
        results = self._execute_query(query)
        return [row[0] for row in results] if results else []

    def fetch_control_level_by_name(self, description):
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))
    
    def fetch_control_level_by_name_prefix(self, prefix):
        """Fetch all distinct FromControl values based on the prefix where Level > 1."""
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "Description" LIKE ?'
        return self._execute_query(query, (f'{prefix}%',))
    
    def fetch_control_level_by_name_prefix_and_id(self, prefix, control_id):
        """Fetch all distinct FromControl values based on the prefix where Level > 1."""
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "Description" LIKE ? AND "AutomationId" = ?'
        return self._execute_query(query, (f'{prefix}%',control_id,))

    def fetch_control_level_by_runtime_id(self, runtime_id):
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "RuntimeId" = ?'
        return self._execute_query(query, (runtime_id,)) 

    def fetch_runtime_id_by_control_id(self, control_id):
        """Fetch the RuntimeId based on the control_id."""
        query = 'SELECT DISTINCT "RuntimeId" FROM "ControlINFO" WHERE "AutomationId" = ?'
        return self._execute_query(query, (control_id,))               
    
    def fetch_control_level2_window_name(self, description):
        """Fetch all distinct WindowLevel2Name values based on the description."""
        query = 'SELECT DISTINCT "WindowLevel2Name" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,)) 
    
    def fetch_control_automation_id_by_name(self, description):
        """Fetch all distinct AutomationId values based on the description."""
        query = 'SELECT DISTINCT "AutomationId" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))

    def fetch_control_name_by_id(self, control_id):
        """Fetch all distinct ControlName values based on the control_id."""
        query = 'SELECT DISTINCT "Description" FROM "ControlINFO" WHERE "AutomationId" = ?'
        return self._execute_query(query, (control_id,))

    def fetch_control_toggle_state_by_control_path_hash(self, control_path_hash):
        """Fetch all distinct toggle state values based on the control path hash."""
        query = 'SELECT "ToggleState" FROM "ControlINFO" WHERE "control_path_hash" = ?'
        return self._execute_query(query, (control_path_hash,)) 
    
    def fetch_from_control_name(self, description):
        """Fetch all distinct FromControl values based on the description where Level > 1."""
        query = 'SELECT DISTINCT "FromControl" FROM "ControlINFO" WHERE "Description" = ? AND "Level" > 1'
        return self._execute_query(query, (description,))
    
    def fetch_process_id_by_contorl_name(self, description):
        """Fetch all distinct ProcessID values based on the description."""
        query = 'SELECT DISTINCT "ProcessID" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))
    
    def fetch_root_process_id(self):
        """Fetch all distinct ProcessID values based on the description."""
        query = 'SELECT DISTINCT "ProcessID" FROM "ControlINFO" WHERE "Level" = 1'
        return self._execute_query(query)
    
    def fetch_control_level_by_id_hash(self, control_id_hash):
        """Fetch the distinct Level based on the control_id_hash."""
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "control_id_hash" = ?'
        return self._execute_query(query, (control_id_hash,)) 
    
    def fetch_control_level_by_control_id(self, control_id):
        """Fetch the distinct Level based on the control_id."""
        query = 'SELECT DISTINCT "Level" FROM "ControlINFO" WHERE "AutomationId" = ?'
        return self._execute_query(query, (control_id,)) 

    def fetch_control_is_validated(self, description):
        """Fetch the distinct is_validated status based on the description."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,)) 
    
    def fetch_control_is_validated_by_control_id(self, control_id):
        """Fetch the distinct is_validated status based on the control_id."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "AutomationId" = ?'
        return self._execute_query(query, (control_id,)) 
    
    def fetch_control_is_validated_prefix(self, description):
        """Fetch the distinct is_validated status based on the description."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "Description" LIKE ?'
        return self._execute_query(query, (f'{description}%',))
    
    def fetch_control_is_validated_by_runtime_id(self, runtime_id):
        """Fetch the distinct is_validated status based on the description."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "RuntimeId" = ?'
        return self._execute_query(query, (runtime_id,)) 
    
    def fetch_control_is_validated_by_control_path_hash(self, control_path_hash):
        """Fetch the distinct is_validated status based on the control_path_hash."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "control_path_hash" = ?'
        return self._execute_query(query, (control_path_hash,)) 
    
    def fetch_control_type_by_name(self, description):
        """Fetch the distinct ControlType based on the description."""
        query = 'SELECT DISTINCT "ControlType" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,)) 
    
    def fetch_control_window_name_by_name(self, description):
        """Fetch the distinct WindowName based on the description."""
        query = 'SELECT DISTINCT "WindowName" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))

    def fetch_control_window_automation_id_by_control_name(self, description):
        """Fetch the distinct WindowAutomationId based on the description."""
        query = 'SELECT DISTINCT "WindowAutomationId" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))

    def fetch_control_name_by_window(self, window_name):
        query = 'SELECT DISTINCT "Description" FROM "ControlINFO" WHERE "WindowName" = ?'
        return self._execute_query(query, (window_name,)) 
    
    def fetch_control_id_hash_by_name(self, description):
        """Fetch the distinct control_id_hash based on the description."""
        query = 'SELECT DISTINCT "control_id_hash" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,))
    
    def fetch_is_validated_by_window_name(self, window_name):
        """Fetch the distinct is_validated status based on the WindowName."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "WindowName" = ?'
        return self._execute_query(query, (window_name,))
    
    def fetch_control_is_validated_by_window_level2(self, window_name):
        """Fetch the distinct is_validated values based on WindowLevel2Name."""
        query = 'SELECT DISTINCT "is_validated" FROM "ControlINFO" WHERE "WindowLevel2Name" = ?'
        return self._execute_query(query, (window_name,))
    
    def fetch_control_window_name_by_control_id_hash(self, control_id_hash):
        """Fetch the distinct WindowName based on the control_id_hash."""
        query = 'SELECT DISTINCT "WindowName" FROM "ControlINFO" WHERE "control_id_hash" = ?'
        return self._execute_query(query, (control_id_hash,))
    
    def fetch_control_level2_window_name_by_control_id_hash(self, control_id_hash):
        """Fetch the distinct WindowLevel2Name based on the control_id_hash."""
        query = 'SELECT DISTINCT "WindowLevel2Name" FROM "ControlINFO" WHERE "control_id_hash" = ?'
        return self._execute_query(query, (control_id_hash,))
    
    # def fetch_control_image(self):
    #     """Fetch all data from the ControlINFO table."""
    #     query = 'SELECT * FROM "ControlINFO"'
    #     df = self._execute_query_as_df(query)
    #     return df

    def fetch_control_history(self):
        """Fetch all data from the ControlActionHistory table."""
        query = 'SELECT * FROM "ControlActionHistory"'
        df = self._execute_query_as_df(query)
        return df
    
    def fetch_control_optimal_path(self, start_level, target_control_name):
        path = []
        current_level = start_level
        current_control = target_control_name
        visited = set()
        
        while current_level >= 1:
            if current_control in visited:
                break
            visited.add(current_control)
            
            query = """
            SELECT level, description, fromControl 
            FROM ControlINFO 
            WHERE description = ? 
            """
            result = self._execute_query(query, (current_control,))
            
            if result:
                if len(result) > 1 and start_level >= 4:
                    control = result[1]
                else:
                    control = result[0]
                
                path.insert(0, control[1])  
                current_control = control[2]  
                current_level = control[0] - 1  
                
                if current_level == start_level - 1:
                    break
            else:
                break

        return path
    
    def fetch_control_optimal_second_path(self, start_level, target_control_name):
        path = []
        current_level = start_level
        current_control = target_control_name
        visited = set()
        
        while current_level >= 1:
            if current_control in visited:
                break
            visited.add(current_control)
            
            query = """
            SELECT level, description, fromControl 
            FROM ControlINFO 
            WHERE description = ? and Level > ?
            """
            result = self._execute_query(query, (current_control, start_level))
            
            if result:
                if len(result) > 1 and start_level >= 4:
                    control = result[1]
                else:
                    control = result[0]
                
                path.insert(0, control[1])  
                current_control = control[2]  
                current_level = control[0] - 1  
                
                if current_level == start_level - 1:
                    break
            else:
                break

        return path
    
    def fetch_ui_path_by_index(self, hierarchical_level):
        print(f"hierarchical_level: {hierarchical_level} type: {type(hierarchical_level)}")
        if not isinstance(hierarchical_level, str):
            hierarchical_level = str(hierarchical_level)

        level_parts = hierarchical_level.split('.')
        path_descriptions = []
        accumulated_parts = []

        for part in level_parts:
            accumulated_parts.append(part)
            partial_level = '.'.join(accumulated_parts)
            rows = self._execute_query("""
                SELECT Description 
                FROM ControlINFO 
                WHERE HierarchicalLevel = ?
            """, (partial_level,))

            if rows:
                path_descriptions.append(rows[0][0])

        return path_descriptions
    
    def fetch_min_level_ui_path(self, target_control_name):
        from collections import deque
        
        query_for_min_level = """
        SELECT "Level", "Description", "FromControl"
        FROM "ControlINFO"
        WHERE "Description" = ?
        ORDER BY "Level" ASC
        """
        rows = self._execute_query(query_for_min_level, (target_control_name,))
        print(f"rows: {rows}")
        if not rows:
            return []

        min_level_row = rows[0]  # (level, description, fromControl)
        start_level, start_desc, from_control = min_level_row

        print(f"min_level_row: {min_level_row}")
        
        queue = deque([(start_level, start_desc, [start_desc])])
        visited = set([(start_level, start_desc)])
        
        final_path = []

        while queue:
            level, desc, path_so_far = queue.popleft()
            print(f"level: {level}, desc: {desc}, path_so_far: {path_so_far}")  
            
            if level <= 1:
                final_path = path_so_far
                break
            
            query_parents = """
            SELECT "Level", "Description", "FromControl"
            FROM "ControlINFO"
            WHERE "Description" = ?
            """
            parent_rows = self._execute_query(query_parents, (desc,))
            print(f"parent_rows: {parent_rows}")
            if not parent_rows:
                continue

            for p_level, p_desc, p_from in parent_rows:
                if p_from:
                    parents = [item.strip() for item in p_from.split(",") if item.strip()]
                    for parent_desc in parents:
                        if (p_level - 1, parent_desc) not in visited:
                            visited.add((p_level - 1, parent_desc))
                            new_path = [parent_desc] + path_so_far
                            queue.append((p_level - 1, parent_desc, new_path))
        print(f"final_path: {final_path}")
        return final_path
    
    def fetch_all_ui_paths_any_level(self, target_control_name):
        from collections import deque
        all_paths = []
        queue = deque([(target_control_name, [target_control_name])])
        visited = set([target_control_name])

        while queue:
            current_desc, current_path = queue.popleft()

            query = """
            SELECT "Level", "Description", "FromControl"
            FROM "ControlINFO"
            WHERE "Description" = ?
            """
            rows = self._execute_query(query, (current_desc,))

            if not rows:
                continue

            for level_value, desc_value, from_control in rows:
                if level_value == 1:
                    all_paths.append(current_path)
                else:
                    if from_control:
                        parents = [item.strip() for item in from_control.split(",") if item.strip()]
                        for parent_desc in parents:
                            if parent_desc not in visited:
                                visited.add(parent_desc)
                                new_path = [parent_desc] + current_path
                                queue.append((parent_desc, new_path))

        return all_paths

    def insert_control_info(self, report_id, control_name, level, from_control, HierarchicalLevel, rule, control_path_hash, control_id_hash, runtime_id, is_validated, WindowName, WindowAutomationId, WindowType, WindowLevel2Name, WindowLevel2AutomationId, WindowLevel2Type, parent_name, parent_type, previous_sibling_name, next_sibling_name,
                            localized_control_type, control_type, ToggleState, automation_id, full_description, control_accesskey, app_version, workflow, language, qt_version, arch, jenkins_job, machine_name, control_bounding_rectangles, class_name,
                            default_action, legacy_value, expand_collapse_state, is_enabled, is_keyboard_focusable, has_keyboard_focus,
                            help_text, legacy_role, legacy_state, image, pre_control_image, window_image, process_id, process_name, project_id, keyboard_action, ancestors=None):
        query = '''
        INSERT INTO ControlINFO (
            ReportId, Description, Level, FromControl, HierarchicalLevel, rule, control_path_hash, control_id_hash, RuntimeId, is_validated, WindowName, WindowAutomationId, WindowType, WindowLevel2Name, WindowLevel2AutomationId, WindowLevel2Type, Parent, ParentType, Pre, Next, 
            ControlLocalizedType, ControlType, ToggleState, AutomationId, FullDescription, AccessKey, AppVersion, Workflow, Language, QtVersion, Arch, JenkinsJob, MachineName, BoundingRectangles, ClassName, 
            Action, LegacyValue, CollapseState, IsEnabled, IsKeyboardFocusable, HasKeyboardFocus, 
            HelpText, LegacyRole, LegacyState, Image, PreControlImage, WindowImage, ProcessID, ProcessName, ProjectID, keyboardAction, Ancestors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            report_id, control_name, level, from_control, HierarchicalLevel, rule, control_path_hash, control_id_hash, runtime_id, is_validated, WindowName, WindowAutomationId, WindowType, WindowLevel2Name, WindowLevel2AutomationId, WindowLevel2Type, parent_name, parent_type, previous_sibling_name, next_sibling_name,
            localized_control_type, control_type, ToggleState, automation_id, full_description, control_accesskey, app_version, workflow, language, qt_version, arch, jenkins_job, machine_name, control_bounding_rectangles, class_name,
            default_action, legacy_value, expand_collapse_state, is_enabled, is_keyboard_focusable, has_keyboard_focus,
            help_text, legacy_role, legacy_state, image, pre_control_image, window_image, process_id, process_name, project_id, keyboard_action, ancestors
        )
        self._execute_query(query, params, commit=True)

    
    def insert_control_info_to_sql(self, report_id, control_name, level=0, from_control="", 
                                   HierarchicalLevel="", rule="", control_path_hash="", 
                                   control_id_hash="", runtime_id="", is_validated=0, 
                                   WindowName="", WindowAutomationId="", WindowType=0, 
                                   WindowLevel2Name="", WindowLevel2AutomationId="", 
                                   WindowLevel2Type=0, parent_name="", parent_type=0, 
                                   previous_sibling_name="", next_sibling_name="",
                                   localized_control_type="", control_type=0, ToggleState="", 
                                   automation_id="", full_description="", control_accesskey="", 
                                   app_version="", workflow="", language="", qt_version="", arch="x64", jenkins_job="", 
                                   machine_name="", control_bounding_rectangles="", class_name="",
                                   default_action="", legacy_value="", expand_collapse_state="", 
                                   is_enabled=0, is_keyboard_focusable=0, has_keyboard_focus=0,
                                   help_text="", legacy_role=0, legacy_state=0, image=None, 
                                   pre_control_image=None, window_image=None, process_id=0, 
                                   process_name="", project_id=0, keyboard_action="", ancestors=None):

        connection = self._get_db_connection()
        if not connection:
            LOGGER_ERROR(f"Failed to get database connection for control info insertion")
            return False
        
        try:
            with connection.cursor() as cursor:
                LOGGER_DEBUG(f"Inserting control info to SQL - Report ID: {report_id}, Control: {control_name}, Level: {level}")
                
                insert_query = """
                    INSERT INTO ControlINFO(
                        ReportId, Description, Level, FromControl, HierarchicalLevel, rule, 
                        control_path_hash, control_id_hash, RuntimeId, is_validated, WindowName, 
                        WindowAutomationId, WindowType, WindowLevel2Name, WindowLevel2AutomationId, 
                        WindowLevel2Type, Parent, ParentType, Pre, Next, ControlLocalizedType, 
                        ControlType, ToggleState, AutomationId, FullDescription, AccessKey, 
                        AppVersion, Workflow, Language, QtVersion, Arch, JenkinsJob, MachineName, BoundingRectangles, 
                        ClassName, Action, LegacyValue, CollapseState, IsEnabled, IsKeyboardFocusable, 
                        HasKeyboardFocus, HelpText, LegacyRole, LegacyState, Image, PreControlImage, 
                        WindowImage, ProcessID, ProcessName, ProjectID, keyboardAction, Ancestors
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                values = (
                    report_id, control_name, level, from_control, HierarchicalLevel, rule, 
                    control_path_hash, control_id_hash, runtime_id, is_validated, WindowName, 
                    WindowAutomationId, WindowType, WindowLevel2Name, WindowLevel2AutomationId, 
                    WindowLevel2Type, parent_name, parent_type, previous_sibling_name, next_sibling_name,
                    localized_control_type, control_type, ToggleState, automation_id, full_description, 
                    control_accesskey, app_version, workflow, language, qt_version, arch, jenkins_job, machine_name, 
                    control_bounding_rectangles, class_name, default_action, legacy_value, 
                    expand_collapse_state, is_enabled, is_keyboard_focusable, has_keyboard_focus,
                    help_text, legacy_role, legacy_state, image, pre_control_image, window_image,
                    process_id, process_name, project_id, keyboard_action, ancestors
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                                
                return True
                
        except pymysql.Error as e:
            LOGGER_ERROR(f"Failed to insert control info to SQL: {e}")
            LOGGER_ERROR(f"Control details - Report ID: {report_id}, Control: {control_name}, Level: {level}, AutomationId: {automation_id}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if connection:
                connection.close()


    def insert_control_action_history(self, description, control_type, automation_id, image_name, image, pre_control_image, window_image, img_hash=None):
        """
        Inserts a control action record into the ControlActionHistory table.
        
        :param description: Description of the control.
        :param control_type: The control type.
        :param automation_id: The automation ID of the control.
        :param image_name: The name of the control image.
        :param image: The current control image.
        :param pre_control_image: The previous control image.
        :param window_image: The topmost window image of the current control.
        :param img_hash: The perceptual hash of the control image.
        """
        query = '''
        INSERT INTO ControlActionHistory (
            Description, ControlType, AutomationId, ImageName, Image, PreControlImage, WindowImage, ImageHash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (description, control_type, automation_id, image_name, image, pre_control_image, window_image, img_hash)
        
        self._execute_query(query, params, commit=True)


    def update_control_validated_status(self, hash_value, is_validated, column_name):
        """
        Updates the validation status of a control based on a given hash.
        
        :param hash_value: The control path hash or control ID hash
        :param is_validated: The validation status value
        :param column_name: Either "control_path_hash" or "control_id_hash"
        :raises ValueError: If column_name is not one of the allowed values
        """
        if column_name not in ("control_path_hash", "control_id_hash", "HierarchicalLevel"):
            raise ValueError("Invalid column name. Must be 'control_path_hash' or 'control_id_hash' or 'HierarchicalLevel'.")

        sqlite_query = f'''
            UPDATE "ControlINFO"
            SET "is_validated" = ?
            WHERE "{column_name}" = ?
        '''
        self._execute_query(sqlite_query, (is_validated, hash_value), commit=True)

    def update_control_image(self, hash_value, window_image, column_name):
        """
        Updates the validation status of a control based on a given hash.
        
        :param hash_value: The control path hash or control ID hash
        :param window_image: The topmost window image path of the current control or the window image in BLOB format
        :param column_name: Either "control_path_hash" or "control_id_hash"
        """
        if column_name not in ("control_path_hash", "control_id_hash"):
            raise ValueError("Invalid column name. Must be 'control_path_hash' or 'control_id_hash'.")

        query = f'''
            UPDATE "ControlINFO"
            SET "WindowImage" = ?
            WHERE "{column_name}" = ?
        '''
        self._execute_query(query, (window_image, hash_value), commit=True)

    def update_control_hierarchical_level(self, hierarchical_level, column_name, column_value):
        if column_name not in ("control_path_hash", "control_id_hash"):
            raise ValueError("Invalid column name. Must be 'control_path_hash' or 'control_id_hash'.")

        sqlite_query = f'''
            UPDATE "ControlINFO"
            SET "HierarchicalLevel" = ?
            WHERE "{column_name}" = ?
        '''
        self._execute_query(sqlite_query, (hierarchical_level, column_value), commit=True)


    def create_control_info_database(self, name="ControlInfo"):
        """
        Create a new ControlInfo database based on version similar to CreateNavigationDB.
        
        Args:
            name (str): Database name suffix (default: "ControlInfo")
            
        Returns:
            str: Database name if successful, None if failed
        """
        try:
            LOGGER_INFO(f"Starting database creation with name suffix: {name}")
            
            # Get base database connection (to MySQL server, not to a specific database)
            connection = self._get_db_connection()
            if not connection:
                LOGGER_ERROR("Failed to get base database connection for creating ControlInfo database")
                return None
            
            LOGGER_INFO("MySQL server connection successful")
            
            # Get settings and version info
            settings = DynamicConfig(SETTINGS_PATH)
            app_version_str = str(settings.get('appVersion', '1.0'))
            LOGGER_INFO(f"Raw app version from settings: {app_version_str}")
            
            app_version = app_version_str.split('.')
            LOGGER_INFO(f"Split app version: {app_version}")
            
            if len(app_version) >= 2:
                version = f'{app_version[0]}.{app_version[1]}'
            else:
                # Fallback if version format is unexpected
                version = "1.0"
                LOGGER_WARNING(f"Unexpected app version format: {app_version_str}, using default: {version}")
            
            language = settings.get("language", "en")
            LOGGER_INFO(f"Using version: {version}, language: {language}")
            
            # Create database name - this will be the actual database name
            new_database = f'RegressShield_{name}_{version.replace(".", "_")}'
            LOGGER_INFO(f"Target database name: {new_database}")
            
            try:
                with connection.cursor() as cursor:
                    LOGGER_INFO("Checking existing databases...")
                    # Check if database exists
                    cursor.execute('SHOW DATABASES;')
                    database_names = [row[0] for row in cursor.fetchall()]
                    LOGGER_INFO(f"Found {len(database_names)} existing databases")
                    
                    if new_database not in database_names:
                        # Create new database
                        LOGGER_INFO(f"Creating new database: {new_database}")
                        cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{new_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
                        LOGGER_INFO(f"Database creation command executed successfully")
                    else:
                        LOGGER_INFO(f"Database {new_database} already exists")
                    
                    # Use the newly created database
                    LOGGER_INFO(f"Switching to database: {new_database}")
                    cursor.execute(f'USE `{new_database}`;')
                    
                    # Create ControlINFO table based on the SQL schema
                    LOGGER_INFO("Creating ControlINFO table...")
                    create_table_sql = '''
                    CREATE TABLE IF NOT EXISTS ControlINFO (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ReportId VARCHAR(255),
                        Description TEXT,
                        Level INT,
                        FromControl VARCHAR(255),
                        HierarchicalLevel VARCHAR(255),
                        rule VARCHAR(255),
                        control_path_hash VARCHAR(255),
                        control_id_hash VARCHAR(255),
                        RuntimeId TEXT,
                        is_validated INT,
                        WindowName VARCHAR(500),
                        WindowAutomationId VARCHAR(500),
                        WindowType VARCHAR(255),
                        WindowLevel2Name VARCHAR(1500),
                        WindowLevel2AutomationId VARCHAR(500),
                        WindowLevel2Type VARCHAR(255),
                        Parent VARCHAR(500),
                        ParentType VARCHAR(255),
                        Pre VARCHAR(500),
                        Next VARCHAR(500),
                        ControlLocalizedType VARCHAR(255),
                        ControlType INT,
                        ToggleState VARCHAR(50),
                        AutomationId VARCHAR(500),
                        FullDescription TEXT,
                        AccessKey VARCHAR(255),
                        AppVersion VARCHAR(100),
                        Workflow VARCHAR(255),
                        Language VARCHAR(50),
                        QtVersion VARCHAR(10),
                        Arch VARCHAR(20),
                        JenkinsJob VARCHAR(255),
                        MachineName VARCHAR(255),
                        BoundingRectangles VARCHAR(255),
                        ClassName VARCHAR(255),
                        Action VARCHAR(255),
                        LegacyValue TEXT,
                        CollapseState VARCHAR(50),
                        IsEnabled VARCHAR(50),
                        IsKeyboardFocusable VARCHAR(50),
                        HasKeyboardFocus VARCHAR(50),
                        HelpText TEXT,
                        LegacyRole VARCHAR(255),
                        LegacyState VARCHAR(50),
                        Image VARCHAR(500),
                        PreControlImage VARCHAR(500),
                        WindowImage VARCHAR(500),
                        ProcessID INT,
                        ProcessName VARCHAR(255),
                        ProjectID VARCHAR(50),
                        keyboardAction VARCHAR(255),
                        Ancestors TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_report_id (ReportId),
                        INDEX idx_control_path_hash (control_path_hash),
                        INDEX idx_control_id_hash (control_id_hash),
                        INDEX idx_workflow_language (Workflow, Language),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    '''
                    
                    LOGGER_INFO("Executing CREATE TABLE command...")
                    cursor.execute(create_table_sql)
                    connection.commit()
                    
                    LOGGER_INFO(f"Successfully created ControlINFO table in database: {new_database}")
                    return new_database
                    
            except pymysql.Error as e:
                LOGGER_ERROR(f"MySQL error during database creation: {e}")
                LOGGER_ERROR(f"Error code: {e.args[0] if e.args else 'Unknown'}")
                LOGGER_ERROR(f"Error message: {e.args[1] if len(e.args) > 1 else 'Unknown'}")
                if connection:
                    connection.rollback()
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Unexpected error creating ControlInfo database: {e}")
            import traceback
            LOGGER_ERROR(f"Traceback: {traceback.format_exc()}")
            return None
            
        finally:
            if connection:
                connection.close()
                LOGGER_INFO("Database connection closed")

    def upload_local_control_info_to_database(self):
        """
        Upload local ControlINFO.db data to the existing MySQL ControlINFO table.
        
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            LOGGER_INFO("Starting upload to existing ControlINFO table")
            
            # Check if local database file exists
            if not os.path.exists(self.db_path):
                LOGGER_ERROR(f"Local database file not found: {self.db_path}")
                return False
            
            # Connect to local SQLite database
            local_conn = sqlite3.connect(self.db_path)
            local_cursor = local_conn.cursor()
            
            # Check if ControlINFO table exists
            local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ControlINFO'")
            if not local_cursor.fetchone():
                LOGGER_WARNING("ControlINFO table not found in local database")
                local_conn.close()
                return True
            
            # Get all data from local ControlINFO table
            local_cursor.execute("SELECT * FROM ControlINFO")
            local_data = local_cursor.fetchall()
            
            # Get column names from SQLite table
            local_cursor.execute("PRAGMA table_info(ControlINFO)")
            columns_info = local_cursor.fetchall()
            sqlite_columns = [col[1] for col in columns_info]
            
            local_conn.close()
            
            if not local_data:
                LOGGER_WARNING("No data found in local ControlINFO table")
                return True
            
            LOGGER_DEBUG(f"Found {len(local_data)} records to upload")
            
            # Connect to the existing MySQL database
            mysql_conn = self._get_db_connection()
            if not mysql_conn:
                LOGGER_ERROR("Failed to get MySQL database connection")
                return False
            
            try:
                with mysql_conn.cursor() as mysql_cursor:
                    # Get MySQL table column names (excluding auto-increment id)
                    mysql_cursor.execute("DESCRIBE ControlINFO")
                    mysql_columns_info = mysql_cursor.fetchall()
                    mysql_columns = [col[0] for col in mysql_columns_info if col[0] != 'id']
                    
                    LOGGER_DEBUG(f"MySQL table has {len(mysql_columns)} columns")
                    
                    # Map SQLite columns to MySQL columns (excluding TabOrder -> id mapping)
                    column_mapping = []
                    for sqlite_col in sqlite_columns:
                        if sqlite_col == 'TabOrder':
                            continue  # Skip TabOrder as it maps to auto-increment id
                        elif sqlite_col in mysql_columns:
                            column_mapping.append(sqlite_col)
                        else:
                            LOGGER_WARNING(f"Column {sqlite_col} from SQLite not found in MySQL table")
                    
                    if not column_mapping:
                        LOGGER_ERROR("No matching columns found between SQLite and MySQL tables")
                        return False
                                        
                    # Prepare INSERT statement
                    placeholders = ', '.join(['%s'] * len(column_mapping))
                    insert_sql = f'''
                        INSERT INTO ControlINFO ({', '.join(column_mapping)})
                        VALUES ({placeholders})
                    '''
                    
                    # Upload data in batches
                    batch_size = 1000
                    total_records = len(local_data)
                    uploaded_count = 0
                    
                    for i in range(0, total_records, batch_size):
                        batch_data = local_data[i:i + batch_size]
                        batch_values = []
                        
                        for row in batch_data:
                            # Extract values for mapped columns
                            row_values = []
                            for col_name in column_mapping:
                                col_index = sqlite_columns.index(col_name)
                                value = row[col_index]
                                row_values.append(value)
                            batch_values.append(tuple(row_values))
                        
                        # Execute batch insert
                        mysql_cursor.executemany(insert_sql, batch_values)
                        uploaded_count += len(batch_values)
                                            
                    mysql_conn.commit()
                    LOGGER_INFO(f"Successfully uploaded {uploaded_count}/{total_records} records from local DB to ControlINFO table")
                    
                    return True
                    
            except pymysql.Error as e:
                LOGGER_ERROR(f"Failed to upload data to MySQL database: {e}")
                if mysql_conn:
                    mysql_conn.rollback()
                return False
                
        except Exception as e:
            LOGGER_ERROR(f"Unexpected error during upload: {e}")
            return False
            
        finally:
            if mysql_conn:
                mysql_conn.close()


