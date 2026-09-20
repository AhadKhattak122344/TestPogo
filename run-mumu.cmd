@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\mumu\start-mumu-stack.cmd"
set "EXITCODE=%ERRORLEVEL%"
exit /b %EXITCODE%
