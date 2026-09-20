@echo off
REM ============================================================
REM  AUTOPILOT — publish_all.bat
REM  Terminal mein sirf: publish_all
REM  Ya: publish_all --series SERIES_1
REM  Ya: publish_all --list
REM  Ya: publish_all --delay 30
REM ============================================================
setlocal
set "ROOT=%~dp0"
python "%ROOT%publish_all.py" %*
endlocal
