# stop_test.ps1 — Kill running WRS test process
# Usage: pwsh scripts/stop_test.ps1
# Finds and terminates any running run_test_case_job.py process and its children.

$found = $false

# Find python processes running run_test_case_job.py
$processes = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python" -and $_.CommandLine -match "run_test_case_job"
}

foreach ($proc in $processes) {
    $found = $true
    $pid_val = $proc.ProcessId
    $cmd = $proc.CommandLine
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host "    Found running test process (PID $pid_val)" -ForegroundColor Yellow
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host "    $cmd" -ForegroundColor DarkGray

    # Kill child processes first
    $children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $pid_val }
    foreach ($child in $children) {
        Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
    }

    # Kill the main process
    Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "    Test process stopped successfully." -ForegroundColor Green
    Write-Host ""
}

if (-not $found) {
    Write-Host ""
    Write-Host "    No running test process found." -ForegroundColor Cyan
    Write-Host ""
}
