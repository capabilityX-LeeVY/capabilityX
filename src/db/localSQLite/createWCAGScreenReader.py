import sqlite3

def create_table(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WCAGScreenReader (
            Control INTEGER PRIMARY KEY AUTOINCREMENT,
            Description TEXT,
            Type TEXT,
            DefaultAction TEXT,
            Compliance TEXT,
            Suggestions TEXT,
            SuggestedRevision TEXT,
            WCAGLevel TEXT,
            "References" TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Specify the path to your database
db_path = 'ControlINFO.db'

# Create the table
create_table(db_path)

print("Table created successfully.")