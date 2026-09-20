function Write-MuMuLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    if (-not $script:logFile) {
        $repoRoot = (Get-Item (Join-Path $PSScriptRoot '..\..\..')).FullName
        $logDir = Join-Path $repoRoot 'logs\mumu-bootstrap'
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        $timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
        $script:logFile = Join-Path $logDir "$timestamp.log"
    }

    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $script:logFile -Value $entry -ErrorAction SilentlyContinue
}

if ($MyInvocation.InvocationName -ne '.') {
    $msg = $args[0]
    $lvl = if ($args.Count -gt 1) { $args[1] } else { 'INFO' }
    Write-MuMuLog -Message $msg -Level $lvl
}
