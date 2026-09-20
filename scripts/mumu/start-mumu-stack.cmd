@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-mumu-stack.ps1" -Normal
set "EXITCODE=%ERRORLEVEL%"
exit /b %EXITCODE%
