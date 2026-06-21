@echo off
setlocal

set "DEPLOY_KEY=1234567890"
set "GIT_URL=git@github.com:user/webex-regress-shield.git"
set "REPO=%USERPROFILE%\workspace\webex-regress-shield"
set "RESTART_CODE=42"

set "GIT_SSH_COMMAND=ssh -i %DEPLOY_KEY% -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

if exist "%REPO%" (
    git -C "%REPO%" pull
) else (
    if not exist "%USERPROFILE%\workspace" mkdir "%USERPROFILE%\workspace"
    git clone "%GIT_URL%" "%REPO%"
)

set "PYTHONPATH=%REPO%\src"
cd /d "%REPO%\src"

:loop
python -u functions\api\server.py
if "%errorlevel%"=="%RESTART_CODE%" (
    timeout /t 2 /nobreak >nul
    goto loop
)
exit /b %errorlevel%
