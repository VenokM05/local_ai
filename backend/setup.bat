@echo off
REM Double-click friendly setup for Windows cmd. Calls setup.ps1.
powershell -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
pause
