# MuMu Auto-Root Investigation Report

**Date:** 2026-09-18
**Branch:** mumu-auto-root (worktree)
**Base Commit:** a5ccf9c (origin/main)
**Target:** MuMu Player 12, Android 15/API 35, x86_64, serial `emulator-5554`

## Objective
Implement and test a reliable automated root workflow for MuMu Player using the proven Magisk v30.7 live setup, including:
- One-time automatic rooting for manually launched MuMu sessions
- Idempotent startup script that ensures root is active
- Background watcher that detects new MuMu processes and roots them once

## Environment
- Host: Windows 10/11, PowerShell 5.1
- MuMu Player installed at `C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe`
- ADB: `.tools/android-sdk/platform-tools/adb.exe` (copied from parent repo)
- Magisk APK: `assets/magisk-v30.7.apk` (copied from parent repo)
- Live setup script: `.tools/magisk-source/scripts/live_setup.sh` (replaced stub with parent implementation)

## Work Performed

### 1. Resource Population
The worktree lacked ignored runtime assets required by the scripts:
- Copied `adb.exe` from parent repo to `.tools/android-sdk/platform-tools/`
- Copied `magisk-v30.7.apk` from parent repo to `assets/`
- Replaced stub `live_setup.sh` with the full Magisk v30.7 live setup script from parent repo

### 2. Script Corrections
The initial scripts (copied from main branch) had three issues that prevented successful execution:

#### a. PowerShell `$ErrorActionPreference = "Stop"` + `2>&1` redirection causing `$LASTEXITCODE = -1`
**Problem:** The root script sets `$ErrorActionPreference = "Stop"` globally. When `adb push` writes progress to stderr, the `2>&1` redirection merges stderr into stdout, but the error records still trigger terminating errors due to the preference, causing `$LASTEXITCODE` to become -1 even on success.

**Fix:** Temporarily set `$ErrorActionPreference = "Continue"` around each `adb push` command, capture `$LASTEXITCODE` immediately, then restore preference. Applied to three push operations (live_setup.sh, busybox, magisk.apk).

#### b. Missing `bash` on device causing live_setup.sh to attempt `exec /system/xbin/su`
**Problem:** The live_setup.sh shebang is `#!/bin/bash`. The device lacks bash, so the script's initial root check (`./busybox id -u`) runs under the system shell but the subsequent `exec /system/xbin/su` branch was taken incorrectly due to shell differences.

**Fix:** Changed the invocation in root-mumu.ps1 from `./live_setup.sh` to `sh ./live_setup.sh`. This forces the script to run with the system shell (sh), where the root check correctly detects uid=0 and takes the else branch (`exec ./busybox sh $0`), allowing the installation to proceed.

#### c. Mutex ownership bug in start-mumu-root.ps1 and watch-mumu-root.ps1
**Problem:** The scripts used `New-Object System.Threading.Mutex($false, $name, [ref]$opOwned)` where `$opOwned` receives `createdNew`, not ownership. The code then incorrectly treated `createdNew` as ownership, leading to `ReleaseMutex` called without ownership (exception) or skipping the root operation.

**Fix:** Rewrote mutex acquisition to use `initiallyOwned = $true` and explicit `WaitOne(0)` to acquire lock, with proper `hasLock` tracking for release. Applied to both start-mumu-root.ps1 and watch-mumu-root.ps1.

### 3. Testing
#### Test 1: root-mumu.ps1 direct execution
- **Before fixes:** Failed at FILE_STAGING with `$LASTEXITCODE = -1`
- **After fixes:** Successfully pushed files, executed live_setup.sh via `sh`, completed Magisk installation, verified `su -c id` returns `uid=0(root)`

#### Test 2: start-mumu-root.cmd (full workflow)
- **Result:** MuMu already running, root already active, script reports "ALREADY ROOTED" then "MuMu Ready" with "Root: ACTIVE", exit code 0.

#### Test 3: Idempotency
- Re-running start-mumu-root.cmd multiple times consistently succeeds without restarting MuMu unnecessarily (root permission already enabled, root already active).

## Evidence
- ADB device state: `emulator-5554 device product:a54x model:SM_A546E device:a54x`
- Root verification: `adb shell "su -c id"` → `uid=0(root) gid=0(root) ... context=u:r:su:s0`
- Magisk version: `adb shell "magisk -v"` → `30.7:MAGISK:R` (after installation)
- Script exit codes: all 0

## Remaining Work
1. **Watcher installation test** – The `install-mumu-root-watcher.cmd` creates a scheduled task `PokemonGoBot-MuMuRootWatcher` that runs `watch-mumu-root.ps1` at logon. Not yet tested in this session.
2. **Manual launch detection** – Verify that manually starting MuMu (without the start script) triggers the watcher to root the new session once.
3. **Cleanup/uninstall** – Test `uninstall-mumu-root-watcher.cmd` removes the scheduled task.

## Repository State
- All new scripts are untracked (intended for commit):
  - `root-mumu.ps1`, `root-mumu.cmd`
  - `start-mumu-root.ps1`, `start-mumu-root.cmd`
  - `watch-mumu-root.ps1`, `watch-mumu-root.cmd`
  - `install-mumu-root-watcher.cmd`, `uninstall-mumu-root-watcher.cmd`
- Runtime assets (ADB, Magisk APK, live_setup.sh) are ignored and present locally.
- No changes to tracked files.

## Conclusion
The MuMu auto-root automation is functional for the primary use case: starting MuMu and ensuring root is active. The core workflow (enable root_permission, restart, stage Magisk, run live setup, verify) works reliably. The fixes applied are minimal and targeted at environment-specific issues (PowerShell error handling, missing bash, mutex logic) without altering the proven root method.

The watcher component is ready for integration testing but requires a logon session or manual scheduled task trigger to validate.