import sqlite3
from config.paths import DB_PATH

db_path = DB_PATH
output_path = r"src\config\control_id_map.py"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT "Description", "AutomationId"
    FROM "ControlINFO"
    WHERE "Description" IS NOT NULL AND "AutomationId" IS NOT NULL AND TRIM("Description") != ''
""")

desc_id_map = {}
for desc, auto_id in cursor.fetchall():
    if desc not in desc_id_map:
        desc_id_map[desc] = auto_id

conn.close()

with open(output_path, "w", encoding="utf-8") as f:
    f.write("CONTROL_ID_MAP = {\n")
    for desc, auto_id in desc_id_map.items():
        desc_str = desc.replace('"', '\\"')
        auto_id_str = auto_id.replace('"', '\\"')
        f.write(f'    "{desc_str}": "{auto_id_str}",\n')
    f.write("}\n")

print(f"save {output_path}, total {len(desc_id_map)} records")