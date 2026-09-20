<#
.SYNOPSIS
    Diagnostic script for HideMockLocation (HML) compatibility testing on MuMu/Android 15.

.DESCRIPTION
    This script checks device readiness for HML installation and testing.
    It verifies ADB connectivity, root status, Magisk/Zygisk state, LSPosed
    status, and multiuser configuration. It does NOT install or modify HML.

    Usage:
        powershell -NoProfile -ExecutionPolicy Bypass -File tools/diagnostics/agent3_hml_compatibility.ps1

.NOTES
    AGENT 3 - HIDEMOCKLOCATION TECHNICAL COMPATIBILITY
    Environment: MuMu Player, Android 15, API 35, x86_64
    This script is read-only and does not mutate the device.
#>

param(
    [string]$Serial = "127.0.0.1:16384",
    [string]$AdbPath = ""
)

# Locate ADB
if ([string]::IsNullOrEmpty($AdbPath)) {
    $AdbPath = "C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
    if (-not (Test-Path $AdbPath)) {
        $AdbPath = "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe"
    }
}

$global:AdbPath = $AdbPath
$global:Serial = $Serial

function Run-Adb {
    $allArgs = @("-s", $Serial) + $args
    $result = & $AdbPath @allArgs 2>&1
    return $result
}

Write-Host "=== HML Compatibility Diagnostics ===" -ForegroundColor Cyan
Write-Host "ADB: $AdbPath"
Write-Host "Serial: $Serial"
Write-Host ""

# 1. ADB connectivity
Write-Host "[1] ADB Connectivity" -ForegroundColor Yellow
$devices = Run-Adb "devices", "-l"
Write-Host $devices
Write-Host ""

# 2. Root status
Write-Host "[2] Root Status" -ForegroundColor Yellow
$whoami = Run-Adb "shell", "whoami"
Write-Host "whoami: $whoami"
$id = Run-Adb "shell", "id"
Write-Host "id: $id"
Write-Host ""

# 3. Magisk status
Write-Host "[3] Magisk Status" -ForegroundColor Yellow
$magiskPkg = Run-Adb "shell", "pm", "list", "packages", "com.topjohnwu.magisk"
Write-Host "Magisk package: $magiskPkg"
$magiskVer = Run-Adb "shell", "su", "-c", "magisk -v"
Write-Host "magisk -v: $magiskVer"
Write-Host ""

# 4. Zygisk status
Write-Host "[4] Zygisk Status" -ForegroundColor Yellow
$zygiskProp = Run-Adb "shell", "getprop", "zygisk.enabled"
Write-Host "zygisk.enabled prop: $zygiskProp"
$zygiskSo = Run-Adb "shell", "ls", "/system/lib64/zygisk/"
Write-Host "zygisk .so dir: $zygiskSo"
Write-Host ""

# 5. LSPosed status
Write-Host "[5] LSPosed Status" -ForegroundColor Yellow
$lsposedPkg = Run-Adb "shell", "pm", "list", "packages"
$lsposedFound = $lsposedPkg | Where-Object { $_ -match "lsposed" }
Write-Host "LSPosed packages: $($lsposedFound -join ', ')"
Write-Host ""

# 6. Multiuser status
Write-Host "[6] Multiuser Status" -ForegroundColor Yellow
$users = Run-Adb "shell", "pm", "list", "users"
Write-Host "Users: $users"
Write-Host ""

# 7. Android version
Write-Host "[7] Android Version" -ForegroundColor Yellow
$sdk = Run-Adb "shell", "getprop", "ro.build.version.sdk"
Write-Host "SDK: $sdk"
$release = Run-Adb "shell", "getprop", "ro.build.version.release"
Write-Host "Release: $release"
$abi = Run-Adb "shell", "getprop", "ro.product.cpu.abi"
Write-Host "ABI: $abi"
Write-Host ""

# 8. Compatibility summary
Write-Host "=== Compatibility Summary ===" -ForegroundColor Cyan
$rootOk = ($whoami -match "root")
$lsposedInstalled = ($lsposedFound.Count -gt 0)
$api35 = ($sdk -match "35")
$x86_64 = ($abi -match "x86_64")

Write-Host "Android 15/API 35: $($api35)"
Write-Host "x86_64: $($x86_64)"
Write-Host "Root available: $($rootOk)"
Write-Host "LSPosed installed: $($lsposedInstalled)"

if ($rootOk -and $lsposedInstalled) {
    Write-Host "FRAMEWORK READY: Proceed with HML installation" -ForegroundColor Green
} else {
    Write-Host "FRAMEWORK NOT READY: Waiting for ROOT READY=YES and LSPOSED ACTIVE=YES" -ForegroundColor Red
}
