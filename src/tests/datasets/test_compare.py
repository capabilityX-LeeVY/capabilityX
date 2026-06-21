import sqlite3
from config.paths import DB_PATH

# 文件路径
db1_path = r'src\db\ControlINFO0519.db'
db2_path = DB_PATH

def get_distinct_descriptions(db_path):
    """
    从指定的 SQLite 数据库中获取 ControlINFO 表的 DISTINCT Description 字段。
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT Description FROM ControlINFO')
        descriptions = {row[0] for row in cursor.fetchall()}  # 使用集合去重
        conn.close()
        return descriptions
    except Exception as e:
        print(f"Error accessing database {db_path}: {e}")
        return set()

def compare_descriptions(db1_descriptions, db2_descriptions):
    """
    比较两个数据库的 Description 字段集合，返回差异。
    """
    only_in_db1 = db1_descriptions - db2_descriptions
    only_in_db2 = db2_descriptions - db1_descriptions
    return only_in_db1, only_in_db2

if __name__ == "__main__":
    # 获取两个数据库的 DISTINCT Description 集合
    db1_descriptions = get_distinct_descriptions(db1_path)
    db2_descriptions = get_distinct_descriptions(db2_path)

    # 比较差异
    only_in_db1, only_in_db2 = compare_descriptions(db1_descriptions, db2_descriptions)

    # 打印结果
    print("Descriptions only in ControlINFOBenchmark.db:")
    for desc in only_in_db1:
        print(f"- {desc}")

    print("\nDescriptions only in ControlINFO.db:")
    for desc in only_in_db2:
        print(f"- {desc}")