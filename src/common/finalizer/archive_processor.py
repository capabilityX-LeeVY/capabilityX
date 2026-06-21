import os
import tarfile
import tempfile
import json
import requests
from urllib.parse import quote

from pathlib import Path
from datetime import datetime

import urllib3
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_DEBUG, LOGGER_ERROR
from config.paths import SETTINGS_PATH, SESSION_OUTPUT_PATH, OUTPUT_ROOT, REMOTE_STORAGE_CONFIG_PATH
from config.global_settings import settings
from common.handler.report_id_generator import report_id_generator
from common.utils import deviceInfo

class RemoteArchiveProcessor:
    def __init__(self):
        self.remote_storage = DynamicConfig(REMOTE_STORAGE_CONFIG_PATH)
        self.host = self._get("host")
        self.web_url = self._get("web_url")
        self.web_url_e2e = self._get("web_url_e2e")
        self.web_url_jmt = self._get("web_url_jmt")

        self.output_root = OUTPUT_ROOT
        self.settings = DynamicConfig(SETTINGS_PATH)
        self.full_version = self.settings.get("appVersion") or "0.0.0"
        self.short_version = '.'.join(self.full_version.split('.')[:3])
        self.test_suite = self.settings.get("test_suite")

    def _get(self, key, default=None):
        value = self.remote_storage.get(key)
        if value is None:
            if default is not None:
                return default
            LOGGER_ERROR(f"Missing required config key: {key}")
            raise ValueError(f"Missing config: {key}")
        return value
    
    def _set_info(self):
        now = datetime.now()
        info = {
            "appVersion": self.settings.get("appVersion"),
            "qtversion": settings.installOptions.get("qtversion"),
            "arch": settings.installOptions.get("arch"),
            "deviceOS": deviceInfo.getOSInfo(),
            "language": self.settings.get("language"),
            "workflow": self.settings.get("workflow"),
            "test_suite": self.settings.get("test_suite"),
            "test_batch": self.settings.get("test_batch"),
            "test_case": self.settings.get("test_case"),
            "reportId": report_id_generator.global_report_id,
            "runDate": f"{now.month}/{now.day}/{now.year}"
        }

        info_path = Path(SESSION_OUTPUT_PATH) / "wrs-job-info.json"
        try:
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=4, ensure_ascii=False)
            LOGGER_DEBUG(f"Session info written to {info_path}")
        except Exception as e:
            LOGGER_ERROR(f"Failed to write session info: {e}")


    def _create_archive(self, folder_path: str, root_path: str = str(SESSION_OUTPUT_PATH)) -> tuple[str, str, str]:
        folder_path = str(Path(folder_path).resolve())
        root_path = str(Path(root_path).resolve())
        archive_name = Path(folder_path).name + ".tar.gz"
        archive_path = Path(tempfile.gettempdir()) / archive_name
        LOGGER_DEBUG(f"Starting to create archive...")

        try:
            relative_path = Path(folder_path).relative_to(Path(root_path))
        except ValueError:
            LOGGER_ERROR(f"{folder_path} is not under root path {root_path}")
            raise

        arcname = Path(root_path).name / relative_path
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(folder_path, arcname=arcname)
        archive_folder = str(arcname)

        LOGGER_DEBUG(f"Archive created completely: {archive_path}")
        return str(archive_path), archive_name, archive_folder

    def upload_archive(self, local_folder=SESSION_OUTPUT_PATH):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self._set_info()
        archive_path, archive_name, archive_folder = self._create_archive(
            str(local_folder), root_path=str(local_folder.parent)
        )

        upload_url = f"https://{self.host}/report/api/upload"
        try:
            LOGGER_DEBUG(f"Uploading to {upload_url} ...")
            with open(archive_path, 'rb') as f:
                resp = requests.post(
                    upload_url,
                    data={'version': self.short_version},
                    files={'file': (archive_name, f, 'application/gzip')},
                    timeout=600,
                    verify=False
                )
            if resp.status_code != 200:
                LOGGER_ERROR(f"Upload failed: {resp.status_code} {resp.text}")
                return None
            result = resp.json()
            LOGGER_DEBUG(f"Upload succeeded (server path: {result.get('url', '')})")
            return self.get_report_url()
        except Exception as e:
            LOGGER_ERROR(f"Exception occurred: {e}")
            return None
        finally:
            try:
                os.remove(archive_path)
            except Exception:
                pass
        
    def get_report_url(self, local_folder=SESSION_OUTPUT_PATH, GT=False):
        try:
            relative_output_path = local_folder.relative_to(self.output_root).as_posix()
        except ValueError:
            relative_output_path = local_folder.name
        # URL-encode each path segment to handle spaces, parentheses, etc.
        encoded_output_path = "/".join(quote(seg, safe='') for seg in relative_output_path.split("/"))
        if GT:
            if self.test_suite == "acc_regression/jmt" or self.test_suite == "jmt":
                report_url = f"{self.web_url_jmt}/{self.short_version}/{encoded_output_path}"
            else:
                report_url = f"{self.web_url_e2e}/{self.short_version}/{encoded_output_path}"
                report_path = local_folder / "report"
                try:
                    files = os.listdir(report_path)
                    for filename in files:
                        if filename.endswith('.md'):
                            report_url = f"{report_url}/report/{quote(filename, safe='')}"
                            break
                except (OSError, FileNotFoundError):
                    LOGGER_ERROR(f"Report not found: {report_path}")
        else:
            report_url = f"{self.web_url}/{self.short_version}/{encoded_output_path}"
        return report_url