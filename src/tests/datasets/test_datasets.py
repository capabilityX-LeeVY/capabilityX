import os
import sys
import sqlite3

class TestDatasets:
    def __init__(self):
        self.db_path = r"ControlINFO.db"  # Path to your SQLite database

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

    def fetch_control_automation_id_by_name(self, description):
        """Fetch all distinct AutomationId values based on the description."""
        query = 'SELECT DISTINCT "AutomationId" FROM "ControlINFO" WHERE "Description" = ?'
        return self._execute_query(query, (description,)) 

if __name__ == "__main__":
    # Example usage: you can replace the parameters with actual values
    control_description = "AI Assistant"
    test_instance = TestDatasets()
    control_automationId = test_instance.fetch_control_automation_id_by_name(control_description) 
    print(f"Fetching AutomationId for description: [{control_description}], AutomationId: {control_automationId}")

