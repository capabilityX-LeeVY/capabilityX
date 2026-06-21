@echo off
setlocal

set "URL=http://127.0.0.1:5000/runtestN"
set "OUT_FILE=%TEMP%\http_response.txt"

rem Fetch URL without launching a browser
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 30 | Select-Object -ExpandProperty Content | Out-File -FilePath '%OUT_FILE%' -Encoding UTF8; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"

if exist "%OUT_FILE%" (
  echo Saved response to %OUT_FILE%
) else (
  echo Request failed.
)

endlocal
