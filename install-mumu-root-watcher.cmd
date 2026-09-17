@echo off
cd /d "%~dp0"
set "REPO=%~dp0"

net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Requesting administrator privileges...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo.
echo Creating scheduled task...

set "WATCHER=%REPO%watch-mumu-root.ps1"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"'$env:REPO'watch-mumu-root.ps1'\"';" ^
  "$tr = New-ScheduledTaskTrigger -AtLogOn;" ^
  "$p = New-ScheduledTaskPrincipal -UserId '$env:USERNAME' -LogonType Password -RunLevel Limited;" ^
  "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1);" ^
  "Register-ScheduledTask -TaskName 'PokemonGoBot-MuMuRootWatcher' -Action $t -Trigger $tr -Principal $p -Settings $s -Force;" 2>&1

echo.
echo Watcher installed. Verify with:
echo   schtasks /Query /TN "PokemonGoBot-MuMuRootWatcher"
echo.
pause
