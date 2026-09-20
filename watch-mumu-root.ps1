$ErrorActionPreference = "Stop"

$repo = $PSScriptRoot
$adb = Join-Path $repo ".tools\android-sdk\platform-tools\adb.exe"
$rootScript = Join-Path $repo "root-mumu.ps1"
$serial = "emulator-5554"

$watcherMutexName = "Global\PokemonGoBot-MuMuRootWatcher"
$operationMutexName = "Global\PokemonGoBot-MuMuRootOperation"

$alreadyRunning = $false
$watcherMutex = New-Object System.Threading.Mutex($false, $watcherMutexName, [ref]$alreadyRunning)
if ($alreadyRunning) {
    exit 0
}

function Wait-AdbDevice {
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        try {
            $state = & $adb -s $serial get-state 2>&1
            if ($state -eq "device") { return $true }
        } catch {
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Wait-MuMuExit {
    while (Get-Process MuMuNxDevice -ErrorAction SilentlyContinue) {
        Start-Sleep -Seconds 3
    }
}

function Run-RootOnce {
<<<<<<< ours
    $opOwned = $false
    $opMutex = New-Object System.Threading.Mutex($false, $operationMutexName, [ref]$opOwned)
    if ($opOwned) {
        try {
            & $rootScript
        } catch {
        } finally {
            $opMutex.ReleaseMutex()
            $opMutex.Dispose()
        }
=======
    $createdNew = $false
    $opMutex = New-Object System.Threading.Mutex($true, $operationMutexName, [ref]$createdNew)
    $hasLock = $false
    try {
        if ($createdNew -or $opMutex.WaitOne(0)) {
            $hasLock = $true
            & $rootScript
        }
    } catch {
    } finally {
        if ($hasLock) {
            $opMutex.ReleaseMutex()
        }
        $opMutex.Dispose()
>>>>>>> theirs
    }
}

$handledPid = $null

while ($true) {
    while (-not (Get-Process MuMuNxDevice -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 3
    }

    $currentPid = (Get-Process MuMuNxDevice).Id

    if ($currentPid -ne $handledPid) {
        $adbReady = Wait-AdbDevice
        if ($adbReady) {
            Run-RootOnce
            $handledPid = $currentPid
        }
    }

    Wait-MuMuExit
    $handledPid = $null

    Start-Sleep -Seconds 3
}
