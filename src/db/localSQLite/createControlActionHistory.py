import sqlite3
from config.paths import DB_PATH

# Connect to the SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the ControlINFO table with a foreign key constraint
cursor.execute('''
CREATE TABLE IF NOT EXISTS ControlActionHistory (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Description TEXT,
    ControlType TEXT,
    AutomationId TEXT,
    ImageName TEXT,
    Image BLOB,
    PreControlImage BLOB,
    WindowImage BLOB,
    Created DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()