@echo off
REM run_chat_sequence.bat
REM 
REM Batch script to run all 4 chat tests sequentially
REM This script will execute each test one by one and show results
REM

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================================
echo 💬 CHAT TESTS SEQUENTIAL EXECUTION
echo ========================================================
echo.
echo Running 4 chat test cases in sequence:
echo   1. test_chat_in_pmr_meeting
echo   2. test_chat_in_webex_meeting
echo   3. test_chat_with_popout_and_popin
echo   4. test_chat_and_layout_workflow
echo.
echo ⏰ Started at: %date% %time%
echo ========================================================

setlocal enabledelayedexpansion
set TOTAL_TESTS=4
set PASSED_TESTS=0
set FAILED_TESTS=0

REM Test 1: Chat in PMR Meeting
echo.
echo ========================================================
echo 🧪 Test 1/4: test_chat_in_pmr_meeting
echo ========================================================
python run_test_simple.py --case meetings/chat/test_chat_in_pmr_meeting
if !errorlevel! == 0 (
    echo ✅ Test 1 PASSED: test_chat_in_pmr_meeting
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 1 FAILED: test_chat_in_pmr_meeting
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 2: Chat in Webex Meeting
echo.
echo ========================================================
echo 🧪 Test 2/4: test_chat_in_webex_meeting
echo ========================================================
python run_test_simple.py --case meetings/chat/test_chat_in_webex_meeting
if !errorlevel! == 0 (
    echo ✅ Test 2 PASSED: test_chat_in_webex_meeting
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 2 FAILED: test_chat_in_webex_meeting
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 3: Chat with Popout and Popin
echo.
echo ========================================================
echo 🧪 Test 3/4: test_chat_with_popout_and_popin
echo ========================================================
python run_test_simple.py --case meetings/chat/test_chat_with_popout_and_popin
if !errorlevel! == 0 (
    echo ✅ Test 3 PASSED: test_chat_with_popout_and_popin
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 3 FAILED: test_chat_with_popout_and_popin
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 4: Chat and Layout Workflow
echo.
echo ========================================================
echo 🧪 Test 4/4: test_chat_and_layout_workflow
echo ========================================================
python run_test_simple.py --case meetings/chat/test_chat_and_layout_workflow
if !errorlevel! == 0 (
    echo ✅ Test 4 PASSED: test_chat_and_layout_workflow
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 4 FAILED: test_chat_and_layout_workflow
    set /a FAILED_TESTS+=1
)

REM Final Summary
echo.
echo ========================================================
echo 🏁 CHAT TESTS EXECUTION SUMMARY
echo ========================================================
echo ⏰ Completed at: %date% %time%
echo 📊 Total Tests: !TOTAL_TESTS!
echo ✅ Passed: !PASSED_TESTS!
echo ❌ Failed: !FAILED_TESTS!

set /a SUCCESS_RATE=!PASSED_TESTS! * 100 / !TOTAL_TESTS!
echo 📈 Success Rate: !SUCCESS_RATE!%%

if !FAILED_TESTS! == 0 (
    echo.
    echo 🎉 ALL TESTS PASSED! Chat test suite completed successfully.
    exit /b 0
) else (
    echo.
    echo ⚠️  !FAILED_TESTS! test^(s^) failed. Please review the results above.
    exit /b 1
)
