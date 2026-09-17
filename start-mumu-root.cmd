@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-mumu-root.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
    echo MuMu startup/root failed with exit code %EXITCODE%.
)
pause
exit /b %EXITCODE%
