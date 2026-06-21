import os
import re
import pandas as pd
import hashlib
import json
import pymysql
import requests
import mimetypes
import imagehash


from jira import JIRA
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from typing import Optional, Union
from types import SimpleNamespace

AUTHORIZATION = "Bearer NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G"
JIRA_token = 'NDcwMjEwNDU0NjU0Olkunv7VJrh+a0YGT9kq8f4tQI5G'


class AcceptImage(object):
    def __init__(self, img_info: Union[str, Path], img_file: Optional[Union[str, Path]] = None) -> None:
        host = 'gc-hgh05-level2-lab-irc-5.cisco.com'
        port = 3306
        user = 'test'
        password = 'pass'
        dbName = 'control_db'
        self.dbconnection = MysqlConnection(host,port,user,password,dbName)

        self.imgInfo = Path(img_info)
        self.img_file = Path(img_file) if img_file else None
            
        self.imgInfo = self._getImageInfo(self.imgInfo)
        self.imgControlName = self.imgInfo.controlName or "unknown"
        self.imgExpectedFocusState = self.imgInfo.expectedFocusState # e.g., "focused" or "unfocused"
        self.imgPlatform = self.imgInfo.platform
        self.imgAppVersion = self.imgInfo.appVersion
        self.imgLanguage = self.imgInfo.language
        self.imgAddBy = self.imgInfo.added_by

    def _getImageInfo(self, imageInfoFile: Path):
        if not imageInfoFile.exists():
            raise FileNotFoundError(f"Image info file not found: {imageInfoFile}")
        with open(imageInfoFile, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Image info is empty: {imageInfoFile}")
            data = json.loads(content, object_hook=lambda d: SimpleNamespace(**d))
            return data

    def _getImageData(self, image_path):
        try:
            img = Image.open(image_path)
            imgPhash = str(imagehash.phash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgPhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None
        
    def set(self):
        current_datetime = datetime.now()
        imgPhash, imgBytes = None, None
        if self.img_file and self.img_file.exists():
            imgPhash, imgBytes = self._getImageData(self.img_file)

        sql1 = f'''
            CREATE TABLE IF NOT EXISTS accepted_control_img (
            id SERIAL PRIMARY KEY,
            img_hash CHAR(64),
            img_bytes MEDIUMBLOB,
            value INT DEFAULT 1,
            control_name VARCHAR(255),
            expected_focus_state TEXT,
            platform VARCHAR(64),
            app_version VARCHAR(32),
            language VARCHAR(16) DEFAULT 'en_US',
            added_by VARCHAR(255) DEFAULT 'wrs',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        '''
        self.dbconnection.Execute(sql1)

        sql2 = f''' SELECT img_hash FROM control_db.accepted_control_img 
                    WHERE expected_focus_state = '{self.imgExpectedFocusState.lower()}' 
                    AND platform = '{self.imgPlatform}'; '''
        results, _ = self.dbconnection.Query(sql2)
        if results and imgPhash:
            current_hash = imagehash.hex_to_hash(imgPhash)
            for row in results:
                existing_hash_str = row[0]
                if existing_hash_str:
                    try:
                        existing_hash = imagehash.hex_to_hash(existing_hash_str)
                        hamming_distance = current_hash - existing_hash
                        if hamming_distance <= 5:
                            print(f"⚠️  Warning: Similar image found (Hamming distance: {hamming_distance}). Skipping insertion.")
                            return
                    except (ValueError, TypeError) as e:
                        continue
        
        sql3 = '''
        INSERT INTO control_db.accepted_control_img
        (img_hash, img_bytes, value, control_name, expected_focus_state, platform, app_version, language, added_by, added_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            imgPhash,
            imgBytes,
            1,
            self.imgControlName,
            self.imgExpectedFocusState.lower(),
            self.imgPlatform,
            self.imgAppVersion,
            self.imgLanguage,
            self.imgAddBy,
            current_datetime
        )
        try:
            self.dbconnection.ExecuteWithData(sql3, values)
        except Exception as e:
            print(f"⚠️  Warning: Failed to insert Jira info to database: {e}")


class MysqlConnection(object):
    def __init__(self,host, port, user, password, dbName, charset = 'utf8mb4'):
        self.db = pymysql.connect(host= host, port=port,user=user, password=password,db=dbName, charset=charset)

    def __del__(self):
        if self.db:
            self.db.close()

    def Query(self,sql_statement):
        if self.db is None:
            return ((),())

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            results = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            return (results,columns)
        except:
            print ("Error: unable to fecth data","RED")
        
        return ((),())
        
    def Execute(self,sql_statement):
        if self.db is None:
            print('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg,"RED")
            self.db.rollback()
            return False
        
    def ExecuteWithData(self, sql_statement, data):
        if self.db is None:
            print('Execute failed, db is None',"RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, data)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg,"RED")
            self.db.rollback()
            return False
            
    def TableInfo(self):
        if self.db is None:
            return None
        cursor = self.db.cursor()
        columns = [item[0] for item in cursor.description]
        return columns
    

if __name__ == "__main__":
    json_file = Path("/Users/weiqli/test data/api/test_accept_image.json")
    control_img = Path("/Users/weiqli/test data/20251202112006_Microsoft 365.png")
    
    jira = AcceptImage(
        img_info=json_file,
        img_file=control_img if control_img.exists() else None
    )
    
    jira.set()