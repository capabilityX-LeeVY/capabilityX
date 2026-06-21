import sqlite3

def initControlINFODB():
    _deleteControlINFO()

def executeQuery(query, params=None):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('ControlINFO.db')
        cursor = conn.cursor()

        # Execute the query with parameters if provided
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error executing query: {e}")


def insertControlINFO(control_name, level, from_control, parent_name, previous_sibling_name, next_sibling_name,
                      localized_control_type, control_type, automation_id, control_runtimeId, full_description, control_accesskey, control_bounding_rectangles, class_name,
                      default_action, legacy_value, is_enabled, is_keyboard_focusable, has_keyboard_focus,
                      help_text, legacy_role, legacy_state, process_id, process_name, project_id, keyboard_action):
    query = '''
    INSERT INTO ControlINFO (
        Description, Level, FromControl, Parent, Pre, Next, 
        ControlLocalizedType, ControlType, AutomationId, RuntimeId, FullDescription, AccessKey, BoundingRectangles, ClassName, 
        Action, LegacyValue, IsEnabled, IsKeyboardFocusable, HasKeyboardFocus, 
        HelpText, LegacyRole, LegacyState, ProcessID, ProcessName, ProjectID, keyboardAction
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    params = (
        control_name, level, from_control, parent_name, previous_sibling_name, next_sibling_name,
        localized_control_type, control_type, automation_id, control_runtimeId, full_description, control_accesskey, control_bounding_rectangles, class_name,
        default_action, legacy_value, is_enabled, is_keyboard_focusable, has_keyboard_focus,
        help_text, legacy_role, legacy_state, process_id, process_name, project_id, keyboard_action
    )
    executeQuery(query, params)

def dropControlINFO():
    query = 'DROP TABLE IF EXISTS ControlINFO'
    executeQuery(query)

def _deleteControlINFO():
    delete_data_query = 'DELETE FROM ControlINFO'
    reset_autoincrement_query = 'DELETE FROM sqlite_sequence WHERE name="ControlINFO"'
    executeQuery(delete_data_query)
    executeQuery(reset_autoincrement_query)

def executeSelectQuery(query, params=None):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('ControlINFO.db')
        cursor = conn.cursor()

        # Execute the query with parameters if provided
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()

        # Close the connection
        conn.close()

        # Return the results
        return results

    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def select_control_info(search_term):
    query = '''
    SELECT DISTINCT "Description", "Level", "FromControl", "AutomationID", "ControlType"
    FROM "ControlINFO"
    WHERE "Description" LIKE ?
    AND "level" = '1'
    AND "ControlType" IN (50000);
    '''
    params = ('%' + search_term + '%',)
    return executeSelectQuery(query, params)

def _selectControlNameByLevel(level):
    query = '''
    SELECT DISTINCT "Description"
    FROM "ControlINFO"
    WHERE "level" = ?;
    '''
    params = (level,)
    return executeSelectQuery(query, params)

def selectControlNameByLevel(level):
    try:
        nested_list = _selectControlNameByLevel(level)
        if nested_list is None:
            return None

        flatten_list = [item for sublist in nested_list for item in sublist]
        return flatten_list

    except Exception as e:
        print(f"Error selecting control info: {e}")
        return None

def selectControlInfoByName(description):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description
    query = '''
        SELECT DISTINCT "Description", "ControlType", "FromControl", "keyboardAction", "AutomationId", "RuntimeId"
        FROM "ControlINFO"
        WHERE "Description" = ?
    '''

    # Execute the query with the provided description
    cursor.execute(query, (description,))
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlInfoByAutoId(description):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description
    query = '''
        SELECT DISTINCT "Description", "ControlType", "FromControl", "keyboardAction", "AutomationId"
        FROM "ControlINFO"
        WHERE "AutomationId" = ?
    '''

    # Execute the query with the provided description
    cursor.execute(query, (description,))
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlInfoByRunId(description):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description
    query = '''
        SELECT DISTINCT "Description", "ControlType", "FromControl", "keyboardAction", "AutomationId", "RuntimeId"
        FROM "ControlINFO"
        WHERE "RuntimeId" = ?
    '''

    # Execute the query with the provided description
    cursor.execute(query, (description,))
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlInfoByFuzzyName(description):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description with LIKE for fuzzy matching
    query = '''
        SELECT DISTINCT "Description", "ControlType", "FromControl", "keyboardAction", "AutomationId"
        FROM "ControlINFO"
        WHERE "Description" LIKE ?
    '''

    # Add wildcards to the description for fuzzy matching
    fuzzy_description = ('%' + description + '%',)
    # Execute the query with the provided description
    cursor.execute(query, fuzzy_description)
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlInfoByFromControl(from_control):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    query = '''
        SELECT DISTINCT "Description", "ControlType", "FromControl", "keyboardAction", "AutomationId"
        FROM "ControlINFO"
        WHERE "FromControl" = ?
    '''

    cursor.execute(query, (from_control,))
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlName(description):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description
    query = '''
        SELECT DISTINCT "Description"
        FROM "ControlINFO"
        WHERE "Description" = ?
    '''
    # Execute the query with the provided description
    cursor.execute(query, (description,))
    results = cursor.fetchall()

    conn.close()
    return results

def selectControlAutomationId(automationId):
    conn = sqlite3.connect('ControlINFO.db')
    cursor = conn.cursor()

    # SQL query to select distinct FromControl based on Description
    query = '''
        SELECT DISTINCT "AutomationId"
        FROM "ControlINFO"
        WHERE "AutomationId" = ?
    '''
    # Execute the query with the provided description
    cursor.execute(query, (automationId,))
    results = cursor.fetchall()

    conn.close()
    return results
    
def select_control_automationid(search_term):
    query = '''
    SELECT DISTINCT "AutomationID"
    FROM "ControlINFO"
    WHERE "Description" LIKE ?;
    '''
    params = ('%' + search_term + '%',)
    return executeSelectQuery(query, params)

def select_process_steps(process_name):
    query = '''
    SELECT "ProcessStep", "ControlName", "ControlAction", "ControlActionWaitTime"
    FROM "Processes"
    WHERE "ProcessName" = ?
    ORDER BY "ProcessStep";
    '''
    params = (process_name,)
    return executeSelectQuery(query, params)

def select_processname_installer():
    query = '''
    SELECT DISTINCT "processName"
    FROM "Processes"
    WHERE ProjectID = 0
    GROUP BY "ProcessName"
    ORDER BY "ProcessID" ASC;
    '''
    return executeSelectQuery(query)

def select_processname_app():
    query = '''
    SELECT DISTINCT "processName"
    FROM "Processes"
    WHERE ProjectID = 1
    GROUP BY "ProcessName"
    ORDER BY "ProcessID" ASC;
    '''
    return executeSelectQuery(query)