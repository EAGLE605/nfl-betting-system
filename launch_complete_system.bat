@echo off
echo ================================================================
echo [NFL] NFL Betting System - Complete Deployment
echo ================================================================
echo.
echo This script will:
echo   1. Fetch latest NFL data from ESPN API
echo   2. Update bet history with current season
echo   3. Launch the interactive dashboard
echo   4. Enable Backtesting Lab with real data
echo.
echo ================================================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate

echo [STEP 1/3] Fetching latest NFL data from ESPN...
python scripts/fetch_latest_nfl_data.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Data fetch had issues, continuing anyway...
)

echo.
echo [STEP 2/3] System ready!
echo.

echo [STEP 3/3] Launching dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo ================================================================
echo.

REM Launch dashboard
.venv\Scripts\streamlit.exe run dashboard/app.py

pause

