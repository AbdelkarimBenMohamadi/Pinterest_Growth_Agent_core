@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     Pinterest Growth Agent - Status Dashboard       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

call venv\Scripts\activate

echo  Loading agent statistics...
echo.

python -m src.main stats

echo.
echo  Press any key to exit.
pause >nul