#!/usr/bin/env bash
set -euo pipefail

DEPLOY_KEY="1234567890"
GIT_URL="${WRS_GIT_URL:-git@github.com:user/webex-regress-shield.git}"
REPO="${1:-${WRS_REPO:-$HOME/workspace/webex-regress-shield}}"
RESTART_CODE=42

export GIT_SSH_COMMAND="ssh -i $DEPLOY_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

if [ -d "$REPO" ]; then
    git -C "$REPO" pull
else
    mkdir -p "$(dirname "$REPO")"
    git clone "$GIT_URL" "$REPO"
fi

export PYTHONPATH="$REPO/src"
cd "$REPO/src"

while true; do
    "${WRS_PYTHON:-python}" -u functions/api/server.py
    rc=$?
    [ $rc -eq $RESTART_CODE ] && sleep 2 && continue
    break
done
