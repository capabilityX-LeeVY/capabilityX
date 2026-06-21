@echo off
REM run_share_sequence.bat
REM 
REM Batch script to run all 2 screen sharing tests sequentially
REM This script will execute each test one by one and show results
REM

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================================
echo 📺 SCREEN SHARING TESTS SEQUENTIAL EXECUTION
echo ========================================================
echo.
echo Running 2 screen sharing test cases in sequence:
echo   1. test_basic_screen_sharing
echo   2. test_screen_sharing_complete
echo.
echo ⏰ Started at: %date% %time%
echo ========================================================

setlocal enabledelayedexpansion
set TOTAL_TESTS=2
set PASSED_TESTS=0
set FAILED_TESTS=0

REM Test 1: Basic Screen Sharing
echo.
echo ========================================================
echo 🧪 Test 1/2: test_basic_screen_sharing
echo ========================================================
python run_test_simple.py --case meetings/share/test_basic_screen_sharing
if !errorlevel! == 0 (
    echo ✅ Test 1 PASSED: test_basic_screen_sharing
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 1 FAILED: test_basic_screen_sharing
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 2: Complete Screen Sharing
echo.
echo ========================================================
echo 🧪 Test 2/2: test_screen_sharing_complete
echo ========================================================
python run_test_simple.py --case meetings/share/test_screen_sharing_complete
if !errorlevel! == 0 (
    echo ✅ Test 2 PASSED: test_screen_sharing_complete
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 2 FAILED: test_screen_sharing_complete
    set /a FAILED_TESTS+=1
)

REM Final Summary
echo.
echo ========================================================
echo 🏁 SCREEN SHARING TESTS EXECUTION SUMMARY
echo ========================================================
echo ⏰ Completed at: %date% %time%
echo 📊 Total Tests: !TOTAL_TESTS!
echo ✅ Passed: !PASSED_TESTS!
echo ❌ Failed: !FAILED_TESTS!

set /a SUCCESS_RATE=!PASSED_TESTS! * 100 / !TOTAL_TESTS!
echo 📈 Success Rate: !SUCCESS_RATE!%%

if !FAILED_TESTS! == 0 (
    echo.
    echo 🎉 ALL TESTS PASSED! Screen sharing test suite completed successfully.
    exit /b 0
) else (
    echo.
    echo ⚠️  !FAILED_TESTS! test^(s^) failed. Please review the results above.
    exit /b 1
)
