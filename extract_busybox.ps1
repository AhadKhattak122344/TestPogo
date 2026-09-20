$magiskApk = 'C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\assets\magisk-v30.7.apk'
$busyboxTemp = Join-Path $env:TEMP 'muumagisk-busybox'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($magiskApk)
$busyboxEntry = $zip.GetEntry('lib/x86_64/libbusybox.so')
if (-not $busyboxEntry) { $zip.Dispose(); exit 1 }
$entryStream = $busyboxEntry.Open()
$fileStream = [System.IO.File]::Create($busyboxTemp)
$entryStream.CopyTo($fileStream)
$fileStream.Close()
$entryStream.Close()
$zip.Dispose()
Write-Output "Extracted to: $busyboxTemp"