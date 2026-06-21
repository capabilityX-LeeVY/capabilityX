@echo off
REM run_all_tests.bat
REM 
REM Master batch script to run all test suites sequentially
REM This script will execute all test categories one by one
REM

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================================
echo 🚀 ALL WEBEX TESTS SEQUENTIAL EXECUTION
echo ========================================================
echo.
echo Running all test suites in sequence:
echo   1. 🔇 Audio Setting Tests (3 tests)
echo   2. 📹 Video Setting Tests (3 tests)
echo   3. 💬 Chat Tests (4 tests)
echo   4. 🧪 Interaction Tests (4 tests)
echo   5. 📺 Screen Sharing Tests (2 tests)
echo.
echo Total: 16 tests across 5 categories
echo ⏰ Started at: %date% %time%
echo ========================================================

setlocal enabledelayedexpansion
set TOTAL_SUITES=5
set PASSED_SUITES=0
set FAILED_SUITES=0

REM Test Suite 1: Audio Setting
echo.
echo ========================================================
echo 🔇 SUITE 1/5: AUDIO SETTING TESTS
echo ========================================================
call run_audio_sequence.bat
if !errorlevel! == 0 (
    echo ✅ SUITE 1 PASSED: Audio Setting Tests
    set /a PASSED_SUITES+=1
) else (
    echo ❌ SUITE 1 FAILED: Audio Setting Tests
    set /a FAILED_SUITES+=1
)

echo.
echo ⏳ Waiting 10 seconds before next suite...
timeout /t 10 /nobreak >nul

REM Test Suite 2: Video Setting
echo.
echo ========================================================
echo 📹 SUITE 2/5: VIDEO SETTING TESTS
echo ========================================================
call run_video_sequence.bat
if !errorlevel! == 0 (
    echo ✅ SUITE 2 PASSED: Video Setting Tests
    set /a PASSED_SUITES+=1
) else (
    echo ❌ SUITE 2 FAILED: Video Setting Tests
    set /a FAILED_SUITES+=1
)

echo.
echo ⏳ Waiting 10 seconds before next suite...
timeout /t 10 /nobreak >nul

REM Test Suite 3: Chat
echo.
echo ========================================================
echo 💬 SUITE 3/5: CHAT TESTS
echo ========================================================
call run_chat_sequence.bat
if !errorlevel! == 0 (
    echo ✅ SUITE 3 PASSED: Chat Tests
    set /a PASSED_SUITES+=1
) else (
    echo ❌ SUITE 3 FAILED: Chat Tests
    set /a FAILED_SUITES+=1
)

echo.
echo ⏳ Waiting 10 seconds before next suite...
timeout /t 10 /nobreak >nul

REM Test Suite 4: Interaction
echo.
echo ========================================================
echo 🧪 SUITE 4/5: INTERACTION TESTS
echo ========================================================
call run_interaction_sequence.bat
if !errorlevel! == 0 (
    echo ✅ SUITE 4 PASSED: Interaction Tests
    set /a PASSED_SUITES+=1
) else (
    echo ❌ SUITE 4 FAILED: Interaction Tests
    set /a FAILED_SUITES+=1
)

echo.
echo ⏳ Waiting 10 seconds before next suite...
timeout /t 10 /nobreak >nul

REM Test Suite 5: Screen Sharing
echo.
echo ========================================================
echo 📺 SUITE 5/5: SCREEN SHARING TESTS
echo ========================================================
call run_share_sequence.bat
if !errorlevel! == 0 (
    echo ✅ SUITE 5 PASSED: Screen Sharing Tests
    set /a PASSED_SUITES+=1
) else (
    echo ❌ SUITE 5 FAILED: Screen Sharing Tests
    set /a FAILED_SUITES+=1
)

REM Final Summary
echo.
echo ========================================================
echo 🏁 ALL TESTS EXECUTION SUMMARY
echo ========================================================
echo ⏰ Completed at: %date% %time%
echo 📊 Total Test Suites: !TOTAL_SUITES!
echo ✅ Passed Suites: !PASSED_SUITES!
echo ❌ Failed Suites: !FAILED_SUITES!

set /a SUCCESS_RATE=!PASSED_SUITES! * 100 / !TOTAL_SUITES!
echo 📈 Suite Success Rate: !SUCCESS_RATE!%%

echo.
echo 📋 Suite Results Summary:
echo   🔇 Audio Setting: %AUDIO_RESULT%
echo   📹 Video Setting: %VIDEO_RESULT%
echo   💬 Chat: %CHAT_RESULT%
echo   🧪 Interaction: %INTERACTION_RESULT%
echo   📺 Screen Sharing: %SHARE_RESULT%

if !FAILED_SUITES! == 0 (
    echo.
    echo 🎉 ALL TEST SUITES PASSED! Complete Webex test execution successful.
    exit /b 0
) else (
    echo.
    echo ⚠️  !FAILED_SUITES! test suite^(s^) failed. Please review individual suite results above.
    exit /b 1
)
