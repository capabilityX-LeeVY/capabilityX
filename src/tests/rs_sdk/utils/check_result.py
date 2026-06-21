import sqlite3
import pandas as pd
from config.paths import DB_NAME

# Database paths
# DB_PATHS = {
#     "ControlINFOBenchmark": r"src\db\ControlINFOBenchmark.db",
#     "ControlINFO": r"src\db\ControlINFO.db"
# }

def fetch_data(db_path):
    """Fetches data from the SQLite database controlinfo table."""
    conn = sqlite3.connect(db_path)
    query = """SELECT 
        "TabOrder", "Level", "Description", "FromControl", "HierarchicalLevel", 
        "rule", is_validated, "ControlLocalizedType", "ToggleState", "ControlType", 
        control_path_hash, "WindowName", "WindowLevel2Name", 
        "parent", "FullDescription", "processid"
        FROM controlinfo"""
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def compare_databases():
    """Compares the controlinfo table between Benchmark and Current databases."""
    # Load Benchmark and Current data
    df_benchmark = fetch_data(DB_NAME["ControlINFOBenchmark"])
    df_current = fetch_data(DB_NAME["ControlINFO"])

    # Merge data based on control_path_hash
    merged_df = df_benchmark.merge(df_current, on="control_path_hash", how="outer", suffixes=("_benchmark", "_current"))

    # 1. Identify data differences in specific fields
    diff_mask = (merged_df["Description_benchmark"] != merged_df["Description_current"]) | \
                (merged_df["FullDescription_benchmark"] != merged_df["FullDescription_current"]) | \
                (merged_df["ControlType_benchmark"] != merged_df["ControlType_current"]) | \
                (merged_df["ToggleState_benchmark"] != merged_df["ToggleState_current"])
    different_data = merged_df[diff_mask][["control_path_hash", "Description_benchmark", "Description_current",
                                           "FullDescription_benchmark", "FullDescription_current",
                                           "ControlType_benchmark", "ControlType_current",
                                           "ToggleState_benchmark", "ToggleState_current"]]

    # 2. Identify TabOrder changes
    taborder_mask = merged_df["TabOrder_benchmark"] != merged_df["TabOrder_current"]
    taborder_changes = merged_df[taborder_mask][["control_path_hash", "Description_benchmark", "TabOrder_benchmark", "TabOrder_current"]]

    # 3. Identify deleted controls (exist in Benchmark but not in Current)
    deleted_controls = merged_df[merged_df["Description_current"].isna()][["control_path_hash", "Description_benchmark", "TabOrder_benchmark"]]

    # 4. Identify newly added controls (exist in Current but not in Benchmark)
    added_controls = merged_df[merged_df["Description_benchmark"].isna()][["control_path_hash", "Description_current", "TabOrder_current"]]

    # Print results
    print("\n📌 Controls with Data Differences:")
    print(different_data)

    print("\n📌 Controls with TabOrder Changes:")
    print(taborder_changes)

    print("\n📌 Deleted Controls:")
    print(deleted_controls)

    print("\n📌 Newly Added Controls:")
    print(added_controls)

if __name__ == "__main__":
    compare_databases()
