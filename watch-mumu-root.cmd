@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0watch-mumu-root.ps1"
