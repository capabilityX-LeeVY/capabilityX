import sqlite3
from config.paths import DB_PATH

# Connect to the SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the Projects table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Projects (
    ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
    ProjectName TEXT,
    ProjectDescription TEXT
)
''')

# Create the ControlINFO table with a foreign key constraint
cursor.execute('''
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
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()