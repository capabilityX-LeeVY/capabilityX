import shutil
import os

from datetime import datetime, timedelta
from config.config import DATA_RETENTION_DAYS
from config.paths import OUTPUT_ROOT

class OutputInitializer:
    def __init__(self, output_path=None):
        self.out_path = output_path or OUTPUT_ROOT
        self.timestamp_format = "%Y%m%d-%H%M%S"

    def setup(self):
        self._cleanup_old_outputs()
        os.makedirs(self.out_path, exist_ok=True)

    def _cleanup_old_outputs(self):
        if not self.out_path.exists():
            return

        threshold = datetime.now() - timedelta(DATA_RETENTION_DAYS)
        for child in self.out_path.iterdir():
            if child.is_dir():
                for subdir in child.iterdir():
                    if subdir.is_dir():
                        try:
                            folder_time = datetime.strptime(subdir.name, self.timestamp_format)
                            if folder_time < threshold:
                                shutil.rmtree(subdir, ignore_errors=True)
                        except ValueError:
                            continue
