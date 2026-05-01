@echo off
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║     Pinterest Growth Agent - Running Agent          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

call venv\Scripts\activate

echo  Starting the agent scheduler...
echo  The agent will run once daily at the hour set in config.yaml
echo.
echo  Press Ctrl+C to stop the agent.
echo.

python -m src.main start