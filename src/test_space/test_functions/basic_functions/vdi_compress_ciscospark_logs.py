import os
from datetime import datetime
import py7zr


def vdi_compress_ciscospark_logs(output_dir=None):
    logs = os.path.join(os.environ["LOCALAPPDATA"], "CiscoSpark", "Logs")
    if not os.path.isdir(logs):
        raise FileNotFoundError(logs)

    if output_dir is None:
        output_dir = r"C:\dev\auto_vdi\HVD"

    out = os.path.join(
        output_dir,
#        f"CiscoSpark-Logs-{datetime.now():%Y%m%d-%H%M%S}.7z",
        f"CiscoSpark-Logs.7z",
    )

    with py7zr.SevenZipFile(out, "w") as archive:
        archive.writeall(logs, arcname="Logs")

    return out

