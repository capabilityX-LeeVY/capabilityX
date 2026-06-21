#!/usr/bin/env bash
set -euo pipefail

export WEBEX_VDI_ARTIFACTORY_TOKEN="${WEBEX_VDI_ARTIFACTORY_TOKEN:-cmVmdGtuOjAxOjE3NzY2NTAwNDI6amR3RVhONXhybEJoOXZ6c3Y5Z09zMDE3T1A2}"

# Usage examples:
#   TestRunner-WRS-LastestV.sh
#     -> GA app + GA plugin (latest)
#   TestRunner-WRS-LastestV.sh 46.3.0.12345
#     -> GA app + specified plugin
#   TestRunner-WRS-LastestV.sh eftbranch
#     -> EFT app (hvd_info.txt eftbranch) + EFT plugin
#   TestRunner-WRS-LastestV.sh 46.3.0.12345 eftbranch
#     -> EFT app (hvd_info.txt eftbranch) + specified plugin

WORK_DIR="/devOps/auto_vdi/TC_Citrix"
cd "$WORK_DIR" || exit 1

HVD_INFO_FILE="/devOps/auto_vdi/hvd_info.txt"
if [ ! -f "$HVD_INFO_FILE" ]; then
    echo "ERROR: $HVD_INFO_FILE not found. Aborting."
    exit 1
fi

read_hvd_value() {
    local key="$1"
    grep -m1 "^${key}:" "$HVD_INFO_FILE" | cut -d':' -f2- | tr -d '\r' | xargs
}

read_eftbranch_value() {
    local raw
    raw=$(grep -m1 "^eftbranch:" "$HVD_INFO_FILE" | cut -d':' -f2- | tr -d '\r')
    raw=$(echo "$raw" | tr -d ' /\\=' | xargs)
    echo "$raw"
}

SF_URL=$(read_hvd_value "sf_url")
USERNAME=$(read_hvd_value "username")
PWD=$(read_hvd_value "pwd")
DOMAIN=$(read_hvd_value "domain")
VM_GROUP=$(read_hvd_value "vm_group")
HVD_IP=$(read_hvd_value "hvd_ip")

if [ -z "$SF_URL" ] || [ -z "$USERNAME" ] || [ -z "$PWD" ] || [ -z "$DOMAIN" ] || [ -z "$VM_GROUP" ] || [ -z "$HVD_IP" ]; then
    echo "ERROR: sf_url, username, pwd, domain, vm_group, or hvd_ip is missing in $HVD_INFO_FILE. Aborting."
    exit 1
fi

OUTPUT_DIR="output"
LOG_DIR="$OUTPUT_DIR/pipefail"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi
find "$LOG_DIR" -type f -name "error_*.log" -mtime +7 -delete
LOG_FILE="$LOG_DIR/error_$(date +%Y%m%d%H%M).log"
echo "===== Start: $(date) | Args: $* =====" >> "$LOG_FILE"
trap 'echo "ERROR: command failed at line $LINENO: $BASH_COMMAND" | tee -a "$LOG_FILE"' ERR

sleep 2
pkill -f wfica || true
sleep 2
pkill -f vmware-view || true
sleep 2

echo
echo "===== Current date/time: $(date) ====="
echo "New Test Run is started..."

EFTBRANCH=""
EFTBRANCH_PRESENT=false
PLUGIN_VERSION=""
PLUGIN_VERSION_PROVIDED=false
for arg in "$@"; do
    if [ "$arg" = "eftbranch" ]; then
        EFTBRANCH_PRESENT=true
    else
        if [ -z "$PLUGIN_VERSION" ]; then
            PLUGIN_VERSION="$arg"
        fi
        PLUGIN_VERSION_PROVIDED=true
    fi
done

if [ "$EFTBRANCH_PRESENT" = true ]; then
    EFTBRANCH=$(read_eftbranch_value)
    if [ -z "$EFTBRANCH" ]; then
        echo "ERROR: eftbranch is missing in $HVD_INFO_FILE. Aborting."
        exit 1
    fi
fi

if [ -n "$EFTBRANCH" ]; then
    WbxVDI_LatestV=$(python3 WebexVDIgetLatestVer.py --eftbranch "$EFTBRANCH")
else
    WbxVDI_LatestV=$(python3 WebexVDIgetLatestVer.py)
fi

if [ -z "$PLUGIN_VERSION" ]; then
    echo "Latest Webex App version: $WbxVDI_LatestV"
    echo "Latest VDI Plugin version: $WbxVDI_LatestV"
    if [ "$EFTBRANCH_PRESENT" = true ]; then
        echo "EFT app + EFT plugin selected."
    else
        echo "Latest app + latest plugin selected."
    fi
    PluginVersion="$WbxVDI_LatestV"
else
    echo "Start N-4 Testing with Webex App version: $WbxVDI_LatestV"
    echo "Specified VDI Plugin version: $PLUGIN_VERSION"
    if [ "$EFTBRANCH_PRESENT" = true ]; then
        echo "EFT app + specified plugin selected."
    else
        echo "Latest app + specified plugin selected."
    fi
    PluginVersion="$PLUGIN_VERSION"
fi

sleep 5
echo "Deploying VDI Plugin..."
python3 WebexVDIgetVdiPlugin.py -v "$PluginVersion"
if [ $? -ne 0 ]; then
    exit 1
fi

sleep 5
python3 WebexVDIgetICA.py -s "$SF_URL" -i "automation.ica" -u "$USERNAME" -p "$PWD" -d "$DOMAIN" -a "$VM_GROUP"
if [ ! -f "automation.ica" ]; then
    echo "ERROR: automation.ica not found. Aborting."
    exit 1
fi

echo "Connecting to HVD..."
bash /opt/Citrix/ICAClient/wfica.sh automation.ica &

sleep 10
echo "Running Test Cases..."

echo "Testing Meeting scenarios..."
RunTs=$(date +%Y%m%d%H%M)
OutputFile="$OUTPUT_DIR/output_${WbxVDI_LatestV}_${PluginVersion}_${RunTs}.txt"

if [ "$PLUGIN_VERSION_PROVIDED" = false ]; then
    # plugin version not provided
    python3 WebexVDITCRunner-WRS.py -s "$HVD_IP" -v "$WbxVDI_LatestV" -pv "$WbxVDI_LatestV" -tc vdi_linux_meeting_sanity_testing-main -o output.txt --deployTeamsWindows yes --vdi-env Citrix
else
    # plugin version provided
    python3 WebexVDITCRunner-WRS.py -s "$HVD_IP" -v "$WbxVDI_LatestV" -pv "$PluginVersion" -tc vdi_linux_meeting_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Citrix
fi

if [ -f "output.txt" ]; then
    cp -f "output.txt" "$OutputFile"
fi


sleep 5
python3 WebexVDIgetICA.py -s "$SF_URL" -i "automation.ica" -u "$USERNAME" -p "$PWD" -d "$DOMAIN" -a "$VM_GROUP"
if [ ! -f "automation.ica" ]; then
    echo "ERROR: automation.ica not found. Aborting."
    exit 1
fi

echo "Connecting to HVD..."

echo "Testing Calling scenarios..."
RunTs=$(date +%Y%m%d%H%M)
OutputFile="$OUTPUT_DIR/output_${WbxVDI_LatestV}_${PluginVersion}_${RunTs}.txt"

if [ "$PLUGIN_VERSION_PROVIDED" = false ]; then
    # plugin version not provided
    python3 WebexVDITCRunner-WRS.py -s "$HVD_IP" -v "$WbxVDI_LatestV" -pv "$WbxVDI_LatestV" -tc vdi_linux_calling_sanity_testing-main -o output.txt --deployTeamsWindows yes --vdi-env Citrix
else
    # plugin version provided
    python3 WebexVDITCRunner-WRS.py -s "$HVD_IP" -v "$WbxVDI_LatestV" -pv "$PluginVersion" -tc vdi_linux_calling_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Citrix
fi

if [ -f "output.txt" ]; then
    cp -f "output.txt" "$OutputFile"
fi