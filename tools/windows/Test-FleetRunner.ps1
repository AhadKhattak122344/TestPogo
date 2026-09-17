# Exercise orchestration failures with fake stage results; no Android tools/devices.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Fleet-Common.ps1')
$scratch = New-FleetArtifactDir -Name 'fleet-runner-tests'
$scriptDir = Join-Path $scratch 'tools/windows'
New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $scratch 'artifacts/pgo-apk') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $scratch 'artifacts/pgo-apk/base.apk') -Value 'fixture only'
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Run-FleetTests.ps1') -Destination $scriptDir
$common = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'Fleet-Common.ps1')
$fakeTools = @'
function Get-FleetTools { [pscustomobject]@{ Adb='unused-fixture' } }
function Get-FleetAdbState { return 'error: device not found' }
function Invoke-FleetNative {
    param([string]$Exe,[string[]]$Arguments,[int]$TimeoutSeconds)
    $stage = Split-Path -Leaf $Arguments[[array]::IndexOf($Arguments,'-File') + 1]
    $caseName = $Arguments[[array]::IndexOf($Arguments,'-Only') + 1]
    if ($stage -eq 'Install-FleetGame.ps1') {
        $summaryPath = $Arguments[[array]::IndexOf($Arguments,'-Summary') + 1]
        $caseName = Split-Path -Leaf (Split-Path -Parent $summaryPath)
    }
    Add-Content -LiteralPath (Join-Path (Get-FleetRepoRoot) 'trace.txt') -Value "$caseName $stage"
    $fixtureMatrix = Get-FleetMatrix -Path (Join-Path (Get-FleetRepoRoot) 'matrix.json')
    $targetSerial = ($fixtureMatrix.avds | Where-Object name -eq $caseName).serial
    $exitCode=0
    if ($stage -eq 'New-FleetAvds.ps1' -and $caseName -eq 'create_fails') { $exitCode=2 }
    if ($stage -eq 'Start-Fleet.ps1') {
        if ($Arguments -notcontains '-Headless') { throw 'Runner did not forward requested headless mode' }
        $summaryPath = $Arguments[[array]::IndexOf($Arguments,'-SummaryPath') + 1]
        $row = [pscustomobject]@{ name=$caseName; serial=$targetSerial; pid=777; status='display_ok' }
        $rows=@($row)
        if ($caseName -eq 'foreign_port') { $exitCode=1; $rows=@() }
        if ($caseName -eq 'capture_fails') { $exitCode=1; $row.status='capture_error' }
        ConvertTo-Json -InputObject $rows -Depth 5 | Set-Content -LiteralPath $summaryPath
    }
    if ($stage -eq 'Install-FleetGame.ps1') {
        if ($caseName -eq 'game_crashes') { $exitCode=1 }
        $resultPath = $Arguments[[array]::IndexOf($Arguments,'-ResultPath') + 1]
        $gameRows = @([pscustomobject]@{ serial=$targetSerial; status=$(if ($exitCode) { 'native_crash' } else { 'process_running' }) })
        if ($caseName -eq 'missing_report') { $gameRows=@() }
        ConvertTo-Json -InputObject $gameRows | Set-Content -LiteralPath $resultPath
    }
    [pscustomobject]@{ ExitCode=$exitCode; Output='fixture result'; TimedOut=$false }
}
'@
Set-Content -LiteralPath (Join-Path $scriptDir 'Fleet-Common.ps1') -Value ($common + "`n" + $fakeTools)
$rows=@(); $port=5562
foreach ($name in @('create_fails','foreign_port','capture_fails','game_crashes','passes','missing_report')) {
    $rows += [pscustomobject]@{ name=$name; port=$port; image='fixture'; device=@('fixture'); displayName=$name; enabled=$true; gpu='auto'; features=@() }
    $port+=2
}
$matrixPath = Join-Path $scratch 'matrix.json'
[pscustomobject]@{ avds=$rows } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $matrixPath
$psExe = Join-Path $PSHOME 'powershell.exe'
$run = Invoke-FleetNative -Exe $psExe -Arguments @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $scriptDir 'Run-FleetTests.ps1'),'-Matrix',$matrixPath,'-Headless')
Set-Content -LiteralPath (Join-Path $scratch 'test-output.log') -Value $run.Output
if ($run.ExitCode -ne 1) { throw "Mixed failure sweep should return 1: $($run.Output)" }
$results=@(Read-FleetJsonRows -Path (Join-Path $scratch 'artifacts/fleet-sweep-latest.json'))
if ($results.Count -ne 6) { throw "Runner lost cases: $($run.Output)" }
$expected=@('create_failed','display_not_ready','display_not_ready','game_test_failed','launch_observed','invalid_game_report')
for ($index=0; $index -lt $expected.Count; $index++) { if ($results[$index].status -ne $expected[$index]) { throw "Wrong case status: $($results[$index] | ConvertTo-Json -Depth 6)" } }
$trace=Get-Content -LiteralPath (Join-Path $scratch 'trace.txt')
if (@($trace | Where-Object { $_ -match 'Stop-Fleet.ps1$' }).Count -ne 4) { throw 'Owned case cleanup did not run exactly four times' }
if (@($trace | Where-Object { $_ -match '^(create_fails|foreign_port) Stop-' }).Count) { throw 'Runner attempted cleanup without an owned launch' }
if (@($trace | Where-Object { $_ -match 'Install-FleetGame.ps1$' }).Count -ne 3) { throw 'Game tests ran without display readiness' }
Write-Host 'PASS: automatic runner continues after failures, gates game tests, cleans owned launches and preserves per-case results'
