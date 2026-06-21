@echo off
REM run_interaction_sequence.bat
REM 
REM Batch script to run all 4 interaction tests sequentially
REM This script will execute each test one by one and show results
REM

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================================
echo 🧪 INTERACTION TESTS SEQUENTIAL EXECUTION
echo ========================================================
echo.
echo Running 4 interaction test cases in sequence:
echo   1. test_single_reaction_thumbs_up
echo   2. test_raise_hand_basic
echo   3. test_raise_lower_hand_complete  
echo   4. test_meeting_reactions_complete
echo.
echo ⏰ Started at: %date% %time%
echo ========================================================

setlocal enabledelayedexpansion
set TOTAL_TESTS=4
set PASSED_TESTS=0
set FAILED_TESTS=0

REM Test 1: Single Reaction Thumbs Up
echo.
echo ========================================================
echo 🧪 Test 1/4: test_single_reaction_thumbs_up
echo ========================================================
python run_test_simple.py --case meetings/interaction/test_single_reaction_thumbs_up
if !errorlevel! == 0 (
    echo ✅ Test 1 PASSED: test_single_reaction_thumbs_up
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 1 FAILED: test_single_reaction_thumbs_up
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 2: Raise Hand Basic
echo.
echo ========================================================
echo 🧪 Test 2/4: test_raise_hand_basic
echo ========================================================
python run_test_simple.py --case meetings/interaction/test_raise_hand_basic
if !errorlevel! == 0 (
    echo ✅ Test 2 PASSED: test_raise_hand_basic
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 2 FAILED: test_raise_hand_basic
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 3: Raise Lower Hand Complete
echo.
echo ========================================================
echo 🧪 Test 3/4: test_raise_lower_hand_complete
echo ========================================================
python run_test_simple.py --case meetings/interaction/test_raise_lower_hand_complete
if !errorlevel! == 0 (
    echo ✅ Test 3 PASSED: test_raise_lower_hand_complete
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 3 FAILED: test_raise_lower_hand_complete
    set /a FAILED_TESTS+=1
)

echo.
echo ⏳ Waiting 5 seconds before next test...
timeout /t 5 /nobreak >nul

REM Test 4: Meeting Reactions Complete
echo.
echo ========================================================
echo 🧪 Test 4/4: test_meeting_reactions_complete
echo ========================================================
python run_test_simple.py --case meetings/interaction/test_meeting_reactions_complete
if !errorlevel! == 0 (
    echo ✅ Test 4 PASSED: test_meeting_reactions_complete
    set /a PASSED_TESTS+=1
) else (
    echo ❌ Test 4 FAILED: test_meeting_reactions_complete
    set /a FAILED_TESTS+=1
)

REM Final Summary
echo.
echo ========================================================
echo 🏁 INTERACTION TESTS EXECUTION SUMMARY
echo ========================================================
echo ⏰ Completed at: %date% %time%
echo 📊 Total Tests: !TOTAL_TESTS!
echo ✅ Passed: !PASSED_TESTS!
echo ❌ Failed: !FAILED_TESTS!

set /a SUCCESS_RATE=!PASSED_TESTS! * 100 / !TOTAL_TESTS!
echo 📈 Success Rate: !SUCCESS_RATE!%%

if !FAILED_TESTS! == 0 (
    echo.
    echo 🎉 ALL TESTS PASSED! Interaction test suite completed successfully.
    exit /b 0
) else (
    echo.
    echo ⚠️  !FAILED_TESTS! test^(s^) failed. Please review the results above.
    exit /b 1
)
