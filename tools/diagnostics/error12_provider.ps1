<#
.SYNOPSIS
    Provider diagnostic script for Pokémon GO Error 12 (Failed to detect location).
    Investigates GPS JoyStick / LocationChanger mock provider state, altitude
    defects, and mock_location system settings consistency.

.ROLE
    PROVIDER - Android LocationManager, GPS JoyStick, test/mock providers,
    location metadata, provider cleanup

.DESCRIPTION
    Read-only snapshot of location state, appops, and mock provider configuration.
    Optionally performs clean reset and GPS JoyStick re-test.

.PARAMETER CleanReset
    If specified, force-stops GPS JoyStick and removes test providers.

.PARAMETER SetMockApp
    If specified, sets mock_location_app and mock_location settings for consistency.

.EXAMPLE
    .\error12_provider.ps1
    Run read-only diagnostics.

.EXAMPLE
    .\error12_provider.ps1 -CleanReset
    Force-stop GPS JoyStick and remove test providers.

.NOTES
    Requires ADB access to emulator-5554 (MuMu Player).
    Mutating actions require coordination via $env:LOCALAPPDATA\PokemonGoError12\device.lock
#>
param(
    [switch]$CleanReset,
    [switch]$SetMockApp,
    [switch]$ReTest
)

$coord = "$env:LOCALAPPDATA\PokemonGoError12"

function Write-Section($title) {
    Write-Output "`n=== $title ==="
}

function Get-LocationState {
    Write-Section "Location Provider State"
    adb shell dumpsys location | Select-String -Pattern "provider \[mock\]|last location=|last mock location=|identity="
}

function Get-MockSettings {
    Write-Section "Mock Location Settings"
    Write-Output "mock_location_app:"
    adb shell settings get secure mock_location_app
    Write-Output "mock_location:"
    adb shell settings get secure mock_location
    Write-Output "location_providers_on:"
    adb shell settings get secure location_providers_on
}

function Get-AppOps {
    Write-Section "AppOps: MOCK_LOCATION"
    Write-Output "[GPS JoyStick]"
    adb shell appops get com.theappninjas.fakegpsjoystick android:mock_location
    Write-Output "[LocationChanger]"
    adb shell appops get com.locationchanger android:mock_location
}

function Get-RootStatus {
    Write-Section "Root Status"
    adb shell "su -c id"
}

function Get-AltitudeAnalysis {
    Write-Section "Altitude Analysis"
    $locs = adb shell dumpsys location | Select-String -Pattern "last location=Location\[gps"
    foreach ($line in $locs) {
        if ($line -match "lat=(\S+).*alt=(\S+)E(\d).*mock") {
            $lat = [double]$matches[1]
            $alt = [double]$matches[2] * [math]::Pow(10, [int]$matches[3])
            $expected = $lat * 1e6
            Write-Output "Latitude: $lat | Altitude: $alt m | lat*1e6: $expected | Diff: $($alt - $expected) | Ratio: $($alt/$lat)"
        }
    }
}

function Invoke-CleanReset {
    Write-Section "Clean Reset (requires device.lock)"
    $lockFile = "$coord\device.lock"
    if (-not (Test-Path $lockFile)) {
        Write-Error "device.lock not held. Acquire lock first."
        return
    }
    Write-Output "Force-stopping GPS JoyStick..."
    adb shell am force-stop com.theappninjas.fakegpsjoystick
    Start-Sleep -Seconds 3
    Write-Output "Removing test providers..."
    adb shell cmd location providers remove-test-provider gps 2>&1
    adb shell cmd location providers remove-test-provider network 2>&1
    Start-Sleep -Seconds 2
    Write-Output "Verifying clean state..."
    Get-LocationState
}

function Set-MockAppSettings {
    Write-Section "Setting mock_location_app and mock_location"
    adb shell settings put secure mock_location_app com.theappninjas.fakegpsjoystick
    adb shell settings put secure mock_location 1
    Start-Sleep -Seconds 2
    Get-MockSettings
}

function Invoke-ReTest {
    Write-Section "GPS JoyStick Re-test"
    Write-Output "Starting OverlayService..."
    adb shell am startservice -n com.theappninjas.fakegpsjoystick/com.theappninjas.fakegpsjoystick.service.OverlayService 2>&1
    Start-Sleep -Seconds 5
    Write-Output "Sample A:"
    adb shell dumpsys location | Select-String -Pattern "last location=Location\[gps"
    Start-Sleep -Seconds 15
    Write-Output "Sample B (15s later):"
    adb shell dumpsys location | Select-String -Pattern "last location=Location\[gps"
    Get-AltitudeAnalysis
}

# --- Main ---
Get-RootStatus
Get-MockSettings
Get-AppOps
Get-LocationState
Get-AltitudeAnalysis

if ($CleanReset) { Invoke-CleanReset }
if ($SetMockApp) { Set-MockAppSettings }
if ($ReTest) { Invoke-ReTest }

Write-Section "Diagnostics Complete"
