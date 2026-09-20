<<<<<<< ours
# MuMu API 35 Magisk Root Procedure

Last verified: 2026-09-17

## NORMAL USAGE

Root mechanics are automated.

Normal startup:

```cmd
.\start-mumu-root.cmd
```

This:

1. Starts MuMu if necessary
2. Waits for Android
3. Runs root-mumu
4. Verifies su
5. Returns when MuMu + root are ready

Automatic behavior:

PokemonGoBot-MuMuRootWatcher starts at Windows login and detects MuMu
sessions launched outside the repo.

The rest of this document is recovery/reference information only.

## Scope

This procedure is for the MuMu Player runtime on this machine. It is not the old Android Studio API 34 AVD procedure and must not be replaced with rootAVD/API 34 instructions.

Current environment:

- Platform: MuMu Player
- Android: 15
- API: 35
- ABI: x86_64
- Typical serial: `emulator-5554`
- Repo: `C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot`
- ADB: `C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe`
- MuMu Manager: `C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe`

## Acceptance test

`adb shell id` returning root only proves that `adbd` is running as root. It does not prove that applications can obtain root.

Root is working only when this command succeeds:

```powershell
& $adb -s emulator-5554 shell "su -c id"
```

Required result contains:

```text
uid=0(root)
```

Also verify:

```powershell
& $adb -s emulator-5554 shell "su -c whoami"
```

Expected result:

```text
root
```

Stop root work immediately after these checks pass. Do not proceed to Frida, Pokémon GO, Zygisk, DenyList, Shamiko, Play Integrity, fingerprint changes, root hiding, ramdisk patching, or Magisk reinstallation unless separately requested.

## Tool setup

```powershell
$adb = "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe"
$manager = "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe"
```

## Procedure

### 1. Verify the running MuMu instance

```powershell
& $adb devices
& $adb -s emulator-5554 shell getprop ro.build.version.release
& $adb -s emulator-5554 shell getprop ro.build.version.sdk
& $adb -s emulator-5554 shell getprop ro.product.cpu.abi
& $adb -s emulator-5554 shell getprop sys.boot_completed
```

Expected values for this procedure:

```text
Android 15
API 35
x86_64
boot_completed=1
```

If the running device is not MuMu API 35 x86_64, stop and identify the actual runtime before changing anything.

### 2. Check real root before changing configuration

```powershell
& $adb -s emulator-5554 shell "which su"
& $adb -s emulator-5554 shell "su -c id"
& $adb -s emulator-5554 shell "magisk -v"
```

If `su -c id` already returns `uid=0(root)`, stop. Root is already working.

### 3. Check and enable MuMu root permission

Inspect the setting:

```powershell
& $manager setting --vmindex 0 --key root_permission --info
```

If it is disabled, enable it once:

```powershell
& $manager setting --vmindex 0 --key root_permission --value true
```

Restart MuMu once if the setting requires a restart:

```powershell
& $manager control --vmindex 0 restart
```

Do not repeatedly restart MuMu. Wait for ADB with a bounded loop, then verify boot completion:

```powershell
$ready = $false
for ($i = 1; $i -le 12; $i++) {
    Start-Sleep -Seconds 5
    $state = & $adb -s emulator-5554 get-state 2>&1
    if ($state -eq "device") {
        $ready = $true
        break
    }
}
if (-not $ready) {
    Write-Output "FAILED: MuMu did not reconnect within 60 seconds"
}

& $adb -s emulator-5554 shell getprop sys.boot_completed
```

### 4. If `su` is still missing, repair the existing live setup

Do not reinstall Magisk, download a random payload, or run the API 34 rootAVD procedure. First inspect the existing state:

```powershell
& $adb -s emulator-5554 shell "ls -la /data/adb/magisk"
& $adb -s emulator-5554 shell "ps -A | grep magisk"
& $adb -s emulator-5554 shell "/data/adb/magisk/magisk -v"
```

The working MuMu instance has previously contained Magisk binaries such as:

```text
/data/adb/magisk/magisk
/data/adb/magisk/magiskinit
/data/adb/magisk/magiskpolicy
```

The repo also contains the existing live setup under:

```text
.tools/magisk-source/scripts/live_setup.sh
tools/windows/install_magisk.py
```

The command that restored `su` on the working API 35 MuMu instance was:

```powershell
& $adb -s emulator-5554 shell "cd /data/local/tmp && chmod 755 live_setup.sh busybox && ./live_setup.sh"
```

This command uses the existing files already staged in `/data/local/tmp`; it is a repair of the existing live setup, not a fresh Magisk installation. It can stop zygote and temporarily disconnect ADB. After it returns or ADB reconnects, wait at most 60 seconds and verify:

```powershell
& $adb -s emulator-5554 shell "which su"
& $adb -s emulator-5554 shell "su -c id"
& $adb -s emulator-5554 shell "su -c whoami"
& $adb -s emulator-5554 shell "magisk -v"
```

If the normal `magisk` command is not on `PATH`, inspect the existing runtime path before using a fallback:

```powershell
& $adb -s emulator-5554 shell "/data/adb/magisk/magisk -v"
& $adb -s emulator-5554 shell "/debug_ramdisk/magisk -v"
```

Do not treat a missing `magisk` command as proof that the APK is absent. Check the package separately:

```powershell
& $adb -s emulator-5554 shell "pm path com.topjohnwu.magisk"
```

### 5. Verify with Root Checker

Installed Root Checker activities previously observed on this instance include:

```text
com.joeykrim.rootcheck/.MainActivity
com.anu.developers3k.rootchecker/.MainActivity
```

Launch the selected checker only after `su -c id` passes:

```powershell
& $adb -s emulator-5554 shell "am start -n com.joeykrim.rootcheck/.MainActivity"
```

Inspect the checker UI or capture a screenshot and confirm that it reports root access. Package presence alone is not a root result.

## Important limitations

- MuMu is not the old Android Studio API 34 AVD.
- `root_permission=true` and `adb root` do not by themselves install an application-accessible `su` binary.
- The proven repair above is a live Magisk setup. Verify it after every reboot; do not call root persistent unless a cold-boot test proves persistence.
- Do not repeatedly run `adb root`, repeatedly restart MuMu, or repeatedly reinstall Magisk.
- If the live setup fails, capture its exact output and diagnose that failure before trying anything else.
=======
# Working root method for MuMu Player

## Summary

MuMu Player can be rooted using the Magisk v30.7 live setup workflow.
The proven verification command is:

```
adb shell "su -c id"
```

A successful result contains:

```
uid=0(root) ... context=u:r:magisk:s0
```

Magisk version reports as approximately `30.7:MAGISK:R`.

## Do NOT use

```
adb shell id
```

This checks the ADB shell UID, which may not be root even when
`su -c id` works correctly. The device shell may not be root while
the `su` binary is available and functional.

## Prerequisites

- MuMu Player installed (Android 15 / API 35 / x86_64)
- ADB configured and connected to the MuMu device (serial: emulator-5554)
- MuMu Manager at: `C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe`
- Required assets (not in repository, must be supplied):
  - `assets/magisk-v30.7.apk` — Magisk v30.7 APK
  - `.tools/magisk-source/` — Magisk source tree including `scripts/live_setup.sh`
  - `lib/x86_64/libbusybox.so` — BusyBox binary extracted from the APK

## Root Workflow

1. Check ADB is available and device is connected
2. Run `adb shell "su -c id"`
3. If `uid=0(root)` is returned, the device is rooted — stop
4. If root is not active:
   a. Enable MuMu root permission setting
   b. Restart MuMu if necessary
   c. Wait for ADB to become ready again
   d. Stage the live Magisk setup (`.tools/magisk-source/scripts/live_setup.sh`)
   e. Run the live setup
   f. Wait for Magisk/root
   g. Verify with `adb shell "su -c id"`
5. Stop once root is verified

## Scripts

| Script | Purpose |
|--------|---------|
| `root-mumu.ps1` / `root-mumu.cmd` | Core root workflow (deterministic state machine) |
| `start-mumu-root.ps1` / `start-mumu-root.cmd` | Start MuMu + root in one operation |
| `watch-mumu-root.ps1` / `watch-mumu-root.cmd` | Watch for new MuMu sessions and root them |
| `install-mumu-root-watcher.cmd` | Install automatic watcher via scheduled task |
| `uninstall-mumu-root-watcher.cmd` | Remove the automatic watcher |

## User Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-mumu-root.cmd
```

Or simply:

```cmd
.\start-mumu-root.cmd
```

## Verification

After running any script, verify root with:

```cmd
adb shell "su -c id"
```

Expected output contains `uid=0(root)` and `context=u:r:magisk:s0`.
>>>>>>> theirs
