@echo off
cd /d "%~dp0"

echo.
echo  Pinterest Growth Agent - Run GUI
echo  --------------------------------
echo.

call venv\Scripts\activate

echo  Running one cycle in GUI browser mode.
echo  Safety limits from config.yaml will be respected.
echo  Posting schedule wait will be skipped for this on-demand run.
echo.

python -m src.main run-now --browser-mode gui --schedule-mode immediate

echo.
echo  Cycle finished. Press any key to exit.
pause >nul
