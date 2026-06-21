import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('ControlINFO.db')
cursor = conn.cursor()

# Drop the existing table if it exists
cursor.execute('DROP TABLE IF EXISTS ControlINFO')

# Commit the changes and close the connection
conn.commit()
conn.close()