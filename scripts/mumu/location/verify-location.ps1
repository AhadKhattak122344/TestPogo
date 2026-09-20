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

Write-MuMuLog -Message "Location verification starting on $serial" -Level INFO

$failures = @()

try {
    $rootOutput = & $adbPath -s $serial shell "su -c id" 2>&1
    if ($rootOutput -notmatch "uid=0\(root\)") {
        $failures += "ROOT: uid=0(root) not found"
    }
} catch {
    $failures += "ROOT: command failed"
}

try {
    $mockApp = & $adbPath -s $serial shell "settings get secure mock_location_app" 2>&1
    $mockApp = $mockApp.Trim()
    if ($mockApp -ne "null" -and $mockApp -ne "") {
        $failures += "MOCK APP: $mockApp"
    }
} catch {
    $failures += "MOCK APP: check failed"
}

try {
    $locationDump = & $adbPath -s $serial shell "dumpsys location" 2>&1

    $testProviderLines = ($locationDump | Where-Object { $_ -match "test-provider|TestProvider|TEST_PROVIDER" })
    if ($testProviderLines) {
        $failures += "THIRD-PARTY TEST PROVIDER: present"
    }

    $gpsLines = ($locationDump | Where-Object { $_ -match "GnssService|gps" })
    if (-not $gpsLines) {
        $failures += "GPS: GnssService not found"
    }

    $mockFlagLines = ($locationDump | Where-Object { $_ -match "mMock|isMock|mock" })
    foreach ($line in $mockFlagLines) {
        if ($line -match "true") {
            $failures += "MOCK FLAG: true detected"
            break
        }
    }

    $fusedLines = ($locationDump | Where-Object { $_ -match "Fused" })
    if (-not $fusedLines) {
        $failures += "FUSED: normal Android/GMS path not found"
    }
} catch {
    $failures += "LOCATION DUMP: command failed"
}

if ($failures.Count -gt 0) {
    foreach ($f in $failures) {
        Write-Output $f
    }
    Write-MuMuLog -Message "Location verification failed: $($failures -join '; ')" -Level ERROR
    exit 70
}

Write-Output "LOCATION CLEANUP: PASS"
Write-MuMuLog -Message "Location verification passed on $serial" -Level INFO
exit 0
