import pandas as pd
import re
import imagehash
import platform

from pathlib import Path
from PIL import Image, UnidentifiedImageError
from typing import Optional
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR
from config.config import CONTROL_DB
from db.cloudMySQL import accData as remote_db
from tools.markdownToDataframe import MarkdownToDataframe
from config.paths import SETTINGS_PATH
from common.handler.settingsHandler import DynamicConfig
from common.handler.report_id_generator import report_id_generator


class FocusRingDataSync:
    
    def __init__(self, md_files: Optional[list] = None):
        self.md_files = md_files
        self.settings = DynamicConfig(SETTINGS_PATH)
        self.os_info = self._getOS()
        self.workflow = self.settings.get("workflow")
        self.app_version = self.settings.get("appVersion")
        self.language = self.settings.get("language") if self.settings.get("language") else "en_US"
        self.report_id = report_id_generator.global_report_id
        self.onfocus_md = None
        self.lostfocus_md = None
        self.onfocus_df = pd.DataFrame()
        self.lostfocus_df = pd.DataFrame()

    def _getOS(self) -> str:
        os = platform.system().lower()
        if os == "windows":
            return "Windows"
        elif os == "darwin":
            return "MacOS"
        return "Unknown"
    
    def _getImagePath(self, row: pd.Series, md_file_path):
        if "Image" not in row or pd.isna(row["Image"]):
            return None 
        img_html = str(row["Image"])
        match = re.search(r'src\s*=\s*"([^"]+)"', img_html)
        if match:
            imgRelPath = match.group(1).replace("\\", "/")
            mdPath = Path(md_file_path).parent
            imgFullPath = (mdPath / imgRelPath).resolve()
            return imgFullPath
        return None

    def _getImageData(self,image_path):
        try:
            img = Image.open(image_path)
            # imgWhash = str(imagehash.whash(img))
            imgPhash = str(imagehash.phash(img))
            with open(image_path, "rb") as f:
                imgBytes = f.read()
            return imgPhash, imgBytes
        except (UnidentifiedImageError, OSError):
            return None, None
    
    def _get_deduplicated_non_compliant(self, df: pd.DataFrame) -> tuple:
        non_compliant = df[df['Compliance'].str.contains('❌', na=False)]
        unknown_df = non_compliant[non_compliant['Control Name'] == 'unknown']
        non_unknown_df = non_compliant[non_compliant['Control Name'] != 'unknown']
        non_unknown_unique_df = non_unknown_df.drop_duplicates(subset=['Control Name'])
        deduplicated_df = pd.concat([unknown_df, non_unknown_unique_df], ignore_index=True)
        total_count = len(deduplicated_df)
        
        return total_count, deduplicated_df
    
    def sync_data(self):
        if not self.workflow:
            return
        
        if not self.md_files:
            LOGGER_WARNING("No focus ring files.")
            return
        
        for md_file in self.md_files:
            if 'onfocus' in md_file.name.lower():
                self.onfocus_md = md_file
            elif 'lostfocus' in md_file.name.lower():
                self.lostfocus_md = md_file
        
        self.onfocus_df = MarkdownToDataframe.MarkdownToDataframe(self.onfocus_md) if self.onfocus_md else pd.DataFrame()
        self.lostfocus_df = MarkdownToDataframe.MarkdownToDataframe(self.lostfocus_md) if self.lostfocus_md else pd.DataFrame()
        
        if self.onfocus_df.empty and self.lostfocus_df.empty:
            LOGGER_WARNING("No data extracted from focus ring summary.")
            return
        
        if not self.onfocus_df.empty and 'Compliance' in self.onfocus_df.columns and 'Control Name' in self.onfocus_df.columns:
            onfocus_deduplicate_non_compliant, onfocus_deduplicated_df = self._get_deduplicated_non_compliant(self.onfocus_df)
        else:
            onfocus_deduplicate_non_compliant, onfocus_deduplicated_df = 0, pd.DataFrame()
        
        if not self.lostfocus_df.empty and 'Compliance' in self.lostfocus_df.columns and 'Control Name' in self.lostfocus_df.columns:
            lostfocus_deduplicate_non_compliant, lostfocus_deduplicated_df = self._get_deduplicated_non_compliant(self.lostfocus_df)
        else:
            lostfocus_deduplicate_non_compliant, lostfocus_deduplicated_df = 0, pd.DataFrame()
        
        onfocus_compliant = int(self.onfocus_df['Compliance'].str.contains('✅', na=False).sum()) if not self.onfocus_df.empty and 'Compliance' in self.onfocus_df.columns else 0
        onfocus_non_compliant = int(self.onfocus_df['Compliance'].str.contains('❌', na=False).sum()) if not self.onfocus_df.empty and 'Compliance' in self.onfocus_df.columns else 0
        lostfocus_compliant = int(self.lostfocus_df['Compliance'].str.contains('✅', na=False).sum()) if not self.lostfocus_df.empty and 'Compliance' in self.lostfocus_df.columns else 0
        lostfocus_non_compliant = int(self.lostfocus_df['Compliance'].str.contains('❌', na=False).sum()) if not self.lostfocus_df.empty and 'Compliance' in self.lostfocus_df.columns else 0
        
        onfocus_accept = int(self.onfocus_df['Compliance'].str.contains('☑️', na=False).sum()) if not self.onfocus_df.empty and 'Compliance' in self.onfocus_df.columns else 0
        lostfocus_accept = int(self.lostfocus_df['Compliance'].str.contains('☑️', na=False).sum()) if not self.lostfocus_df.empty and 'Compliance' in self.lostfocus_df.columns else 0

        summary_data = None
        summary_data = (self.workflow,
                onfocus_compliant,
                onfocus_non_compliant,
                onfocus_deduplicate_non_compliant,
                onfocus_accept,
                lostfocus_compliant,
                lostfocus_non_compliant,
                lostfocus_deduplicate_non_compliant,
                lostfocus_accept,
                self.app_version,
                self.os_info,
                self.language,
                self.report_id
                )
        if summary_data:
            remote_db.createFocusRingSummaryTable(CONTROL_DB)
            remote_db.insertDataToFocusRingSummary(summary_data, dbName=CONTROL_DB)

        non_compliant_data = []
        
        for _, row in onfocus_deduplicated_df.iterrows():
            img_path = self._getImagePath(row, self.onfocus_md)
            img_whash, img_bytes = self._getImageData(img_path) if img_path else (None, None)
            
            item = (
                img_bytes,
                img_whash,
                row.get('Control Name', None),
                row.get('Analysis Result', None),
                row.get('Compliance', None),
                row.get('Reference', None),
                row.get('Suggestion', None),
                True,
                self.workflow,
                self.app_version,
                self.os_info,
                self.language,
                self.report_id
            )
            non_compliant_data.append(item)
        
        for _, row in lostfocus_deduplicated_df.iterrows():
            img_path = self._getImagePath(row, self.lostfocus_md)
            img_whash, img_bytes = self._getImageData(img_path) if img_path else (None, None)
            
            item = (
                img_bytes,
                img_whash,
                row.get('Control Name', None),
                row.get('Analysis Result', None),
                row.get('Compliance', None),
                row.get('Reference', None),
                row.get('Suggestion', None),
                False,
                self.workflow,
                self.app_version,
                self.os_info,
                self.language,
                self.report_id
            )
            non_compliant_data.append(item)
        if non_compliant_data:
            remote_db.createNonCompliantFocusRingTable(CONTROL_DB)
            remote_db.insertDataToNonompliantFocusRing(non_compliant_data, dbName=CONTROL_DB)

# def store_focus_ring_summary(md_files: Optional[list] = None):
#     store = FocusRingDataStore(md_files)
#     store.store_data_to_remote()