import pandas as pd
import platform
import sqlite3
from typing import Optional
from config.paths import DB_PATH
from config.mysql import ConnectToDB
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH, DB_CONFIG_PATH,data_path
from common.utils.logger import LOGGER_WARNING


def createFocusRingSummaryTable(dbName: Optional[str] = None):
    conn = ConnectToDB(dbName)
    sql_statement = """
    CREATE TABLE IF NOT EXISTS focus_ring_summary (
        summary_id SERIAL PRIMARY KEY,
        workflow VARCHAR(64),
        onfocus_compliant INT,
        onfocus_non_compliant INT,
        onfocus_deduplicate_non_compliant INT,
        onfocus_accept INT,
        lostfocus_compliant INT,
        lostfocus_non_compliant INT,
        lostfocus_deduplicate_non_compliant INT,
        lostfocus_accept INT,
        app_version VARCHAR(32),
        platform VARCHAR(64),
        language VARCHAR(16),
        report_id VARCHAR(128),
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn.Execute(sql_statement)
    except Exception as e:
        LOGGER_WARNING(f"Failed to create table: {e}")

def createNonCompliantFocusRingTable(dbName: Optional[str] = None):
    conn = ConnectToDB(dbName)
    sql_statement = """
    CREATE TABLE IF NOT EXISTS non_compliant_focus_ring (
        id SERIAL PRIMARY KEY,
        image MEDIUMBLOB,
        image_whash VARCHAR(64),
        control_name VARCHAR(255),
        analysis_result TEXT,
        compliance VARCHAR(32),
        reference TEXT,
        suggestion TEXT,
        is_onfocus_control BOOLEAN,
        workflow VARCHAR(64),
        app_version VARCHAR(32),
        platform VARCHAR(64),
        language VARCHAR(16),
        report_id VARCHAR(128),
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_whash_focus_workflow (image_whash, is_onfocus_control, workflow)
    );
    """
    try:
        conn.Execute(sql_statement)
    except Exception as e:
        LOGGER_WARNING(f"Failed to create table: {e}")

def insertDataToFocusRingSummary(data, dbName: Optional[str] = None):
    conn = ConnectToDB(dbName)
    sql_statement = '''
        INSERT INTO focus_ring_summary (
            workflow,
            onfocus_compliant,
            onfocus_non_compliant,
            onfocus_deduplicate_non_compliant,
            onfocus_accept,
            lostfocus_compliant,
            lostfocus_non_compliant,
            lostfocus_deduplicate_non_compliant,
            lostfocus_accept,
            app_version,
            platform,
            language,
            report_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    try:
        conn.ExecuteWithData(sql_statement, data)
    except Exception as e:
        return None

def insertDataToNonompliantFocusRing(data, dbName: Optional[str] = None):
    conn = ConnectToDB(dbName)
    sql_statement = '''
        INSERT INTO non_compliant_focus_ring (
            image,
            image_whash,
            control_name,
            analysis_result,
            compliance,
            reference,
            suggestion,
            is_onfocus_control,
            workflow,
            app_version,
            platform,
            language,
            report_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    try:
        if isinstance(data, list):
            for item in data:
                conn.ExecuteWithData(sql_statement, item)
        else:
            conn.ExecuteWithData(sql_statement, data)
    except Exception as e:
        LOGGER_WARNING(f"Failed to insert data to non-compliant_focus_ring: {e}")
        return None

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

def fetchAcceptedImages(dbName: Optional[str] = None, expected_focus_state: Optional[str] = None):
    """
    Fetch accepted control images from MySQL database.
    
    Args:
        dbName: Optional database name to connect to
        expected_focus_state: Optional filter for expected focus state (e.g., 'onfocus', 'lostfocus')
        
    Returns:
        pandas.DataFrame: Result set containing img_hash and other columns
    """
    try:
        conn = ConnectToDB(dbName)
        if expected_focus_state:
            safe_focus_state = expected_focus_state.replace("'", "''")
            sql_statement = f"""
                SELECT * FROM accepted_control_img 
                WHERE img_hash IS NOT NULL AND expected_focus_state = '{safe_focus_state}' AND value = 1
            """
        else:
            sql_statement = """
                SELECT * FROM accepted_control_img WHERE img_hash IS NOT NULL AND value = 1
            """
        results, columns = conn.Query(sql_statement)
        if not results:
            # LOGGER_WARNING("No accepted control images found in database")
            return pd.DataFrame()
        df = pd.DataFrame(results, columns=columns)
        # LOGGER_WARNING(f"Found {len(df)} accepted control images")
        return df
        
    except Exception as e:
        LOGGER_WARNING(f"Error fetching accepted control images: {e}")
        return pd.DataFrame()    

def getControlInfo(table_name):
    mysql_conn = ConnectToDB()
    results, columns = mysql_conn.Query(f"SELECT * FROM {table_name};")
    df = pd.DataFrame(results, columns=columns)
    df.to_excel(data_path / f'''{table_name}.xlsx''', index=False)
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
    # table_name = "navigation_mac_deep_DailyRun_zh_CN_InMeeting"
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
