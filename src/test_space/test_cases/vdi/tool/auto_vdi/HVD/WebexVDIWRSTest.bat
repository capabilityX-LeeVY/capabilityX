@echo off

REM Add firewall rule to allow Webex traffic
netsh advfirewall firewall add rule name="Webex" dir=in action=allow program="C:\program files\cisco spark\ciscocollabhost.exe" enable=yes profile=any

cd C:\dev\webex-regress-shield

REM Timeout is 3600s
set "TIMEOUT_MS=3600000"

setlocal enabledelayedexpansion
set "testcase=%1"
set "account_prefix="

REM Read account from calling_info.txt and extract substring before @
if exist "C:\dev\auto_vdi\calling_info.txt" (
    for /f "tokens=2 delims=:" %%a in ('type C:\dev\auto_vdi\calling_info.txt ^| findstr /i "tc_account"') do (
        set "account_line=%%a"
        set "account_line=!account_line:~1!"
        for /f "tokens=1 delims=@" %%b in ("!account_line!") do (
            set "account_prefix=%%b"
        )
    )
)

if "!testcase:_meeting_=!" neq "!testcase!" (
    REM Contains vdi_meeting - use original command with -k -ts
    echo Running command: uv run python src/run_test_case_job.py -k -ts "%1" ^> C:\dev\auto_vdi\HVD\output.txt 2^>^&1
    powershell -NoProfile -Command "$p=Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','uv run python src/run_test_case_job.py -k -ts "%1" > C:\dev\auto_vdi\HVD\output.txt 2>&1' -NoNewWindow -PassThru; if(!$p.WaitForExit(%TIMEOUT_MS%)){ taskkill /PID $p.Id /T /F | Out-Null; exit 1 } else { exit $p.ExitCode }"
    if errorlevel 1 exit /b %errorlevel%
) else if "!testcase:_calling_=!" neq "!testcase!" (
    REM Contains vdi_calling - use command with account from calling_info.txt
    echo Running command: uv run python src/run_test_case_job.py -k -account !account_prefix! -ts "%1" ^> C:\dev\auto_vdi\HVD\output.txt 2^>^&1
    powershell -NoProfile -Command "$p=Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','uv run python src/run_test_case_job.py -k -account !account_prefix! -ts "%1" > C:\dev\auto_vdi\HVD\output.txt 2>&1' -NoNewWindow -PassThru; if(!$p.WaitForExit(%TIMEOUT_MS%)){ taskkill /PID $p.Id /T /F | Out-Null; exit 1 } else { exit $p.ExitCode }"
    if errorlevel 1 exit /b %errorlevel%
)

endlocal
