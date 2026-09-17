$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$adb = Join-Path $repo ".tools\android-sdk\platform-tools\adb.exe"
$rootScript = Join-Path $repo "root-mumu.ps1"
$manager = "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe"
$serial = "emulator-5554"
$vmIndex = 0

foreach ($file in @($adb, $manager, $rootScript)) {
    if (-not (Test-Path $file)) {
        Write-Output "[FAILED] Missing required file:"
        Write-Output $file
        exit 1
    }
}

$state = ""
try {
    $state = & $adb -s $serial get-state 2>&1
} catch {
}

if ($state -eq "device") {
    Write-Output "[OK] MuMu is already running."
} else {
    Write-Output "[STEP] Starting MuMu..."
    & $manager control --vmindex $vmIndex launch
    if ($LASTEXITCODE -ne 0) {
        Write-Output "[FAILED] MuMu launch failed."
        exit 1
    }

    $deadline = (Get-Date).AddSeconds(120)
    $adbReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $checkState = & $adb -s $serial get-state 2>&1
            if ($checkState -eq "device") {
                $adbReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds 3
    }
    if (-not $adbReady) {
        Write-Output "[FAILED] ADB did not detect emulator-5554 within 120 seconds."
        exit 1
    }

    $deadline = (Get-Date).AddSeconds(120)
    $bootReady = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $boot = & $adb -s $serial shell getprop sys.boot_completed 2>&1
            if ($boot -eq "1") {
                $bootReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds 3
    }
    if (-not $bootReady) {
        Write-Output "[FAILED] Android did not finish booting within 120 seconds."
        exit 1
    }
}

Write-Output "[STEP] Ensuring root is active..."

$operationMutexName = "Global\PokemonGoBot-MuMuRootOperation"
$opOwned = $false
$mutex = New-Object System.Threading.Mutex($false, $operationMutexName, [ref]$opOwned)
try {
    if ($opOwned) {
        & $rootScript
        $rootExitCode = $LASTEXITCODE
    } else {
        $rootExitCode = 1
    }
} catch {
    $rootExitCode = 1
} finally {
    if ($opOwned) {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }
}

$verify = ""
try {
    $verify = & $adb -s $serial shell "su -c id" 2>&1
} catch {
}

if ($verify -match "uid=0\(root\)") {
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Ready"
    Write-Output "========================================"
    Write-Output "Device: emulator-5554"
    Write-Output "MuMu: RUNNING"
    Write-Output "Root: ACTIVE"
    Write-Output "Status: READY"
    Write-Output "========================================"
    exit 0
} else {
    Write-Output ""
    Write-Output "========================================"
    Write-Output "MuMu Ready"
    Write-Output "========================================"
    Write-Output "MuMu: RUNNING"
    Write-Output "Root: FAILED"
    Write-Output "Status: FAILED"
    Write-Output "========================================"
    exit 1
}
