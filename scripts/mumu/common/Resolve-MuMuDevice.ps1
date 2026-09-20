$ErrorActionPreference = "Stop"

function Resolve-MuMuDevice {
    param([string]$adbPath)

    $knownEndpoints = @(
        "emulator-5554",
        "127.0.0.1:16384"
    )

    foreach ($serial in $knownEndpoints) {
        try {
            $state = & $adbPath -s $serial get-state 2>&1
            if ($state -eq "device") {
                return $serial
            }
        } catch {
        }
    }

    $devices = & $adbPath devices 2>&1
    foreach ($line in $devices) {
        if ($line -match '^\S+\tdevice$') {
            $parts = $line -split '\s+'
            $serial = $parts[0]
            if ($serial -and $serial -ne 'List' -and $serial -ne 'of') {
                return $serial
            }
        }
    }

    return ""
}

if ($MyInvocation.InvocationName -ne '.') {
    $adbPath = . (Join-Path $PSScriptRoot 'Resolve-Adb.ps1')
    $serial = Resolve-MuMuDevice -adbPath $adbPath
    if (-not $serial) { exit 20 }
    Write-Output $serial
}
