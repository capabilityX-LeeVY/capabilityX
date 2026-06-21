#!/usr/bin/env bash
set -euo pipefail

URL="http://127.0.0.1:5000/runtestN?eftbranch=1"
OUT_FILE="${OUT_FILE:-/tmp/http_response.txt}"
HTTP_STATUS=0

if command -v curl >/dev/null 2>&1; then
    HTTP_STATUS=$(curl -fsS --max-time 30 -w "%{http_code}" -o "$OUT_FILE" "$URL" || echo 0)
elif command -v wget >/dev/null 2>&1; then
    RESP=$(wget -q -T 30 --server-response -O "$OUT_FILE" "$URL" 2>&1 || true)
    HTTP_STATUS=$(echo "$RESP" | awk '/^  HTTP/{code=$2} END{print code+0}')
else
    echo "ERROR: curl or wget is required"
    exit 1
fi

if [ -f "$OUT_FILE" ]; then
    echo "Saved response to $OUT_FILE"
    echo "HTTP status: $HTTP_STATUS"
else
    echo "Request failed."
fi
