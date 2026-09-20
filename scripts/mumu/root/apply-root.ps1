$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot '..\common\Resolve-Adb.ps1')
. (Join-Path $PSScriptRoot '..\common\Resolve-MuMuDevice.ps1')
. (Join-Path $PSScriptRoot '..\common\Wait-MuMuBoot.ps1')
. (Join-Path $PSScriptRoot '..\common\Write-MuMuLog.ps1')

$adbPath = Resolve-Adb
if (-not $adbPath) {
    Write-Output "ROOT: FAIL - ADB not found"
    Write-MuMuLog -Message "Root failed: ADB not found" -Level ERROR
    exit 10
}

$serial = Resolve-MuMuDevice -adbPath $adbPath
if (-not $serial) {
    Write-Output "ROOT: FAIL - MuMu not found"
    Write-MuMuLog -Message "Root failed: MuMu not found" -Level ERROR
    exit 20
}

Write-Output "ROOT: APPLYING"
Write-MuMuLog -Message "Root applying on $serial" -Level INFO

$bootExit = Wait-MuMuBoot -adbPath $adbPath -serial $serial
if ($bootExit -ne 0) {
    Write-Output "ROOT: FAIL - boot timeout"
    Write-MuMuLog -Message "Root failed: boot timeout" -Level ERROR
    exit 30
}

$repoRoot = (Get-Item (Join-Path $PSScriptRoot '..\..\..')).FullName
$rootScript = Join-Path $repoRoot 'root-mumu.ps1'
if (-not (Test-Path $rootScript)) {
    Write-Output "ROOT: FAIL - root workflow not found"
    Write-MuMuLog -Message "Root failed: workflow not found at $rootScript" -Level ERROR
    exit 40
}

Write-Output "ROOT: WAITING"
Write-MuMuLog -Message "Root waiting - executing root workflow" -Level INFO

& $rootScript
$rootExit = $LASTEXITCODE

if ($rootExit -ne 0) {
    Write-Output "ROOT: FAIL - root workflow exit code $rootExit"
    Write-MuMuLog -Message "Root workflow failed: exit $rootExit" -Level ERROR
    exit 40
}

$deadline = (Get-Date).AddSeconds(90)
$deviceReady = $false
while ((Get-Date) -lt $deadline) {
    try {
        $state = & $adbPath -s $serial get-state 2>&1
        if ($state -eq "device") {
            $deviceReady = $true
            break
        }
    } catch {
    }
    Start-Sleep -Seconds 3
}

if (-not $deviceReady) {
    $serial = Resolve-MuMuDevice -adbPath $adbPath
    if (-not $serial) {
        Write-Output "ROOT: FAIL - MuMu disconnected"
        Write-MuMuLog -Message "Root failed: MuMu disconnected" -Level ERROR
        exit 20
    }
}

try {
    $verify = & $adbPath -s $serial shell "su -c id" 2>&1
} catch {
    $verify = ""
}

if ($verify -match "uid=0\(root\)") {
    Write-Output "ROOT: PASS"
    Write-MuMuLog -Message "Root verified on $serial" -Level INFO
    exit 0
} else {
    Write-Output "ROOT: FAIL - su -c id did not return uid=0(root)"
    Write-MuMuLog -Message "Root verification failed on $serial" -Level ERROR
    exit 50
}
