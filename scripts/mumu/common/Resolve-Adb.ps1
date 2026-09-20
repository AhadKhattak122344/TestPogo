function Resolve-Adb {
    $repoRoot = (Get-Item (Join-Path $PSScriptRoot '..\..\..')).FullName
    $candidates = @(
        Join-Path $repoRoot '.tools\android-sdk\platform-tools\adb.exe'
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }

    $cmd = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path $cmd.Source)) {
        return $cmd.Source
    }

    $wingetPath = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
    if (Test-Path $wingetPath) {
        return $wingetPath
    }

    return ""
}

if ($MyInvocation.InvocationName -ne '.') {
    $adbPath = Resolve-Adb
    if (-not $adbPath) { exit 10 }
    Write-Output $adbPath
}
