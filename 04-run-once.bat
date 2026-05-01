@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     Pinterest Growth Agent - Run One Cycle          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

call venv\Scripts\activate

echo  Running a single agent cycle now...
echo  This will: Research ^>^> Generate ^>^> Post ^>^> Analyze
echo  Safety limits from config.yaml will be respected.
echo.
echo  Watch the output below for progress.
echo  A detailed report will be shown when complete.
echo.

python -m src.main run-now

echo.
echo  Cycle finished. Press any key to exit.
pause >nul