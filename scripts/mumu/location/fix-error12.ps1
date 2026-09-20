$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot '..\common\Resolve-Adb.ps1')
. (Join-Path $PSScriptRoot '..\common\Write-MuMuLog.ps1')

$adbPath = Resolve-Adb
if (-not $adbPath) {
    Write-Output "LOCATION CLEANUP: FAIL - ADB not found"
    exit 10
}

$serial = Resolve-MuMuDevice -adbPath $adbPath
if (-not $serial) {
    Write-Output "LOCATION CLEANUP: FAIL - MuMu not found"
    exit 20
}

Write-MuMuLog -Message "Location cleanup starting on $serial" -Level INFO

$forceStop = {
    param([string]$pkg)
    try {
        & $adbPath -s $serial shell "am force-stop $pkg" 2>&1
        return $true
    } catch {
        return $false
    }
}

& $forceStop "com.nianticlabs.pokemongo"

& $forceStop "com.theappninjas.fakegpsjoystick"

& $forceStop "com.locationchanger"

try {
    $result = & $adbPath -s $serial shell "cmd location providers remove-test-provider gps" 2>&1
} catch {
}

try {
    $result = & $adbPath -s $serial shell "cmd location providers remove-test-provider network" 2>&1
} catch {
}

try {
    $result = & $adbPath -s $serial shell "settings put secure mock_location_app null" 2>&1
} catch {
}

Write-Output "LOCATION CLEANUP: PASS"
Write-MuMuLog -Message "Location cleanup complete on $serial" -Level INFO
exit 0
