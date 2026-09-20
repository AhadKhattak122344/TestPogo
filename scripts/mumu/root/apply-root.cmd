@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply-root.ps1"
set "EXITCODE=%ERRORLEVEL%"
exit /b %EXITCODE%
