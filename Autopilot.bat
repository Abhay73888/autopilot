@echo off
title AUTOPILOT Desktop App
cd /d "%~dp0"
echo Starting AUTOPILOT Desktop Application...
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
