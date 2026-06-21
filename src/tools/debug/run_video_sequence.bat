@echo off
REM run_video_sequence.bat
REM 
REM Batch script to run all 3 video setting tests sequentially
REM This script will execute each test one by one and show results
REM

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================================
echo 📹 VIDEO SETTING TESTS SEQUENTIAL EXECUTION
echo ========================================================
echo.
echo Running 3 video setting test cases in sequence:
echo   1. test_pre_meeting_video_settings
echo   2. test_in_meeting_video_settings
echo   3. test_video_control_complete_workflow
echo.
echo ⏰ Started at: %date% %time%
echo ========================================================

setlocal enabledelayedexpansion
set TOTAL_TESTS=3
set PASSED_TESTS=0
set FAILED_TESTS=0

REM Test 1: Pre-Meeting Video Settings
echo.
echo ========================================================
echo 🧪 Test 1/3: test_pre_meeting_video_settings
echo ========================================================
python run_test_simple.py --case meetings/video_setting/test_pre_meeting_video_settings
if !errorlevel! == 0 (
    echo ✅ Test 1 PASSED: test_pre_meeting_video_settings
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 1 FAILED: test_pre_meeting_video_settings
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 2: In-Meeting Video Settings
echo.
echo ========================================================
echo 🧪 Test 2/3: test_in_meeting_video_settings
echo ========================================================
python run_test_simple.py --case meetings/video_setting/test_in_meeting_video_settings
if !errorlevel! == 0 (
    echo ✅ Test 2 PASSED: test_in_meeting_video_settings
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 2 FAILED: test_in_meeting_video_settings
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 3: Complete Video Control Workflow
echo.
echo ========================================================
echo 🧪 Test 3/3: test_video_control_complete_workflow
echo ========================================================
python run_test_simple.py --case meetings/video_setting/test_video_control_complete_workflow
if !errorlevel! == 0 (
    echo ✅ Test 3 PASSED: test_video_control_complete_workflow
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 3 FAILED: test_video_control_complete_workflow
    set /a FAILED_TESTS+=1
)

REM Final Summary
echo.
echo ========================================================
echo 🏁 VIDEO SETTING TESTS EXECUTION SUMMARY
echo ========================================================
echo ⏰ Completed at: %date% %time%
echo 📊 Total Tests: !TOTAL_TESTS!
echo ✅ Passed: !PASSED_TESTS!
echo ❌ Failed: !FAILED_TESTS!

set /a SUCCESS_RATE=!PASSED_TESTS! * 100 / !TOTAL_TESTS!
echo 📈 Success Rate: !SUCCESS_RATE!%%

if !FAILED_TESTS! == 0 (
    echo.
    echo 🎉 ALL TESTS PASSED! Video setting test suite completed successfully.
    exit /b 0
) else (
    echo.
    echo ⚠️  !FAILED_TESTS! test^(s^) failed. Please review the results above.
    exit /b 1
)
