import json
import yaml
import pandas as pd
import os
import threading
from typing import Optional

class GTMetaDataItem(object):
    def __init__(self):
        self.name = None
        self.control_name = None
        self.control_name_regex = None
        self.identifier = None
    
    def isEmpty(self):
        if self.control_name is None and self.control_name_regex is None and self.identifier is None:
            return True
        return False
        
    def toDict(self):
        ret_dict = {}
        if self.name is None:
            return ret_dict
        
        item_dict = {}
        if self.control_name is not None:
            item_dict["control_name"] = self.control_name
        if self.control_name_regex is not None:
            item_dict["control_name_regex"] = self.control_name_regex
        if self.identifier is not None:
            item_dict["identifier"] = self.identifier

        ret_dict[self.name] = item_dict

        return ret_dict
    
    def fromDict(self, dict_data):
        keys = list(dict_data.keys())
        self.name = keys[0]
        meta = dict_data.get(self.name, {})
        self.control_name = meta.get("control_name", None)
        self.control_name_regex = meta.get("control_name_regex", None)
        self.identifier = meta.get("identifier", None)

    def toSql(self):
        if self.isEmpty():
            return ""
        
        name = self.name.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')

        control_name = "NULL"
        if self.control_name is not None:
            control_name = self.control_name.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
            control_name = f"'{control_name}'"

        control_name_regex = "NULL"
        if self.control_name_regex is not None:
            control_name_regex = self.control_name_regex.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
            control_name_regex = f"'{control_name_regex}'"

        identifier = "NULL"
        if self.identifier is not None:
            identifier = self.identifier.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
            identifier = f"'{identifier}'"

        sql = f'''INSERT IGNORE INTO `RegressShield`.`gt_meta_data_mac` (`name`, `control_name`, `control_name_regex`, `identifier`) VALUES ('{name}', {control_name}, {control_name_regex}, {identifier});'''
        return sql

class GTMetaDataMgr(object):
    _instance_lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        if not hasattr(GTMetaDataMgr, "_instance"):
            with GTMetaDataMgr._instance_lock:
                if not hasattr(GTMetaDataMgr, "_instance"):
                    GTMetaDataMgr._instance = object.__new__(cls)
        return GTMetaDataMgr._instance
    
    def __init__(self):
        if not hasattr(self, "metadata_items"):
            self.metadata_items = {}

        if not hasattr(self, "l18nMetadata_items"):
            self.l18nMetadata_items = []

    def loadL18NFromYAMLFile(self):
        from config.paths import TEST_CONTROL_DATASET_FOLDER_PATH
        folder = TEST_CONTROL_DATASET_FOLDER_PATH
        yamlPath = os.path.join(folder, "gt_meta_data_mac_l18n.yaml")

        res = []
        if os.path.exists(yamlPath) == False:
            return res

        with open(yamlPath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            res = data.get("GT_meta_data_l18n_mac", [])

        return res
    
    def convertToL18NToYAMLFile(self):
        from config.paths import TEST_CONTROL_DATASET_FOLDER_PATH
        folder = TEST_CONTROL_DATASET_FOLDER_PATH
        yamlPath = os.path.join(folder, "gt_meta_data_mac_l18n.yaml")
        
        self.l18nMetadata_items = self.loadL18NFromYAMLFile()
        metaData_items = self.get_all_metadata_items()
        yaml_data_keys = [key for item in self.l18nMetadata_items for key in item.keys()]
        for name, item in metaData_items.items():
            if item.isEmpty():
                continue
            
            if item.control_name is not None:
                if item.control_name not in yaml_data_keys:
                    l18n_item = {}
                    l18n_item[item.control_name] = {}
                    l18n_item[item.control_name]["en_US"] = item.control_name
                    self.l18nMetadata_items.append(l18n_item)
                    continue
            
            if item.control_name_regex is not None:
                if item.control_name_regex not in yaml_data_keys:
                    l18n_item = {}
                    l18n_item[item.control_name_regex] = {}
                    l18n_item[item.control_name_regex]["en_US"] = item.control_name_regex
                    self.l18nMetadata_items.append(l18n_item)
                    continue

        with open(yamlPath, 'w', encoding='utf-8') as file:
            yaml.dump({"GT_meta_data_l18n_mac": self.l18nMetadata_items}, file, allow_unicode=True, indent=2, default_flow_style=False)
            #print(f"L18N data saved to {yamlPath}, Done")

        with open(yamlPath, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if line.startswith('GT_l18n_mac:'):
                    f.write(line)
                else:
                    f.write('  ' + line)


    def add_metadata_item(self, item: GTMetaDataItem):
        self.metadata_items[item.name] = item

    def get_metadata_item_by_name(self, name: str)-> Optional[GTMetaDataItem] :
        if name in self.metadata_items:
            return self.metadata_items[name]
        return None
    
    def get_all_metadata_items(self):
        return self.metadata_items
    
    def fromDict(self, dict_data):
        for name in dict_data:
            metadata_item = GTMetaDataItem()
            metadata_item.name = name
            if metadata_item.name in self.metadata_items:
                continue
            
            # don't load other fields from json, set them to None
            metadata_item.control_name = None
            metadata_item.control_name_regex = None
            metadata_item.identifier = None
            self.add_metadata_item(metadata_item)

    def fromJSONFile(self, json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            self.fromDict(data)
                

    def FromYAMLFile(self, yaml_file_path):
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            metadata_list = data.get("GT_meta_data_mac", [])
            for item in metadata_list:
                metadata_item = GTMetaDataItem()
                metadata_item.fromDict(item)
                if metadata_item.name in self.metadata_items:
                    continue
                self.add_metadata_item(metadata_item)


    def toYaml(self):
        yaml_data = []
        empty_datas = []
        for name,item in self.metadata_items.items():
            if item.name is None or name == "":
                continue
            item_dict = item.toDict()
            if item.isEmpty():
                empty_datas.append(item_dict)
            else:
                yaml_data.append(item_dict)

        yaml_data.extend(empty_datas)
        return yaml_data
    
    def toYamlFile(self, yaml_file_path):
        yaml_data = self.toYaml()
        with open(yaml_file_path, 'w', encoding='utf-8') as file:
            yaml.dump({"GT_meta_data_mac": yaml_data}, file, allow_unicode=True, indent=2, default_flow_style=False)
            #print(f"Converted data saved to {yaml_file_path}, Done")

        with open(yaml_file_path, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if line.startswith('GT_meta_data_mac:'):
                    f.write(line)
                else:
                    f.write('  ' + line)

    def fromDataFrame(self, df:pd.DataFrame):
        for _, row in df.iterrows():
            metadata_item = GTMetaDataItem()
            metadata_item.name = str(row["name"])
            control_name = row.get("control_name", None)
            if pd.isna(control_name) == False:
                metadata_item.control_name = str(control_name)
            control_name_regex = row.get("control_name_regex", None)
            if pd.isna(control_name_regex) == False:
                metadata_item.control_name_regex = str(control_name_regex)
            identifier = row.get("identifier", None)
            if pd.isna(identifier) == False:
                metadata_item.identifier = str(identifier)

            if metadata_item.name in self.metadata_items:
                continue
            self.add_metadata_item(metadata_item)

    def toSql(self):
        sql_data = []
        for _, item in self.metadata_items.items():
            sql = item.toSql()
            if sql == "":
                continue
            sql_data.append(sql)
        return sql_data
    

    @staticmethod
    def LoadAndSaveGTMetaData(dbConnection = None,save_to_db=False):
        from config.paths import TEST_CONTROL_DATASET_FOLDER_PATH
        folder = TEST_CONTROL_DATASET_FOLDER_PATH
        json_file_path = os.path.join(folder, "control_datasets.json")
        yaml_file_path = os.path.join(folder, "gt_meta_data_mac.yaml")
        gt_meta_mgr = GTMetaDataMgr()

        if os.path.exists(yaml_file_path):
            #load from yaml first
            gt_meta_mgr.FromYAMLFile(yaml_file_path)
        
        if dbConnection is not None:
            #load from db second
            sql = "SELECT * FROM `RegressShield`.`gt_meta_data_mac`;"
            results, columns = dbConnection.Query(sql)
            df = pd.DataFrame(data=results, columns=columns)
            gt_meta_mgr.fromDataFrame(df)

        #load from json last
        gt_meta_mgr.fromJSONFile(json_file_path)

        #save to yaml 
        gt_meta_mgr.toYamlFile(yaml_file_path)

        gt_meta_mgr.convertToL18NToYAMLFile()

        if dbConnection is not None and save_to_db:
            #save to db
            sqls = gt_meta_mgr.toSql()
            steps = 1
            batch_sqls = []
            for i in range(0, len(sqls), steps):
                batch_sql = sqls[i:i+steps]
                batch_sqls.append(('\n').join(batch_sql))

            for sql in batch_sqls:
                try:
                    dbConnection.Execute(sql)
                except Exception as e:
                    print(f"Failed to execute SQL: {sql}, Error: {str(e)}")
        
        return gt_meta_mgr

    @staticmethod
    def getL18NMetadataByName(key: str, lang="en_US"):
        if lang == "en_US":
            return key
        
        gt_meta_mgr = GTMetaDataMgr()
        #gt_meta_mgr.convertToL18NToYAMLFile()

        for item in gt_meta_mgr.l18nMetadata_items:
            if key in item:
                translations = item.get(key, {})
                if lang in translations:
                    return translations[lang]
        return None
        
    
if __name__ == "__main__":
    gt_meta_mgr = GTMetaDataMgr()
    # gt_meta_mgr.fromJSONFile("/Volumes/Data/Code/WebexRegressSheild/src/test_space/datasets/control_datasets.json")
    # yaml_data = gt_meta_mgr.toYaml()
    #gt_meta_mgr.toYamlFile("gt_meta_data_mac.yaml")
    gt_meta_mgr.FromYAMLFile("gt_meta_data_mac.yaml")
    gt_meta_mgr.toSql()
    # gt_meta_mgr.FromYAMLFile("gt_meta_data_mac.yaml")
    # yaml_data = gt_meta_mgr.toYaml()
    # with open("gt_meta_data_mac_out.yaml", 'w', encoding='utf-8') as file:
    #     yaml.dump({"GT_meta_data_mac": yaml_data}, file, allow_unicode=True)