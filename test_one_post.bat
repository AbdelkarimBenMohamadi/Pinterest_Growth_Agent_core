@echo off
title Pinterest Growth Agent - Test Single Post
color 0E

echo ==========================================================
echo        Pinterest Growth Agent - Test Single Post
echo ==========================================================
echo.
echo This will force the robot to wake up, research, create, 
echo and post exactly ONE pin right now to test if everything works.
echo.

:: Check if setup was run
IF NOT EXIST "venv\" (
    color 0C
    echo [ERROR] The robot is not built yet!
    echo Please double-click 'start_windows.bat' first to build it.
    echo.
    pause
    exit /b
)

echo Activating the robot...
call venv\Scripts\activate.bat

echo.
echo Running a single test cycle...
echo ----------------------------------------------------------
python -m src.main run --once

echo.
echo ----------------------------------------------------------
echo Test complete! Check your Pinterest account or the dashboard.
echo.
pause
