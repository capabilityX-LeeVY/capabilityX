#!/usr/bin/env bash
set -euo pipefail

VERSION_FILE="/devOps/auto_vdi/n-4_GA_version.txt"

if [ ! -f "$VERSION_FILE" ]; then
    echo "ERROR: version file not found: $VERSION_FILE"
    exit 1
fi

has_versions=false
has_failures=false
while IFS= read -r N4_VERSION; do
    N4_VERSION=${N4_VERSION%$'\r'}
    N4_VERSION=$(echo "$N4_VERSION" | xargs)
    if [ -z "$N4_VERSION" ]; then
        continue
    fi
    has_versions=true
    if ! bash "$(dirname "$0")/TestRunner-WRS-LastestV.sh" "$N4_VERSION"; then
        echo "ERROR: TestRunner failed for version: $N4_VERSION"
        has_failures=true
    fi
done < "$VERSION_FILE"

if [ "$has_versions" = false ]; then
    echo "ERROR: version file is empty: $VERSION_FILE"
    exit 1
fi

if [ "$has_failures" = true ]; then
    exit 1
fi
