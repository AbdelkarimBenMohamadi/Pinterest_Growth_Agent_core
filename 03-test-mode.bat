@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  Pinterest Growth Agent - FORCE TEST MODE           ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

call venv\Scripts\activate

echo  WARNING: Running in FORCE MODE - Safety limits are BYPASSED
echo.
echo  This mode is intended for TESTING only.
echo  Do NOT use it repeatedly on a live account.
echo.
echo  What this does:
echo    - Generates and posts pins regardless of daily limits
echo    - Runs the full Research ^>^> Generate ^>^> Post flow
echo    - Bypasses hourly and daily pin caps
echo.
echo  When to use:
echo    - First time setup - to verify everything works
echo    - After changing config.yaml - to test new keywords
echo    - When debugging a specific issue
echo.
echo  When NOT to use:
echo    - On a fresh Pinterest account (days 1-7) repeatedly
echo    - While the normal scheduler (06-start-scheduler.bat) is also running
echo    - More than once per hour
echo.
echo  Press Ctrl+C to cancel, or Enter to continue...
pause >nul

echo.
echo  Starting forced test cycle...
echo.

python -m src.main run-now --force

echo.
echo  Cycle finished. Press any key to exit.
pause >nul