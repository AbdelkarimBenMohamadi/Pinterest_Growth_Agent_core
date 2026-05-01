@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     Pinterest Growth Agent - Setup Wizard             ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

echo  [1/5] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment. Make sure Python 3.11+ is installed.
        pause
        exit /b 1
    )
    echo  Done.

echo.
echo  [2/5] Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  ERROR: Failed to install dependencies. Check your internet connection.
        pause
        exit /b 1
    )
    echo  Done.

echo.
echo  [3/5] Installing Playwright Chromium browser...
    playwright install chromium
    if errorlevel 1 (
        echo  WARNING: Playwright installation may have failed. Run this again or install manually.
    ) else (
        echo  Done.
    )

echo.
echo  [4/5] Setting up configuration files...
    if not exist .env (
        copy .env.example .env
        echo   - Created .env from template
    ) else (
        echo   - .env already exists - skipping
    )
    if not exist data (
        mkdir data
        echo   - Created data/ directory
    )
    if not exist assets (
        mkdir assets
        echo   - Created assets/ directory
    )
    echo  Done.

echo.
echo  [5/5] Opening .env in Notepad for your API keys...
    start notepad .env

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║              SETUP COMPLETE!                          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  NEXT STEPS:
echo .
echo  STEP 1 - Fill in your .env file (now open in Notepad):
echo    - GROQ_API_KEY      ^<-- Get free at console.groq.com
echo    - PINTEREST_EMAIL   ^<-- Your Pinterest account email
echo    - PINTEREST_PASSWORD ^<-- Your Pinterest account password
echo.
echo  STEP 2 - Edit config.yaml with your niche:
echo    - seed_keywords     ^<-- Topics you want to post about
echo    - categories       ^<-- Pinterest categories for your niche
echo.
echo  STEP 3 - Validate everything is working:
echo    Run: 02-validate.bat
echo.
echo  STEP 4 - Start the agent:
echo    Run: 06-start-scheduler.bat
echo.
echo  Need help? Open BEGINNERS_GUIDE_EN.md
echo.
pause