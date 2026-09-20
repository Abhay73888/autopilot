@echo off
REM ============================================================
REM  AUTOPILOT — next_ep.bat
REM  Terminal mein sirf: next_ep SERIES_1
REM  Ya: next_ep SERIES_6
REM  Ya: next_ep --list
REM  Ya: next_ep --all
REM ============================================================
setlocal

REM Project root (is .bat file ke saath same folder mein hona chahiye)
set "ROOT=%~dp0"

REM Python ko project root mein se chalaao
python "%ROOT%next_ep.py" %*

endlocal
