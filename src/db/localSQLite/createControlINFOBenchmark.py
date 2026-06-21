import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect(r'src\db\ControlINFOBenchmark.db')
cursor = conn.cursor()

# Create the ControlINFO table with a foreign key constraint
cursor.execute('''
CREATE TABLE IF NOT EXISTS ControlINFO (
    TabOrder INTEGER PRIMARY KEY AUTOINCREMENT,
    Description TEXT,
    Level INTEGER,
    FromControl TEXT,
    HierarchicalLevel INTEGER,
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
    Pre TEXT,
    Next TEXT,
    ControlLocalizedType TEXT,
    ControlType INTEGER,
    ToggleState TEXT,
    AutomationId TEXT,
    FullDescription TEXT,
    AccessKey TEXT,
    BoundingRectangles TEXT,          
    ClassName TEXT,
    Action TEXT,
    LegacyValue TEXT,
    IsEnabled INTEGER,
    IsKeyboardFocusable INTEGER,
    HasKeyboardFocus INTEGER,
    HelpText TEXT,
    LegacyRole INTEGER,
    LegacyState INTEGER,
    ProcessID INTEGER,
    ProcessName TEXT,
    ProjectID INTEGER,
    keyboardAction TEXT,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()