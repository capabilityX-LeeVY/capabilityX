import os
import re
import sys
import shutil
import sqlite3
import pandas as pd
import platform

from db.cloudMySQL import accData
from common.utils.logger import LOGGER_INFO
from config.paths import DB_PATH, CONTROL_SCREEN_READER_DATA_PATH, SETTINGS_PATH, I18N_STATUS, I18N_TYPES, I18N_LOCALE
from common.handler.settingsHandler import DynamicConfig
from common.i18n.locale_utils import LocaleManager
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler


class ScreenReaderDataProcessor:
    def __init__(self, db_path=DB_PATH):
        self.current_os = platform.system().lower()
        self.db_path = db_path
        self.raw_data = CONTROL_SCREEN_READER_DATA_PATH /'raw-data'
        os.makedirs(self.raw_data, exist_ok=True)
        self.test_case_db_handler = TestCaseDBHandler()
        # os.makedirs(self.to_be_analyzed_path, exist_ok=True)
        self.language = DynamicConfig(SETTINGS_PATH).get("language")
        self.i18n_state = DynamicConfig(I18N_STATUS)
        self.i18n_type = DynamicConfig(I18N_TYPES)
        self.locale_config = DynamicConfig(I18N_LOCALE)

        self._i18n_values_initialized = False
        self.i18n_checked = None
        self.i18n_unchecked = None
        self.i18n_selected = None
        self.i18n_unselected = None
        self.i18n_collapsed = None
        self.i18n_expanded = None

    def _ensure_i18n_values_initialized(self):
        if not self._i18n_values_initialized:
            self.language = DynamicConfig(SETTINGS_PATH).get("language")
            
            self.i18n_checked = self.get_i18n_state('checked')
            self.i18n_unchecked = self.get_i18n_state('unchecked')
            self.i18n_selected = self.get_i18n_state('selected')
            self.i18n_unselected = self.get_i18n_state('unselected')
            self.i18n_collapsed = self.get_i18n_state('collapsed')
            self.i18n_expanded = self.get_i18n_state('expanded')
            
            self._i18n_values_initialized = True

    def get_i18n_state(self, state_key):
        normalized_language = LocaleManager.normalize(self.language)
        value = self.i18n_state.get(normalized_language, "state", state_key, default=None)
        if value is not None:
            return value
        value = self.i18n_state.get("en_US", "state", state_key, default=f"[{state_key}]")
        return value
    
    def get_i18n_control_type(self, control_type_key):
        normalized_language = LocaleManager.normalize(self.language)

        value = self.i18n_type.get(normalized_language, "control_types", control_type_key, default=None)
        if value is not None:
            return value
        value = self.i18n_type.get("en_US", "control_types", control_type_key, default=f"[{control_type_key}]")
        return value
    
    def get_i18n_unknown_description(self):
        from core.mac.RSSkipMgr import CRSSikipMgr
        i18n_config = CRSSikipMgr.ReadConfig()
        if i18n_config and "specialNames" in i18n_config:
            unknown_description = i18n_config["specialNames"].get("AXUnknownDescription", "")
        else:
            unknown_description = ""
        return unknown_description

    def windows_data(self):
        conn = sqlite3.connect(self.db_path)
        query_all = '''
            SELECT * FROM (
                SELECT 
                    "Description",
                    "TabOrder", 
                    "ControlType",
                    "ControlLocalizedType",
                    "LegacyValue", 
                    "CollapseState",
                    "LegacyState", 
                    "FullDescription", 
                    "AccessKey", 
                    "Level",
                    ROW_NUMBER() OVER (PARTITION BY "Description" ORDER BY "TabOrder") AS rn
                FROM "ControlINFO"
                ) 
            WHERE rn = 1
            ORDER BY "TabOrder", "Description";
        '''
        df_all = pd.read_sql_query(query_all, conn)
        df_all.drop_duplicates(subset=['Description'], keep='first', inplace=True)
        df_all = self._preprocess_windows_df(df_all)

        levels = sorted(df_all['Level'].unique())
        file_name_path = None
        for level in levels:
            df_level = df_all[df_all['Level'] == level][['order', 'screenReader']]
            if not df_level.empty:
                file_name = f'{self.raw_data}/Windows_level{(level):02d}'
                file_name_path = self._split_and_save(df_level, file_name)
                LOGGER_INFO(f">>> Processing control hierarchy level {level}...")
        conn.close()

        return file_name_path

    def windows_data_for_cloud_db(self, report_id, sr_enabled_cases=None):
        results = self.test_case_db_handler.get_navigate_report_data(report_id)        
        if results.empty:
            LOGGER_INFO("No data found in the database")
            return
        
        # Filter out test cases that should not be analyzed for screen reader
        # These cases have check_points: [] which means no checkpoints should be executed
        excluded_cases = ['install_app', 'uninstall_app', 're-install_app']
        
        # Filter by test_case column (case-insensitive partial match)
        if 'test_case' in results.columns:
            original_count = len(results)
            results = results[~results['test_case'].str.lower().str.contains('|'.join([case.lower() for case in excluded_cases]), na=False)]
            filtered_count = original_count - len(results)
            if filtered_count > 0:
                LOGGER_INFO(f"Filtered out {filtered_count} rows from install/uninstall/reinstall cases for screen reader analysis", "CYAN")
        
        # Filter to only include cases that have Screen Reader in their check_points
        if sr_enabled_cases is not None and 'test_case' in results.columns:
            original_count = len(results)
            results = results[results['test_case'].isin(sr_enabled_cases)]
            filtered_count = original_count - len(results)
            if filtered_count > 0:
                LOGGER_INFO(f"Filtered out {filtered_count} rows from cases without Screen Reader check point", "CYAN")
            LOGGER_INFO(f"Screen reader analysis will process {len(results)} rows from SR-enabled cases: {sr_enabled_cases}", "CYAN")
        
        if results.empty:
            LOGGER_INFO("No data remaining after filtering")
            return
            
        results = self._preprocess_windows_df_for_sr(results)
        df_level = results[['order', 'screenReader']]
        file_name = f'{self.raw_data}/windows_control_datasets'
        file_name_path = self._split_and_save(df_level, file_name)
        return file_name_path

    def macos_data(self):
        results = accData.selectNavigationData()
        if results.empty:
            LOGGER_INFO("No data found in the database")
            return

        results = self._preprocess_macos_df(results)

        for level in results['level'].unique():
            df_level = results[results['level'] == level][['order', 'screenReader']]
            file_name = f'{self.raw_data}/macOS_level{(level):02d}'
            file_name_path = self._split_and_save(df_level, file_name)
        
        return file_name_path

    def get_screen_reader_data(self):
        if self.current_os == 'windows':
            file_name_path = self.windows_data()
            return file_name_path
        elif self.current_os == 'darwin':
            file_name_path = self.macos_data()
            return file_name_path

    def get_screen_reader_data_for_cloud(self, report_id, sr_enabled_cases=None):
        if self.current_os == 'windows':
            file_name_path = self.windows_data_for_cloud_db(report_id, sr_enabled_cases=sr_enabled_cases)
            return file_name_path
        elif self.current_os == 'darwin':
            self.macos_data()

    def _preprocess_windows_df(self, df, field_mapping=None):
        """
            Windows DataFrame
        Args:
            df: needed to process DataFrame
            field_mapping: field name mapping dictionary, if None, the default mapping (from ControlINFO table) is used
        """
        default_mapping = {
            'order': 'TabOrder',
            'Description': 'Description',
            'ControlLocalizedType': 'ControlLocalizedType',
            'FullDescription': 'FullDescription',
            'AccessKey': 'AccessKey',
            'LegacyValue': 'LegacyValue'
        }
        
        # Use provided mapping or default mapping
        mapping = field_mapping if field_mapping is not None else default_mapping
        
        # Field mapping and basic processing
        df['order'] = df[mapping['order']]
        df['Description'] = df[mapping['Description']].apply(lambda x: x.replace('\n', '') if x else '')
        # Strip zero-width characters from control type before processing
        _zwsp = '\u200b\u200c\u200d\ufeff'
        df['ControlLocalizedType'] = df[mapping['ControlLocalizedType']].apply(
            lambda x: '' if not x or (isinstance(x, str) and not x.strip(_zwsp).strip())
            else '' if x in ['menu item', 'tab item', 'custom', 'list item', 'text']
            else self.get_i18n_control_type(x.strip(_zwsp).strip()) if x else ''
        )
        df['FullDescription'] = df[mapping['FullDescription']].fillna('').apply(str.strip)
        df['AccessKey'] = df[mapping['AccessKey']].fillna('')
        
        # Optional fields: LegacyValue, LegacyState, CollapseState
        df['LegacyValue'] = df[mapping['LegacyValue']].fillna('') if ('LegacyValue' in mapping and mapping['LegacyValue'] in df.columns) else ''
        # Filter out LegacyValue that contains only zero-width chars or brackets with zero-width/whitespace content
        # e.g. "[​]" (brackets + U+200B zero-width space) from empty edit/password controls

        df['LegacyValue'] = df['LegacyValue'].apply(
            lambda v: '' if isinstance(v, str) and re.fullmatch(r'[\[\]\s\u200b\u200c\u200d\ufeff]*', v) else v
        )
        df['LegacyState'] = self._get_control_state(df) if ('LegacyState' in df.columns or 'ControlType' in df.columns) else ''
        df['CollapseState'] = self._get_control_collapse_state(df) if 'CollapseState' in df.columns else ''

        # Construct screenReader field
        def join_fields(row):
            fields = [str(x) for x in [row['Description'], row['ControlLocalizedType'],
                                       row['LegacyState'], row['LegacyValue'], row['CollapseState'],
                                       row['FullDescription'], row['AccessKey']] 
                     if x not in [None, 'None', 'N/A', '']]
            if not fields:
                return ''
            
            result = fields[0]
            for field in fields[1:]:
                if result and result[-1] in [',', '.']:
                    result += ' ' + field
                else:
                    result += ', ' + field
            
            return result

        df['screenReader'] = df.apply(join_fields, axis=1)
        return df
    
    def _preprocess_windows_df_for_sr(self, df):
        """
        Preprocess data for cloud database screen reader (compatible method)
        """
        field_mapping = {
            'order': 'step_order',
            'Description': 'current_control_name',
            'ControlLocalizedType': 'control_type',
            'FullDescription': 'full_description',
            'AccessKey': 'accessKey',
            'LegacyValue': 'legacy_value'
        }
        return self._preprocess_windows_df(df, field_mapping=field_mapping)

    def _preprocess_macos_df(self, df):
        self._ensure_i18n_values_initialized()
        unknown_description = self.get_i18n_unknown_description()
        df.loc[df['label'] == df['controlName'], 'label'] = None
        df.loc[(df['value'] == df['controlName']) & (df['role'] == 'AXTextField'), 'value'] = None
        df.loc[(df['selected'].notnull()) & (df['role'] == 'AXMenuButton'), 'help'] = None

        # df['selected'] = df['selected'].apply(lambda x: self.i18n_selected if str(x).strip().lower() == 'true' else None)
        exclude_list_roles = ['AXMenuItem', 'AXTextField']
        mask = (
            df['selected'].astype(str).str.strip().str.lower() == 'true'
        ) & ~df['role'].isin(exclude_list_roles)
        df['selected'] = df['selected'].where(mask, None)
        df.loc[mask, 'selected'] = self.i18n_selected

        mask_checked = df['role'].isin(['AXCheckBox', 'AXRadioButton'])
        df.loc[mask_checked, 'value'] = pd.to_numeric(df.loc[mask_checked, 'value'], errors='coerce').astype('Int64')
        df['checkStatus'] = None
        df.loc[mask_checked, 'checkStatus'] = df.loc[mask_checked, 'value'].apply(
            lambda v: self.i18n_checked if pd.notna(v) and v == 1 else self.i18n_unchecked if pd.notna(v) and v == 0 else None
        )

        mask = (df['parentRole'].notnull() &
                df['parentRole'].str.split(';').str[0].eq("AXTabGroup") &
                df['partString'].notnull())
        df.loc[mask, 'partString'] = df.loc[mask, 'partString'].str.strip()

        df.loc[
            (df['help'].notnull()) &
            ((df['help'].str.strip() == df['controlName'].str.strip()) |
             (df['help'].str.strip() == df['label'].str.strip())),
            'help'
        ] = None

        df.loc[df['roleDescription'].isin(unknown_description), 'roleDescription'] = None
        df['parentRole'] = None
        
        df.loc[(df['otherInfo'].notnull()) & (df['value'].isnull()),'value'] = df['otherInfo']
        input_roles = [
            'AXTextField', 'AXSecureTextField', 'AXTextArea', 'AXTextView',
            'AXSearchField', 'AXComboBox', 'AXTokenField', 'AXIncrementor', 'AXDateTimeArea'
        ]
        df.loc[~df['role'].isin(input_roles), 'value'] = None

        cols = ['value', 'controlName', 'selected', 'checkStatus', 'roleDescription',
        'parentRole', 'partString', 'label', 'help']
        df['screenReader'] = df[cols].fillna('').apply(
            lambda x: ', '.join(i for i in x if str(i).strip() not in ['', 'None']),
            axis=1
        )

        return df

    def _get_control_state(self, df):
        self._ensure_i18n_values_initialized()
        
        return [
            self.i18n_checked if (row['ControlType'] in [50002, 50013] and 
                        row['LegacyState'] == 1048596)
            else self.i18n_unchecked if row['ControlType'] in [50002, 50013]
            else ''
            for _, row in df.iterrows()
        ]
    
    def _get_control_collapse_state(self, df):
        self._ensure_i18n_values_initialized()
        
        state_map = {
            "0": self.i18n_collapsed,
            "1": self.i18n_expanded,
            "2": "partially expanded",
            "3": "leaf node"
        }
        return [
            state_map.get(row['CollapseState'], '') if pd.notna(row['CollapseState']) and row['CollapseState'] != 'None'
            else ''
            for _, row in df.iterrows()
        ]

    def _split_and_save(self, df, base_name, chunk_size=50):
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i: i + chunk_size]
            file_name = self._to_markdown(chunk, f"{base_name}_{(i // chunk_size) + 1}.md")
        return file_name

    def _to_markdown(self, df, file_name):
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write('| order | screenReader |\n')
            f.write('|-------|---------------|\n')
            for _, row in df.iterrows():
                f.write(f"| {row['order']} | {row['screenReader']} |\n")
        return file_name

    def _list_files(self, directory):
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    def _copy_files(self, src_dir, dst_dir, files):
        os.makedirs(dst_dir, exist_ok=True)
        for file in files:
            shutil.copy(os.path.join(src_dir, file), dst_dir)
        print(f"Copied {len(files)} files to {dst_dir}")
