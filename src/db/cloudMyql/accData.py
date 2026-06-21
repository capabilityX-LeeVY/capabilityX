import pandas as pd
import platform
import sqlite3
from config.paths import DB_PATH
from config.mysql import ConnectToDB
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH, DB_CONFIG_PATH
from common.utils.logger import LOGGER_WARNING

def dbInitializer():
    createControlImgReviewResultTable()
    
def createControlImgReviewResultTable():
    conn = ConnectToDB()
    sql_statement = """
    CREATE TABLE IF NOT EXISTS control_img_review_result (
        img_hash CHAR(64) PRIMARY KEY,
        img_bytes MEDIUMBLOB,
        status INT,
        image_focus_status TEXT,
        platform TEXT,
        added_by TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn.Execute(sql_statement)
        print("Table onfocus_controls_reviewed_result ensured.")
    except Exception as e:
        print(f"Failed to create table: {e}")

def insertDataToWindowsControls(contrls_data):
    table_name = "windowsControls" if platform.system().lower() == "windows" else "macOSControls"
    
    conn = ConnectToDB()
    sql_statement = f'''
        INSERT INTO {table_name} (
            controlName,
            controlType,
            controlAutomationID,
            controlFullDescription,
            controlBoundingRectangle,
            controlNativeWindowHandle,
            currentControl,
            entryControl,
            preControl,
            fromAction,
            controlFocusRing,
            preControlFocusRing,
            isProcessed    
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    try:
        conn.ExecuteWithData(sql_statement, contrls_data)
    except Exception as e:
        return None
    
def getControlInfo(table_name):
    mysql_conn = ConnectToDB()
    results, columns = mysql_conn.Query(f"SELECT * FROM {table_name};")
    df = pd.DataFrame(results, columns=columns)
    df.rename(columns={
        "role": "ControlLocalizedType",
        "status": "is_validated"
    }, inplace=True)
    sqlite_conn = sqlite3.connect(DB_PATH)
    df.to_sql("ControlINFO", sqlite_conn, if_exists="replace", index=False)
    sqlite_conn.commit()
    sqlite_conn.close()
    
def selectNavigationData():
    # table_name = "ControlINFO" if platform.system().lower() == "windows" else "navigation_mac_baseline"
    settings = DynamicConfig(SETTINGS_PATH)
    table_name = settings.get('macOSnavigationTableName')
    if not table_name:
        LOGGER_WARNING("Failed to get navigation table.")
    
    conn = ConnectToDB()
    sql_statement = f'''
    SELECT *
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY controlID ORDER BY `timestamp` ASC) AS rn
        FROM {table_name}
        WHERE error = ''
    ) AS sub
    WHERE rn = 1
    ORDER BY `timestamp` ASC;
    '''
    results, columns = conn.Query(sql_statement)
    df = pd.DataFrame(results, columns=columns)
    return df

def selectProcessSteps(language_code='en_US',processIDs:list = []):
    settings = DynamicConfig(SETTINGS_PATH)
    db_config = DynamicConfig(DB_CONFIG_PATH)
    env = settings.get('environment')
    config = db_config.get('dbConfig')
    db_config = config[env] 
    dbName = db_config['dbName']
    table_name = "processesWindows" if platform.system().lower() == "windows" else f'''`{dbName}`.`processesMacOS`'''
    
    processIDin = ','.join(map(str, processIDs))
    conn = ConnectToDB()
    sql_statement = f'''
    SELECT *
    FROM {table_name}
    WHERE languageCode = '{language_code}' and processID in ({processIDin}) ORDER BY processID ASC, processStep ASC;
    '''
    results, columns = conn.Query(sql_statement)
    df = pd.DataFrame(results, columns=columns)
    return df

# def selectControls(isProcessed=0):
#     table_name = "windowsControls" if platform.system().lower() == "windows" else "macControls"
    
#     conn = ConnectToDB()
#     sql_statement = f'''
#     SELECT *
#     FROM {table_name}
#     WHERE isProcessed = {isProcessed} ORDER BY navigationID ASC;
#     '''
#     results, columns = conn.Query(sql_statement)
#     df = pd.DataFrame(results, columns=columns)

#     if not df.empty:
#         entry_controls = df.loc[df['isProcessed'] == isProcessed, 'entryControl']
#         if not entry_controls.empty:
#             currentControl = entry_controls.iloc[0]
#             if currentControl:
#                 sql_statement = f'''
#                 SELECT *
#                 FROM {table_name}
#                 WHERE currentControl = '{currentControl}' or isProcessed = {isProcessed}
#                 ORDER BY navigationID ASC;
#                 '''
#                 results, columns = conn.Query(sql_statement)
#                 df = pd.DataFrame(results, columns=columns)
#     if df.empty:
#         print("No data found.")
#     else:
#         print(df)
#     return df

def queryControls(isProcessed=1):
    table_name = "windowsControls" if platform.system().lower() == "windows" else "macOSControls"
    
    conn = ConnectToDB()
    sql_statement = f'''
    SELECT *
    FROM {table_name}
    WHERE isProcessed = {isProcessed} ORDER BY navigationID ASC;
    '''
    results, columns = conn.Query(sql_statement)
    df = pd.DataFrame(results, columns=columns)
    return df

def queryProcessControls(isProcessed=0):
    table_name = "windowsControls" if platform.system().lower() == "windows" else "macOSControls"
    
    conn = ConnectToDB()
    sql_statement = f'''
    WITH RECURSIVE control_flow AS (
    SELECT *
    FROM {table_name}
    WHERE isProcessed = {isProcessed}
    UNION ALL
    SELECT c.*
    FROM {table_name} c
    INNER JOIN control_flow cf
    ON cf.entryControl = c.currentControl
    )
    SELECT * FROM control_flow ORDER BY navigationID ASC;
    '''
    results, columns = conn.Query(sql_statement)
    df = pd.DataFrame(results, columns=columns)

    if not df.empty:
        print(df)
    return df


def updateControl(navigationID, isProcessed=0):
    table_name = "windowsControls" if platform.system().lower() == "windows" else "macOSControls"

    conn = ConnectToDB()
    sql_statement = f'''
    UPDATE {table_name}
    SET isProcessed = {isProcessed}
    WHERE navigationID = {navigationID};
    '''
    try:
        conn.Execute(sql_statement)
    except Exception as e:
        return None
