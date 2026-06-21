@echo off
setlocal DisableDelayedExpansion
cd C:\dev\auto_vdi\TC_Horizon

rem Usage examples:
rem   TestRunner-WRS-LastestV.bat
rem     -> GA app + GA plugin (latest)
rem   TestRunner-WRS-LastestV.bat 46.3.0.12345
rem     -> GA app + specified plugin
rem   TestRunner-WRS-LastestV.bat eftbranch
rem     -> EFT app (hvd_info.txt eftbranch) + EFT plugin
rem   TestRunner-WRS-LastestV.bat 46.3.0.12345 eftbranch
rem     -> EFT app (hvd_info.txt eftbranch) + specified plugin

set "HVD_INFO_FILE=C:\dev\auto_vdi\hvd_info-horizon.txt"
set "HORIZON_HVD_ACCESS_FILE=C:\dev\auto_vdi\TC_Horizon\horizon_hvd_access.txt"
if not exist "%HVD_INFO_FILE%" (
    echo ERROR: %HVD_INFO_FILE% not found. Aborting.
    exit /b 1
)
if not exist "%HORIZON_HVD_ACCESS_FILE%" (
    echo ERROR: %HORIZON_HVD_ACCESS_FILE% not found. Aborting.
    exit /b 1
)

for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "sf_url:" "%HVD_INFO_FILE%"') do set "SF_URL=%%b"
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "username:" "%HVD_INFO_FILE%"') do set "USERNAME=%%b"
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "pwd:" "%HVD_INFO_FILE%"') do set "PWD=%%b"
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "domain:" "%HVD_INFO_FILE%"') do set "DOMAIN=%%b"
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "vm_group:" "%HVD_INFO_FILE%"') do set "VM_GROUP=%%b"
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "hvd_ip:" "%HVD_INFO_FILE%"') do set "HVD_IP=%%b"

for %%v in (SF_URL USERNAME PWD DOMAIN VM_GROUP HVD_IP) do call :trim_var %%v
rem Keep original values (do not strip colons).

if "%SF_URL%"=="" (
    echo ERROR: sf_url is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)
if "%USERNAME%"=="" (
    echo ERROR: username is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)
if "%PWD%"=="" (
    echo ERROR: pwd is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)
if "%DOMAIN%"=="" (
    echo ERROR: domain is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)
if "%VM_GROUP%"=="" (
    echo ERROR: vm_group is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)
if "%HVD_IP%"=="" (
    echo ERROR: hvd_ip is missing in %HVD_INFO_FILE%. Aborting.
    exit /b 1
)

ping 127.0.0.1 -n 3 > nul
taskkill /f /t /im wfica32.exe
ping 127.0.0.1 -n 3 > nul
taskkill /f /t /im horizon-client.exe
ping 127.0.0.1 -n 3 > nul
taskkill /f /t /im horizon-protocol.exe
ping 127.0.0.1 -n 3 > nul

echo.
echo ===== Current date/time: %DATE% %TIME% =====
echo HVD_INFO_FILE: %HVD_INFO_FILE%
echo HORIZON_HVD_ACCESS_FILE: %HORIZON_HVD_ACCESS_FILE%
echo New Test Run is started...
echo Uninstalling existing Webex VDI Plugin...
wmic product where name="Webex VDI Plug-in" call uninstall

set "EFTBRANCH="
set "EFTBRANCH_PRESENT="
set "PLUGIN_VERSION="
set "PLUGIN_VERSION_PROVIDED="
for %%A in (%*) do call :parse_args "%%~A"

if defined EFTBRANCH_PRESENT (
    for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "$line = Get-Content -Path '%HVD_INFO_FILE%' | Select-String -Pattern '^eftbranch:' | Select-Object -First 1; if ($line) { $value = $line.ToString().Split(':',2)[1]; $value = $value -replace '[\s/\\=]',''; Write-Output $value }"`) do set "EFTBRANCH=%%a"
    if not defined EFTBRANCH (
        echo ERROR: eftbranch is missing in %HVD_INFO_FILE%. Aborting.
        exit /b 1
    )
)

if defined EFTBRANCH (
    for /f "delims=" %%i in ('python WebexVDIgetLatestVer.py --eftbranch %EFTBRANCH%') do set WbxVDI_LatestV=%%i
) else (
    for /f "delims=" %%i in ('python WebexVDIgetLatestVer.py') do set WbxVDI_LatestV=%%i
)
:: echo Latest Webex App version: %WbxVDI_LatestV%

if not defined PLUGIN_VERSION (
    echo Latest Webex App version: %WbxVDI_LatestV%
    echo Latest VDI Plugin version: %WbxVDI_LatestV%
    if defined EFTBRANCH_PRESENT (
        echo EFT app + EFT plugin selected.
    ) else (
        echo Latest app + latest plugin selected.
    )
    set "PLUGIN_VERSION=%WbxVDI_LatestV%"
) else (
    echo Start N-4 Testing with Webex App version: %WbxVDI_LatestV%
    echo Specified VDI Plugin version: %PLUGIN_VERSION%
    if defined EFTBRANCH_PRESENT (
        echo EFT app + specified plugin selected.
    ) else (
        echo Latest app + specified plugin selected.
    )
)


ping 127.0.0.1 -n 5 > nul
echo Deploying VDI Plugin...

echo Running: python WebexVDIgetVdiPlugin.py -v %PLUGIN_VERSION%
python WebexVDIgetVdiPlugin.py -v %PLUGIN_VERSION%
if errorlevel 1 exit /b %errorlevel%


ping 127.0.0.1 -n 5 > nul
echo Connecting to HVD...
start "" "C:\Program Files\Omnissa\Omnissa Horizon Client\horizon-client.exe" -file "%HORIZON_HVD_ACCESS_FILE%"

ping 127.0.0.1 -n 20 > nul
echo Running Test Cases...

echo Testing Meeting scenarios...
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmm"') do set "RunTs=%%t"
if not exist "output" mkdir "output"
set "OutputFile=output\output_%WbxVDI_LatestV%_%PLUGIN_VERSION%_%RunTs%.txt"

if not defined PLUGIN_VERSION_PROVIDED (
    REM %1 does NOT exist
    echo Running: python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %WbxVDI_LatestV% -tc vdi_windows_meeting_sanity_testing-main -o output.txt --deployTeamsWindows yes --vdi-env Horizon
    python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %WbxVDI_LatestV% -tc vdi_windows_meeting_sanity_testing-main  -o output.txt --deployTeamsWindows yes --vdi-env Horizon	
) else (
    REM %1 exists
    echo Running: python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %PLUGIN_VERSION% -tc vdi_windows_meeting_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Horizon
    python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %PLUGIN_VERSION% -tc vdi_windows_meeting_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Horizon
)

if exist "output.txt" copy /y "output.txt" "%OutputFile%" > nul


ping 127.0.0.1 -n 5 > nul
echo Connecting to HVD...
start "" "C:\Program Files\Omnissa\Omnissa Horizon Client\horizon-client.exe" -file "%HORIZON_HVD_ACCESS_FILE%"

echo Testing Calling scenarios...
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmm"') do set "RunTs=%%t"
if not exist "output" mkdir "output"
set "OutputFile=output\output_%WbxVDI_LatestV%_%PLUGIN_VERSION%_%RunTs%.txt"

if not defined PLUGIN_VERSION_PROVIDED (
    REM %1 does NOT exist
    echo Running: python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %WbxVDI_LatestV% -tc vdi_windows_calling_sanity_testing-main -o output.txt --deployTeamsWindows yes --vdi-env Horizon
    python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %WbxVDI_LatestV% -tc vdi_windows_calling_sanity_testing-main  -o output.txt --deployTeamsWindows yes --vdi-env Horizon	
) else (
    REM %1 exists
    echo Running: python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %PLUGIN_VERSION% -tc vdi_windows_calling_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Horizon
    python WebexVDITCRunner-WRS.py -s %HVD_IP% -v %WbxVDI_LatestV% -pv %PLUGIN_VERSION% -tc vdi_windows_calling_sanity_testing_N-4 -o output.txt --deployTeamsWindows yes --vdi-env Horizon
)

if exist "output.txt" copy /y "output.txt" "%OutputFile%" > nul

exit /b 0

:trim_var
setlocal DisableDelayedExpansion
for /f "tokens=1* delims==" %%i in ('cmd /v:off /c set %1 2^>nul') do (
    if /i "%%i"=="%1" (
        endlocal & set "%1=%%j"
        goto :eof
    )
)
endlocal
goto :eof

:parse_args
for /f "tokens=1 delims==" %%B in ("%~1") do (
    if /i "%%B"=="eftbranch" (
        set "EFTBRANCH_PRESENT=1"
    ) else (
        if not defined PLUGIN_VERSION set "PLUGIN_VERSION=%~1"
        set "PLUGIN_VERSION_PROVIDED=1"
    )
)
goto :eof