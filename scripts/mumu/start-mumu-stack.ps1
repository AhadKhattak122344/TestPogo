$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot '..\common\Resolve-Adb.ps1')
. (Join-Path $PSScriptRoot '..\common\Resolve-MuMuDevice.ps1')
. (Join-Path $PSScriptRoot '..\common\Wait-MuMuBoot.ps1')
. (Join-Path $PSScriptRoot '..\common\Write-MuMuLog.ps1')

$mode = 'Normal'
if ($args.Count -gt 0) { $mode = $args[0] }
if ($args.Count -gt 1) { $mode = $args[1] }

$mutexName = "Global\PokemonGoBot-MuMuBootstrap"
$createdNew = $false
$mutex = New-Object System.Threading.Mutex($true, $mutexName, [ref]$createdNew)
if (-not $createdNew) {
    Write-Output "MUMU BOOTSTRAP ALREADY RUNNING"
    $mutex.Dispose()
    exit 0
}

try {
    $repoRoot = (Get-Item (Join-Path $PSScriptRoot '..\..\..')).FullName
    $adbPath = Resolve-Adb
    if (-not $adbPath) {
        Write-Output "[1/7] RESOLVE ADB: FAIL"
        exit 10
    }
    Write-Output "[1/7] RESOLVE ADB: $adbPath"

    $serial = Resolve-MuMuDevice -adbPath $adbPath
    if (-not $serial) {
        if ($mode -eq 'Normal') {
            Write-Output "[2/7] START/DETECT MUMU: launching..."
            $manager = "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe"
            if (Test-Path $manager) {
                & $manager control --vmindex 0 launch
            } else {
                Write-Output "[2/7] START/DETECT MUMU: FAIL - MuMuManager not found"
                exit 20
            }
        } else {
            Write-Output "[2/7] START/DETECT MUMU: FAIL - MuMu not found"
            exit 20
        }

        $deadline = (Get-Date).AddSeconds(120)
        $adbReady = $false
        while ((Get-Date) -lt $deadline) {
            try {
                $state = & $adbPath -s emulator-5554 get-state 2>&1
                if ($state -eq "device") { $adbReady = $true; break }
            } catch {
            }
            Start-Sleep -Seconds 3
        }
        if (-not $adbReady) {
            Write-Output "[2/7] START/DETECT MUMU: FAIL - ADB did not detect"
            exit 20
        }

        $serial = Resolve-MuMuDevice -adbPath $adbPath
        if (-not $serial) {
            Write-Output "[2/7] START/DETECT MUMU: FAIL - still not found"
            exit 20
        }
    }
    Write-Output "[2/7] START/DETECT MUMU: $serial"

    Write-Output "[3/7] WAIT FOR ANDROID"
    $bootExit = Wait-MuMuBoot -adbPath $adbPath -serial $serial
    if ($bootExit -ne 0) {
        Write-Output "[3/7] WAIT FOR ANDROID: FAIL - timeout"
        exit 30
    }
    Write-Output "[3/7] WAIT FOR ANDROID: OK"

    Write-Output "[4/7] APPLY ROOT"
    $rootScript = Join-Path $repoRoot 'root-mumu.ps1'
    if (-not (Test-Path $rootScript)) {
        Write-Output "[4/7] APPLY ROOT: FAIL - script not found"
        exit 40
    }
    & $rootScript
    $rootExit = $LASTEXITCODE
    if ($rootExit -ne 0) {
        Write-Output "[4/7] APPLY ROOT: FAIL - exit $rootExit"
        exit 40
    }
    Write-Output "[4/7] APPLY ROOT: PASS"

    Write-Output "[5/7] WAIT FOR ROOTED DEVICE"
    $deadline = (Get-Date).AddSeconds(60)
    $rooted = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $verify = & $adbPath -s $serial shell "su -c id" 2>&1
            if ($verify -match "uid=0\(root\)") {
                $rooted = $true
                break
            }
        } catch {
        }
        Start-Sleep -Seconds 3
    }
    if (-not $rooted) {
        Write-Output "[5/7] WAIT FOR ROOTED DEVICE: FAIL"
        exit 50
    }
    Write-Output "[5/7] WAIT FOR ROOTED DEVICE: OK"

    Write-Output "[6/7] FIX ERROR12 STATE"
    $fixScript = Join-Path $repoRoot 'scripts\mumu\location\fix-error12.ps1'
    if (-not (Test-Path $fixScript)) {
        Write-Output "[6/7] FIX ERROR12 STATE: FAIL - script not found"
        exit 60
    }
    & $fixScript
    $fixExit = $LASTEXITCODE
    if ($fixExit -ne 0) {
        Write-Output "[6/7] FIX ERROR12 STATE: FAIL - exit $fixExit"
        exit 60
    }
    Write-Output "[6/7] FIX ERROR12 STATE: PASS"

    Write-Output "[7/7] VERIFY"
    $verifyScript = Join-Path $repoRoot 'scripts\mumu\location\verify-location.ps1'
    if (-not (Test-Path $verifyScript)) {
        Write-Output "[7/7] VERIFY: FAIL - script not found"
        exit 70
    }
    & $verifyScript
    $verifyExit = $LASTEXITCODE
    if ($verifyExit -ne 0) {
        Write-Output "[7/7] VERIFY: FAIL - exit $verifyExit"
        exit 70
    }
    Write-Output "[7/7] VERIFY: PASS"

    Write-Output "MUMU READY"
    Write-Output "ROOT: PASS"
    Write-Output "LOCATION STATE: PASS"
    exit 0
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
