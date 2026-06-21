#!/usr/bin/env bash
# stop_test.sh — Kill running WRS test process on macOS / Linux
# Usage: bash scripts/stop_test.sh
# Finds and terminates any running run_test_case_job.py process and its children.

found=0

# Find python processes running run_test_case_job.py
while IFS= read -r line; do
    pid=$(echo "$line" | awk '{print $1}')
    if [ -z "$pid" ]; then
        continue
    fi

    found=1
    echo ""
    echo "  ============================================"
    echo "    Found running test process (PID $pid)"
    echo "  ============================================"
    ps -p "$pid" -o command= 2>/dev/null | head -1 | sed 's/^/    /'

    # Kill child processes first
    pkill -P "$pid" 2>/dev/null

    # Kill the main process
    kill -TERM "$pid" 2>/dev/null
    sleep 1
    # Force kill if still alive
    kill -KILL "$pid" 2>/dev/null

    echo ""
    echo "    Test process stopped successfully."
    echo ""
done < <(pgrep -af "run_test_case_job" 2>/dev/null | grep -v "$$" | awk '{print $1}')

if [ "$found" -eq 0 ]; then
    echo ""
    echo "    No running test process found."
    echo ""
fi
