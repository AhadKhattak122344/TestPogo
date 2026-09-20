function Wait-MuMuBoot {
    param(
        [string]$adbPath,
        [string]$serial,
        [int]$pollSeconds = 2,
        [int]$timeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($timeoutSeconds)

    Write-Output "WAITING FOR ADB"

    $adbReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $state = & $adbPath -s $serial get-state 2>&1
            if ($state -eq "device") {
                $adbReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds $pollSeconds
    }

    if (-not $adbReady) {
        return 30
    }

    Write-Output "ADB CONNECTED"
    Write-Output "ANDROID BOOTING"

    $bootReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $boot = & $adbPath -s $serial shell getprop sys.boot_completed 2>&1
            if ($boot -eq "1") {
                $bootReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds $pollSeconds
    }

    Write-Output "ANDROID READY"

    $pkgReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $pm = & $adbPath -s $serial shell "pm list packages android" 2>&1
            if ($pm -and $pm -match 'package:') {
                $pkgReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds $pollSeconds
    }

    if (-not $bootReady -or -not $pkgReady) {
        return 30
    }

    return 0
}

if ($MyInvocation.InvocationName -ne '.') {
    $exitCode = Wait-MuMuBoot -adbPath $args[0] -serial $args[1]
    exit $exitCode
}
