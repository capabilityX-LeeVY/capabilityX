import pymysql
from common.utils.logger import LOGGER_ERROR

class CMysqlConnection(object):
    def __init__(self,host, port, user, password, dbName, charset = 'utf8mb4'):
        #print('connecting to mysql server...')
        self.db = None
        self.db = pymysql.connect(host= host, port=port,user=user, password=password,db=dbName, charset=charset)
        #print('conencted to mysql server successfully!')

    def __del__(self):
        if getattr(self, "db", None):
            #print('disconnect mysql server successfully!')
            self.db.close()


    def Query(self,sql_statement):
        if self.db is None:
            #print('Query failed, db is None')
            return ((),())

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            results = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            return (results,columns)
        except:
            LOGGER_ERROR ("Error: unable to fecth data","RED")
        
        return ((),())
    
    def QueryWithData(self, sql_statement, data):
        if self.db is None:
            return ((), ())

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, data)
            results = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            return (results, columns)
        except Exception as e:
            LOGGER_ERROR(f"Error: unable to fetch data: {e}", "RED")
        return ((), ())
        
    def Execute(self,sql_statement):
        if self.db is None:
            LOGGER_ERROR('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            LOGGER_ERROR(msg,"RED")
            self.db.rollback()
            return False
        
    def ExecuteWithData(self, sql_statement, data):
        if self.db is None:
            LOGGER_ERROR('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, data)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            LOGGER_ERROR(msg,"RED")
            self.db.rollback()
            return False
            
    def TableInfo(self):
        if self.db is None:
            return None
        cursor = self.db.cursor()
        columns = [item[0] for item in cursor.description]
        return columns
    
    def close(self):
        """Close database connection"""
        try:
            if self.db:
                self.db.close()
                self.db = None
        except Exception as e:
            LOGGER_ERROR(f"Error closing database connection: {e}")

if __name__ == "__main__":
    host = '10.140.218.56'
    port = 3306
    user = 'test'
    password = 'P@ss1234'
    dbName = 'RegressShield'
    dbconnection = CMysqlConnection(host,port,user,password,dbName)