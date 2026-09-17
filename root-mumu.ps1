$ErrorActionPreference = "Stop"

$adb = Join-Path $PSScriptRoot ".tools\android-sdk\platform-tools\adb.exe"
$manager = "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe"
$serial = "emulator-5554"
$vmIndex = 0

$liveSetup = Join-Path $PSScriptRoot ".tools\magisk-source\scripts\live_setup.sh"
$magiskApk = Join-Path $PSScriptRoot "assets\magisk-v30.7.apk"

function Wait-AdbDevice {
    $deadline = (Get-Date).AddSeconds(90)
    $stableCount = 0
    while ((Get-Date) -lt $deadline) {
        try {
            $state = & $adb -s $serial get-state 2>&1
            if ($state -eq "device") {
                $stableCount++
                if ($stableCount -ge 3) { return $true }
            } else {
                $stableCount = 0
            }
        } catch {
            $stableCount = 0
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Wait-AndroidBoot {
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        try {
            $boot = & $adb -s $serial shell getprop sys.boot_completed 2>&1
            if ($boot -eq "1") { return $true }
        } catch {
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Test-ApplicationRoot {
    try {
        $output = & $adb -s $serial shell "su -c id" 2>&1
        if ($output -match "uid=0\(root\)") { return $true }
    } catch {
    }
    return $false
}

function Get-MagiskVersion {
    $candidates = @(
        "magisk -v",
        "/data/adb/magisk/magisk -v",
        "/debug_ramdisk/magisk -v"
    )
    foreach ($cmd in $candidates) {
        try {
            $result = & $adb -s $serial shell $cmd 2>&1
            if ($result -and $result -notmatch "not found" -and $result -notmatch "No such") {
                return $result
            }
        } catch {
        }
    }
    return ""
}

function Fail-Stage {
    param(
        [string]$Stage,
        [string]$Reason
    )
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Root Setup"
    Write-Output "========================================"
    Write-Output "Status: FAILED"
    Write-Output "Stage: $Stage"
    Write-Output "Reason: $Reason"
    Write-Output "========================================"
    exit 1
}

# =============================================================================
# STEP A — Basic local validation
# =============================================================================

foreach ($file in @($adb, $manager, $liveSetup, $magiskApk)) {
    if (-not (Test-Path $file)) {
        Write-Output "[FAILED] Missing required file:"
        Write-Output $file
        exit 1
    }
}

# =============================================================================
# STEP B — Check MuMu / ADB
# =============================================================================

$devices = & $adb devices 2>&1
if ($LASTEXITCODE -ne 0 -or -not ($devices -match $serial)) {
    Write-Output "[FAILED] MuMu is not connected through ADB."
    Write-Output "Open MuMu completely and run .\root-mumu.ps1 again."
    exit 1
}

# Wait for device to enter device state (may be offline during boot)
$deviceReady = $false
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    try {
        $state = & $adb -s $serial get-state 2>&1
        if ($state -eq "device") { $deviceReady = $true; break }
    } catch {
    }
    Start-Sleep -Seconds 3
}
if (-not $deviceReady) {
    Write-Output "[FAILED] MuMu is not connected through ADB."
    Write-Output "Open MuMu completely and run .\root-mumu.ps1 again."
    exit 1
}

# =============================================================================
# STEP C — Fast root check
# =============================================================================

$rootCheck = ""
try {
    $rootCheck = & $adb -s $serial shell "su -c id" 2>&1
} catch {
}
if ($rootCheck -match "uid=0\(root\)") {
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Root"
    Write-Output "========================================"
    Write-Output "Device: $serial"
    Write-Output "Status: ALREADY ROOTED"
    Write-Output "Root: ACTIVE"
    Write-Output "========================================"
    exit 0
}

# =============================================================================
# STEP D — Enable MuMu root permission
# =============================================================================

$rootPermissionEnabled = $false
try {
    $info = & $manager setting --vmindex $vmIndex --key root_permission --info 2>&1
    if ($info -match "true" -or $info -match "enabled") {
        $rootPermissionEnabled = $true
    }
} catch {
}

if (-not $rootPermissionEnabled) {
    & $manager setting --vmindex $vmIndex --key root_permission --value true
    if ($LASTEXITCODE -ne 0) {
        Fail-Stage -Stage "ROOT_PERMISSION" -Reason "Failed to enable root_permission"
    }
}

# =============================================================================
# STEP E — Restart / Wait
# =============================================================================

& $manager control --vmindex $vmIndex restart
if ($LASTEXITCODE -ne 0) {
    Fail-Stage -Stage "RESTART" -Reason "MuMu restart failed"
}

if (-not (Wait-AdbDevice)) {
    Fail-Stage -Stage "WAIT_ADB" -Reason "ADB did not reconnect within 90 seconds"
}

if (-not (Wait-AndroidBoot)) {
    Fail-Stage -Stage "WAIT_BOOT" -Reason "Android did not finish booting within 90 seconds"
}

Start-Sleep -Seconds 3

# =============================================================================
# STEP F — Check root again
# =============================================================================

if (Test-ApplicationRoot) {
    $magiskVersion = Get-MagiskVersion
    $whichSu = & $adb -s $serial shell "which su" 2>&1
    if (-not $whichSu -or $whichSu -match "not found") { $whichSu = "/system_ext/bin/su" }
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Root Setup"
    Write-Output "========================================"
    Write-Output "Device: $serial"
    Write-Output "Android: 15"
    Write-Output "API: 35"
    Write-Output "ABI: x86_64"
    Write-Output "MuMu root permission: enabled"
    Write-Output "su: $whichSu"
    if ($magiskVersion) {
        Write-Output "Magisk: $magiskVersion"
    } else {
        Write-Output "Magisk: (not on PATH)"
    }
    Write-Output "Root test: uid=0(root)"
    Write-Output "Status: SUCCESS"
    Write-Output "========================================"
    exit 0
}

# =============================================================================
# STEP G — Stage known live setup
# =============================================================================

Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue

$busyboxTemp = Join-Path $env:TEMP "muumagisk-busybox"
try {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($magiskApk)
    $busyboxEntry = $zip.GetEntry("lib/x86_64/libbusybox.so")
    if (-not $busyboxEntry) {
        $zip.Dispose()
        Fail-Stage -Stage "FILE_STAGING" -Reason "busybox not found in Magisk APK"
    }
    $entryStream = $busyboxEntry.Open()
    $fileStream = [System.IO.File]::Create($busyboxTemp)
    $entryStream.CopyTo($fileStream)
    $fileStream.Close()
    $entryStream.Close()
    $zip.Dispose()
} catch {
    Fail-Stage -Stage "FILE_STAGING" -Reason "Failed to extract busybox from APK: $($_.Exception.Message)"
}

& $adb -s $serial shell "mkdir -p /data/local/tmp"
if ($LASTEXITCODE -ne 0) {
    Remove-Item $busyboxTemp -ErrorAction SilentlyContinue
    Fail-Stage -Stage "FILE_STAGING" -Reason "Failed to create /data/local/tmp"
}

$pushOutput = ""
try {
    $pushOutput = & $adb -s $serial push $liveSetup "/data/local/tmp/live_setup.sh" 2>&1
} catch {
    $pushOutput = $_.Exception.Message
}
if ($LASTEXITCODE -ne 0) {
    Remove-Item $busyboxTemp -ErrorAction SilentlyContinue
    Fail-Stage -Stage "FILE_STAGING" -Reason "live_setup.sh push failed: $pushOutput"
}

try {
    $pushOutput = & $adb -s $serial push $busyboxTemp "/data/local/tmp/busybox" 2>&1
} catch {
    $pushOutput = $_.Exception.Message
}
if ($LASTEXITCODE -ne 0) {
    Remove-Item $busyboxTemp -ErrorAction SilentlyContinue
    Fail-Stage -Stage "FILE_STAGING" -Reason "busybox push failed: $pushOutput"
}

try {
    $pushOutput = & $adb -s $serial push $magiskApk "/data/local/tmp/magisk.apk" 2>&1
} catch {
    $pushOutput = $_.Exception.Message
}
if ($LASTEXITCODE -ne 0) {
    Remove-Item $busyboxTemp -ErrorAction SilentlyContinue
    Fail-Stage -Stage "FILE_STAGING" -Reason "magisk.apk push failed: $pushOutput"
}

Remove-Item $busyboxTemp -ErrorAction SilentlyContinue

# =============================================================================
# STEP H — Execute live root once
# =============================================================================

try {
    & $adb -s $serial shell "cd /data/local/tmp && chmod 755 live_setup.sh busybox && ./live_setup.sh"
} catch {
}

# =============================================================================
# STEP I — Wait after live setup
# =============================================================================

if (-not (Wait-AdbDevice)) {
    Fail-Stage -Stage "POST_LIVE_SETUP_ADB" -Reason "ADB did not reconnect within 90 seconds"
}

if (-not (Wait-AndroidBoot)) {
    Fail-Stage -Stage "POST_LIVE_SETUP_BOOT" -Reason "Android did not finish booting within 90 seconds"
}

Start-Sleep -Seconds 3

# =============================================================================
# STEP J — Final verification
# =============================================================================

$whichSu = ""
$suId = ""
$suWhoami = ""
try {
    $whichSu = & $adb -s $serial shell "which su" 2>&1
} catch {
}
try {
    $suId = & $adb -s $serial shell "su -c id" 2>&1
} catch {
}
try {
    $suWhoami = & $adb -s $serial shell "su -c whoami" 2>&1
} catch {
}
$magiskVersion = Get-MagiskVersion

$rootIdPass = $suId -match "uid=0\(root\)"
$rootWhoamiPass = ($suWhoami.Trim()) -eq "root"

if ($rootIdPass -and $rootWhoamiPass) {
    if (-not $whichSu) { $whichSu = "/system_ext/bin/su" }
    if (-not $magiskVersion) { $magiskVersion = "(not on PATH)" }
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Root Setup"
    Write-Output "========================================"
    Write-Output "Device: $serial"
    Write-Output "Android: 15"
    Write-Output "API: 35"
    Write-Output "ABI: x86_64"
    Write-Output "MuMu root permission: enabled"
    Write-Output "su: $whichSu"
    Write-Output "Magisk: $magiskVersion"
    Write-Output "Root test: uid=0(root)"
    Write-Output "Status: SUCCESS"
    Write-Output "========================================"
    exit 0
} else {
    $reason = ""
    if (-not $rootIdPass) { $reason = "su -c id did not return uid=0(root)" }
    if (-not $rootWhoamiPass) {
        if ($reason) { $reason = "$reason; " }
        $reason = "${reason}su -c whoami did not return root"
    }
    Fail-Stage -Stage "FINAL_ROOT_CHECK" -Reason $reason
}
