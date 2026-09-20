# MuMu Automation — Source Notes

Recovered proven workflows. Do not redesign. Use as reference only.

---

## ROOT PROVEN WORKFLOW

### CANONICAL ROOT CMD

`root-mumu.cmd` (repo root) — thin wrapper, invokes `root-mumu.ps1`.

### CANONICAL ROOT PS1

`root-mumu.ps1` (repo root) — deterministic state machine, stages Magisk v30.7 live setup, executes, verifies.

### SUPPORTING FILES

| File | Role |
|------|------|
| `start-mumu-root.cmd` / `.ps1` | Start MuMu + root in one operation |
| `watch-mumu-root.cmd` / `.ps1` | Background watcher; roots new MuMu sessions |
| `install-mumu-root-watcher.cmd` | Scheduled task at logon |
| `.tools/magisk-source/scripts/live_setup.sh` | Magisk v30.7 live setup (staged to /data/local/tmp) |
| `assets/magisk-v30.7.apk` | Magisk APK source |

### DOES SCRIPT RESTART ANDROID/MUMU

YES — `root-mumu.ps1` Step E: `& $manager control --vmindex 0 restart` after enabling root_permission. `start-mumu-root.ps1` launches MuMu if not running, then roots.

### EXPECTED ADB DISCONNECT

YES — ADB drops temporarily during MuMu restart (Step E) and after live setup execution (Step H/I). Scripts wait for reconnection via bounded loop (90s default).

### POST-ROOT VERIFICATION

Command: `adb -s <MUMU_SERIAL> shell "su -c id"`

PASS requires: `uid=0(root)`

DO NOT use `adb shell id` — that checks ADB shell UID, not application root access.

### EXPECTED PASS OUTPUT

```
uid=0(root) gid=0(root) ... context=u:r:magisk:s0
```

Also verify: `adb -s emulator-5554 shell "su -c whoami"` → `root`

### KNOWN BLOCKERS

1. **Missing bash on device**: live_setup.sh shebang is `#!/bin/bash`. Device lacks bash. Fix: invoke via `sh ./live_setup.sh` (not `./live_setup.sh`).
2. **PowerShell $ErrorActionPreference**: `$ErrorActionPreference = "Stop"` + `2>&1` causes `$LASTEXITCODE = -1` on adb push. Fix: temporarily set to `"Continue"` around push operations.
3. **Mutex ownership**: `New-Object Mutex($false, ...)` returns `createdNew` not ownership. Fix: use `initiallyOwned = $true` with `WaitOne(0)` tracking.
4. **Magisk not on PATH after root**: Check `/data/adb/magisk/magisk -v` or `/debug_ramdisk/magisk -v` as fallbacks. `pm path com.topjohnwu.magisk` confirms package presence.
5. **docs/ROOT_MAGISK_WORKING.md has merge conflict markers** (ours/theirs). Use the "theirs" section (lines 233-318) as the canonical readable version.

---

## ERROR 12 — ROOT CAUSE

Pokemon GO Error 12 was caused by **stale third-party mock/test-provider state** occupying GPS/network provider slots. When GPS JoyStick (or shell-owned test providers) held mock provider entries, Pokemon GO could not transition from UnityMainActivity.

The successful fix: **MuMu native Virtual Location** via `MuMuManager.exe control tool location`, which feeds coordinates through the native GnssService layer (identity=1000/android[GnssService]) without mock provider labels, with realistic satellite metadata.

---

## ERROR 12 — EXACT COMMANDS

### PROVEN REQUIRED

| Command | Source |
|---------|--------|
| `& MuMuManager.exe control tool location --vmindex 0 --latitude <LAT> --longitude <LON>` | error12_stage3_mumu_native.md:179 |
| `adb shell am force-stop com.nianticlabs.pokemongo` | error12_stage3_mumu_native.md:183 |
| `adb shell am force-stop com.theappninjas.fakegpsjoystick` | error12_provider.md:119, error12_stage2_nomock.md:27 |
| `adb shell am force-stop com.locationchanger` | error12_stage2_nomock.md:27 |
| `adb shell cmd location providers remove-test-provider gps` | error12_provider.md:122, location-android.md:100 |
| `adb shell cmd location providers remove-test-provider network` | error12_provider.md:122, location-android.md:101 |
| `adb shell settings put secure mock_location_app null` | error12_handoff.md:7 (mock_location_app=null state) |
| `adb -s emulator-5554 shell su -c id` | Root verification across all docs |

### PROVEN OPTIONAL

| Command | Source | Note |
|---------|--------|------|
| `adb shell pm disable-user --user 0 com.locationchanger` | location-android.md:76 | Prevents Location Changer from re-registering providers |
| `adb shell appops set com.theappninjas.fakegpsjoystick android:mock_location deny` | error12_stage2_nomock.md:14 | Deny MOCK_LOCATION when GPS JoyStick not needed |
| `adb shell appops set com.locationchanger android:mock_location deny` | error12_stage2_nomock.md:15 | Deny MOCK_LOCATION when Location Changer not needed |

### FAILED / DO NOT USE

| Command | Reason | Source |
|---------|--------|--------|
| `adb shell settings put secure mock_location_app com.theappninjas.fakegpsjoystick` + `mock_location 1` | Causes Location.isMock()=true on all locations; inherent mock flag cannot be hidden (forbidden) | error12_provider.md:126-128, error12_provider.md:178-180 |
| `adb shell cmd location providers add-test-provider gps/network` | Creates mock provider state; opposite of cleanup | location-android.md:47-48 |
| `./live_setup.sh` (without `sh`) | Fails: no bash on device | mumu-auto-root.md:40 |
| `adb shell id` (without su) | Checks adbd UID not app root; not a valid root proof | ROOT_MAGISK_WORKING.md:255 |
| Hardcoding coordinates (e.g., 40.7580,-73.9855) | Testing-only; final automation must preserve user-selected location | TASK REQUIREMENT |

---

## KNOWN GOOD FINAL ERROR12 STATE

- MuMu native Virtual Location = working
- GPS owner: 1000/android[GnssService]
- Third-party mock provider: absent
- Mock state: false / absent
- Pokemon GO: ERROR 12: NO, MAP: YES, POKESTOPS/GYMS: YES, SPAWNS: YES

**CORRECTION**: An older Stage 3 report may say SPAWNS: NO. The later observed result confirmed **SPAWNS: YES**. See error12_stage3_mumu_native.md:145-158 for the correction note.
