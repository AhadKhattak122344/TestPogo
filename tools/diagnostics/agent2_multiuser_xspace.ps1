# Agent 2 — MuMu Multiuser / XSpace Diagnostic Script
#
# Read-only. No mutations. Run after MuMu VM is booted and ADB is connected.
#
# Usage:
#   .\tools\diagnostics\agent2_multiuser_xspace.ps1

$ErrorActionPreference = "Continue"
$ADB = "adb"
$SERIAL = "127.0.0.1:16384"

Write-Host "=== PHASE 1: Android Users ===" -ForegroundColor Cyan
& $ADB -s $SERIAL shell pm list users 2>&1
Write-Host ""
& $ADB -s $SERIAL shell cmd user list 2>&1
Write-Host ""
& $ADB -s $SERIAL shell dumpsys user 2>&1 | Select-String -Pattern "Current user|UserInfo|Type:|State:|Has profile|Guest|Device managed|Started users|Cached user|Max users|Supports switchable" | Select-Object -First 25
Write-Host ""

Write-Host "=== PHASE 2: Pokemon GO User ===" -ForegroundColor Cyan
& $ADB -s $SERIAL shell pm path com.nianticlabs.pokemongo 2>&1
Write-Host ""
& $ADB -s $SERIAL shell dumpsys package com.nianticlabs.pokemongo 2>&1 | Select-String -Pattern "Package|uid=|userId|versionName|versionCode|dataDir|primaryCpuAbi" | Select-Object -First 15
Write-Host ""

Write-Host "=== PHASE 3: Multi-instance check ===" -ForegroundColor Cyan
Write-Host "VM directories:"
Get-ChildItem "C:\Program Files\Netease\MuMuPlayer\vms" -ErrorAction SilentlyContinue | Select-Object Name
Write-Host ""
Write-Host "Android users inside VM:"
& $ADB -s $SERIAL shell pm list users 2>&1
Write-Host ""

Write-Host "=== PHASE 4: LSPosed / Magisk check ===" -ForegroundColor Cyan
& $ADB -s $SERIAL shell pm list packages 2>&1 | Select-String -Pattern "lsposed|magisk|zygisk" | Select-Object -First 5
Write-Host ""

Write-Host "=== PHASE 5: Device identity ===" -ForegroundColor Cyan
& $ADB -s $SERIAL shell getprop ro.build.version.release 2>&1
& $ADB -s $SERIAL shell getprop ro.build.version.sdk 2>&1
& $ADB -s $SERIAL shell getprop ro.product.manufacturer 2>&1
& $ADB -s $SERIAL shell getprop ro.product.brand 2>&1
& $ADB -s $SERIAL shell getprop ro.product.model 2>&1
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green