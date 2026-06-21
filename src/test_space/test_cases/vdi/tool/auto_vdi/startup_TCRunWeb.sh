#!/usr/bin/env bash
set -euo pipefail

cd /devOps/auto_vdi
source ./.venv/bin/activate
cd TC_Citrix
python WebexVDITCRunWeb-WRS.py run

