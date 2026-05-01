@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     Pinterest Growth Agent - Pre-Flight Check       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

call venv\Scripts\activate

set ALL_OK=1

echo  [1/6] Python Version
python --version
if errorlevel 1 (
    echo  FAIL: Python not found. Install Python 3.11+ from python.org
    set ALL_OK=0
) else (
    echo  PASS
)
echo.

echo  [2/6] Virtual Environment
if exist venv\Scripts\activate.bat (
    echo  PASS: venv found
) else (
    echo  FAIL: Run 01-install.bat first to create the virtual environment
    set ALL_OK=0
)
echo.

echo  [3/6] Python Dependencies
pip show playwright >nul 2>&1
if not errorlevel 1 (
    echo  PASS: playwright
) else (
    echo  FAIL: Run 01-install.bat to install dependencies
    set ALL_OK=0
)
pip show groq >nul 2>&1
if not errorlevel 1 (
    echo  PASS: groq
) else (
    echo  FAIL: Run 01-install.bat to install dependencies
    set ALL_OK=0
)
pip show apscheduler >nul 2>&1
if not errorlevel 1 (
    echo  PASS: apscheduler
) else (
    echo  FAIL: Run 01-install.bat to install dependencies
    set ALL_OK=0
)
echo.

echo  [4/6] Playwright Chromium Browser
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" 2>nul
if not errorlevel 1 (
    echo  PASS: Chromium installed
) else (
    echo  FAIL: Run 01-install.bat again or run: playwright install chromium
    set ALL_OK=0
)
echo.

echo  [5/6] Configuration Files
if exist config.yaml (
    echo  PASS: config.yaml found
) else (
    echo  FAIL: config.yaml not found
    set ALL_OK=0
)
if exist .env (
    echo  PASS: .env found
) else (
    echo  FAIL: .env not found - run 01-install.bat
    set ALL_OK=0
)
echo.

echo  [6/6] API Keys (checking .env)
findstr /C:"GROQ_API_KEY" .env >nul 2>&1
if not errorlevel 1 (
    echo  PASS: GROQ_API_KEY is set
) else (
    echo  FAIL: GROQ_API_KEY missing in .env
    echo         Open .env and add: GROQ_API_KEY=your_key_here
    echo         Get a free key at: https://console.groq.com
    start https://console.groq.com
    set ALL_OK=0
)

findstr /C:"PINTEREST_EMAIL" .env >nul 2>&1
if not errorlevel 1 (
    echo  PASS: PINTEREST_EMAIL is set
) else (
    echo  FAIL: PINTEREST_EMAIL missing in .env
    set ALL_OK=0
)

findstr /C:"PINTEREST_PASSWORD" .env >nul 2>&1
if not errorlevel 1 (
    echo  PASS: PINTEREST_PASSWORD is set
) else (
    echo  FAIL: PINTEREST_PASSWORD missing in .env
    set ALL_OK=0
)
echo.

echo  ════════════════════════════════════════════════════════

if %ALL_OK%==1 (
    echo.
    echo   ALL CHECKS PASSED - You are ready to go!
    echo.
    echo   Run 03-test-mode.bat to test a full cycle
    echo   Run 04-run-once.bat for normal on-demand runs
    echo   Run 06-start-scheduler.bat to start the daily scheduler
) else (
    echo.
    echo   SOME CHECKS FAILED - Fix the issues above first
    echo   Then run 02-validate.bat again to confirm
)

echo  ════════════════════════════════════════════════════════
echo.
pause