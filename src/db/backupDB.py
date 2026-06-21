from db.cloudMySQL.connectToMysql import CMysqlConnection
# sqls = [
#     f'''replace into RegressShield.bugInfo_backup select * from RegressShield.bugInfo;''',
# ]

# def backupDB():
#     dbConnection = ConnectToDB()
#     for sql in sqls:
#         dbConnection.Execute(sql)


import pandas as pd

def _listAllTablesCreateStatementOfOneDatabase(dbConnection,databaseName):
    res = dbConnection.Execute(f''' USE  {databaseName}''')
    resultSQLS  = [
        f'''CREATE DATABASE `{databaseName}`;''',
        f''' USE `{databaseName}`; ''',
    ]
    if res :
        results, _  = dbConnection.Query("show tables;")
        tableNames = [f[0] for f in results]
        for tableName in tableNames:
            sql = f'''show create table `{tableName}`;'''
            res = dbConnection.Query(sql)
            resultSQLS.append(res[0][0][1])
    
    return resultSQLS


def BackUpTables(oldDBConnection,dbConnection):
    exceptTables = ['information_schema','mysql','performance_schema','sys']
    results, _  = oldDBConnection.Query('''show databases;''')
    datebaseNames = [f[0] for f in results]
    sqls = []
    for name in datebaseNames:
        if name in exceptTables:
            continue

        sqlList = _listAllTablesCreateStatementOfOneDatabase(oldDBConnection,name)
        sqls.extend(sqlList)
    
    for sql in sqls:
        print(sql)
        res = dbConnection.Execute(sql)
        if not res:
            print(sql)
            break

def DataFrameToInsertSQLs(dataFrame,tableName):
    sqls = []        
    for _, row in dataFrame.iterrows():
        indexStr = '''`,`'''.join(row.index)
        valueStr = '''","'''.join(str(x).replace("'", "\\'").replace('"', '\\"') for x in row.values)
        sql = f'''INSERT IGNORE INTO {tableName} ( `{indexStr}`)  VALUES ("{valueStr}");'''
        sqls.append(sql)
    return sqls
    
def _backUpTableData(oldDBConnection,dbConnection,tableName):
    data, columns  = oldDBConnection.Query(f'''SELECT * FROM {tableName};''')
    df = pd.DataFrame(data,columns= columns)
    sqls= DataFrameToInsertSQLs(df,tableName)
    for sql in sqls:
        #print(sql)
        res = dbConnection.Execute(sql)
        if not res:
            print(sql)
            break

def BackUpDatas(oldDBConnection,dbConnection):
    exceptTables = ['information_schema','mysql','performance_schema','sys']
    results, _  = oldDBConnection.Query('''show databases;''')
    datebaseNames = [f[0] for f in results]
    for name in datebaseNames:
        if name in exceptTables:
            continue

        dbConnection.Execute(f''' USE `{name}`; ''')
        results, _  = dbConnection.Query(f'''show tables;''')
        tableNames = [f[0] for f in results]
        for tableName in tableNames:
            fullTableName = f'''`{name}`.`{tableName}`'''
            _backUpTableData(oldDBConnection,dbConnection,fullTableName)
            print(fullTableName)


def ConnectDBFrom():
    host = "10.140.216.252"
    port = 3306
    user = "test"
    password = "P@ss1234"
    dbName = "RegressShield"
    conn = CMysqlConnection(host, port, user, password, dbName)
    return conn


def ConnectDBTo():
    host = "wrs-sm.qa.webex.com"
    port = 3306
    user = "root"
    password = "pass"
    dbName = "sys"
    conn = CMysqlConnection(host, port, user, password, dbName)
    return conn


def BackUp():
    connFrom = ConnectDBFrom()
    connTo = ConnectDBTo()
    BackUpTables(connFrom,connTo)
    BackUpDatas(connFrom,connTo)

def BackupBySchemas(fromDBName="RegressShield",toDBName="RegressShield_backup"):
    connTo = ConnectDBTo()
    results, _  = connTo.Query('''show databases;''')
    datebaseNames = [f[0] for f in results]
    if fromDBName not in datebaseNames:
        print("source database not found:", fromDBName)
        return
    
    if toDBName in datebaseNames:
        msg = input(f'''The database {toDBName} already exists, do you want to drop it? [y/n]''')
        if msg.lower() == 'y':
            connTo.Execute(f'''DROP DATABASE IF EXISTS `{toDBName}`;''')
        else:
            print(f'''The database {toDBName} already exists, keep it.''')
            return
        
    connTo.Execute(f'''CREATE DATABASE `{toDBName}`;''')
    connTo.Execute(f''' USE  {fromDBName}''')
    results, _  = connTo.Query(f'''show tables;''')
    tableNames = [f[0] for f in results]
    createStatement = []
    for tableName in tableNames:
        sql = f'''show create table `{tableName}`;'''
        res = connTo.Query(sql)
        createStatement.append(res[0][0][1])

    connTo.Execute(f''' USE  {toDBName}''')
    for sql in createStatement:
        res = connTo.Execute(sql)

    for tableName in tableNames:
        sql = f'''INSERT INTO `{toDBName}`.`{tableName}` SELECT * FROM `{fromDBName}`.`{tableName}`;'''
        connTo.Execute(sql)
        print(f'''Backup table `{tableName}` from `{fromDBName}` to `{toDBName}` Done!''')

    print(f'''Backup from `{fromDBName}` to `{toDBName}` completed!''')

def _CreateUser(dbConnection):
    userName = 'triager'
    pwd = "pass1234"
    sqls = [
        f'''CREATE USER '{userName}'@'%' IDENTIFIED WITH mysql_native_password BY '{pwd}';''',
        f'''GRANT ALL ON *.* TO '{userName}'@'%' WITH GRANT OPTION;'''
    ]

    for sql in sqls:
        res = dbConnection.Execute(sql)
        if not res:
            print(sql)
            break

if __name__ == '__main__':
    ConnectDBFrom()
    #BackupFromMCToLocal()
    #BackupFromMCToTeams()
