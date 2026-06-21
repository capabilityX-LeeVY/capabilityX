import json

from common.handler.settingsHandler import DynamicConfig
from db.cloudMySQL.connectToMysql import CMysqlConnection
from config.paths import DB_CONFIG_PATH, SETTINGS_PATH
from typing import Optional

def ConnectToDB(env: Optional[str] = None) -> CMysqlConnection:
    settings = DynamicConfig(SETTINGS_PATH)
    db_config = DynamicConfig(DB_CONFIG_PATH)
    if env is None:
        env = settings.get('environment')
    if env is None:
        env = 'BTS'
    config = db_config.get('dbConfig')
    if config is None:
        raise ValueError("dbConfig is missing in the database configuration.")
    if env not in config:
        raise ValueError(f"Environment '{env}' not found in dbConfig.")
    db_config = config[env]

    host = db_config['host']
    port = db_config['port']
    user = db_config['user']
    password = db_config['password']
    dbName = db_config.get('dbName', db_config.get('database'))
    if dbName is None:
        raise KeyError(f"Neither 'dbName' nor 'database' found in dbConfig[{env}]")
    
    return CMysqlConnection(host, port, user, password, dbName)


def ConnectToJiraDB(database_name: str) -> CMysqlConnection:
    """
    Connect to JIRA crawler database with custom database name
    
    Args:
        database_name: Name of the database to connect to
        
    Returns:
        CMysqlConnection instance
    """
    settings = DynamicConfig(SETTINGS_PATH)
    db_config = DynamicConfig(DB_CONFIG_PATH)
    db_name = database_name
    config = db_config.get('dbConfig')
    
    if not config:
        raise ValueError("Database configuration 'dbConfig' not found in config file")
    db_config = config[db_name]
    print(f"Using database configuration for {db_name}")
    print(json.dumps(db_config, indent=4))
    host = db_config['host']
    port = db_config['port']
    user = db_config['user']
    password = db_config['password']
    
    print(f"Connecting to JIRA database {database_name} on {host}:{port} as {user}...")
    
    return CMysqlConnection(host, port, user, password, database_name)