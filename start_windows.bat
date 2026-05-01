@echo off
setlocal enabledelayedexpansion
title Pinterest Growth Agent - Setup & Run
color 0B

echo ==========================================================
echo       Pinterest Growth Agent - Setup ^& Launcher
echo ==========================================================
echo.

:: Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Python is not installed!
    echo Please go to https://www.python.org/downloads/
    echo Download Python, and when installing, check the box that says "Add Python to PATH".
    echo.
    pause
    exit /b
)
echo [OK] Python is installed.

:: Create virtual environment if missing
IF NOT EXIST "venv\" (
    echo.
    echo [1/3] Building the robot's virtual home...
    python -m venv venv
) ELSE (
    echo [OK] Virtual home found.
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo.
echo [2/3] Installing robot parts (this might take a minute)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo [OK] Parts installed.

echo.
echo [3/3] Installing robot browser...
playwright install chromium >nul 2>&1
echo [OK] Browser installed.

:: Check for .env file
IF NOT EXIST ".env" (
    echo.
    echo ==========================================================
    echo                 ROBOT SECRET KEYS
    echo ==========================================================
    echo It looks like this is your first time! We need your keys.
    echo.
    set /p INPUT_GROQ="1. Paste your Groq API Key: "
    set /p INPUT_EMAIL="2. Enter your Pinterest Email: "
    set /p INPUT_PASS="3. Enter your Pinterest Password: "
    
    echo GROQ_API_KEY=!INPUT_GROQ!> .env
    echo PINTEREST_EMAIL=!INPUT_EMAIL!>> .env
    echo PINTEREST_PASSWORD=!INPUT_PASS!>> .env
    echo PINTEREST_PROXY=>> .env
    
    echo.
    echo [SUCCESS] Keys saved securely to .env file!
)

echo.
echo ==========================================================
echo                  READY TO GO!
echo ==========================================================
echo The robot is fully built and ready to work.
echo.
set /p START_BOT="Do you want to wake up the robot right now? (Y/N): "

IF /I "!START_BOT!"=="Y" (
    echo.
    echo Waking up... Press Ctrl+C to stop it at any time.
    echo ----------------------------------------------------------
    python -m src.main run
    pause
) ELSE (
    echo.
    echo No problem! Just double-click this start_windows.bat file whenever you're ready.
    pause
)
