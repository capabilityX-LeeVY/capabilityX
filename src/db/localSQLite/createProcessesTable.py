import sqlite3

# Create an SQLite database and table with auto-incrementing TabOrder
conn = sqlite3.connect('ControlINFO.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Processes (
    ProcessID INTEGER,
    ProcessName TEXT,
    ProcessStep INTEGER,
    ControlName TEXT,
    ControlType TEXT,
    ControlAutomationID TEXT,
    ControlAction TEXT,
    ControlActionWaitTime INTEGER DEFAULT 1,
    ProjectID INTEGER,
    ProjectName TEXT,
    UNIQUE(ProcessName, ControlName)
)
''')
conn.commit()
conn.close()