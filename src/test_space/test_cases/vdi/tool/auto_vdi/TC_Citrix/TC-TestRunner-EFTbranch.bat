@echo off
setlocal DisableDelayedExpansion

set "HVD_INFO_FILE=C:\dev\auto_vdi\hvd_info.txt"
if not exist "%HVD_INFO_FILE%" (
	echo ERROR: %HVD_INFO_FILE% not found. Aborting.
	exit /b 1
)

set "EFTBRANCH="
for /f "tokens=1,* delims=:" %%a in ('findstr /b /i "eftbranch:" "%HVD_INFO_FILE%"') do set "EFTBRANCH=%%b"
for /f "tokens=* delims= " %%a in ("%EFTBRANCH%") do set "EFTBRANCH=%%a"
set "EFTBRANCH=%EFTBRANCH:/=%"
set "EFTBRANCH=%EFTBRANCH:\=%"

if defined EFTBRANCH (
	echo Running: call TestRunner-WRS-LastestV.bat eftbranch
	call TestRunner-WRS-LastestV.bat eftbranch
) else (
	echo Running: call TestRunner-WRS-LastestV.bat
	call TestRunner-WRS-LastestV.bat
)
