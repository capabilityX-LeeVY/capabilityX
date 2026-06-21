import sqlite3

# Create an SQLite database and table with auto-incrementing TabOrder
conn = sqlite3.connect('ControlINFO.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Projects (
    ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
    ProjectName TEXT,
    ProjectDescription TEXT
)
''')
conn.commit()
conn.close()