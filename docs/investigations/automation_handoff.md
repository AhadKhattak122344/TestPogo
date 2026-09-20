# Automation Handoff — MuMu Startup + Error 12

## ROOT PROVEN WORKFLOW

Enable root_permission → restart MuMu → wait for ADB/boot → stage Magisk v30.7 live setup → run via `sh` → verify su. Full details in docs/MUMU_AUTOMATION_SOURCE_NOTES.md.

## ROOT EXACT COMMANDS

```powershell
& MuMuManager.exe setting --vmindex 0 --key root_permission --value true
& MuMuManager.exe control --vmindex 0 restart
adb -s <SERIAL> push live_setup.sh /data/local/tmp/live_setup.sh
adb -s <SERIAL> shell "cd /data/local/tmp && sh ./live_setup.sh"
adb -s <SERIAL> shell "su -c id"
```

## ROOT SIDE EFFECTS

- MuMu restarts during root enablement; ADB disconnects temporarily after live setup
- Device may go offline briefly; bounded wait up to 90s expected
- Magisk may not be on PATH; check `/data/adb/magisk/magisk -v` fallback

## ERROR12 ROOT CAUSE

Stale third-party mock/test-provider state. GPS JoyStick or shell-owned test providers occupied GPS/network slots with mock flags, blocking Pokemon GO at UnityMainActivity. MuMu native Virtual Location bypasses this via GnssService without mock labels.

## ERROR12 EXACT COMMANDS

```powershell
adb -s <SERIAL> shell am force-stop com.nianticlabs.pokemongo
adb -s <SERIAL> shell am force-stop com.theappninjas.fakegpsjoystick
adb -s <SERIAL> shell am force-stop com.locationchanger
adb -s <SERIAL> shell cmd location providers remove-test-provider gps
adb -s <SERIAL> shell cmd location providers remove-test-provider network
adb -s <SERIAL> shell settings put secure mock_location_app null
```

## ERROR12 VERIFICATION

Filtered `dumpsys location` → GPS owner: 1000/android[GnssService] (no [mock]), no mock providers, mock_location_app=null.

## FILES TO REUSE

`root-mumu.ps1/cmd` (repo root)
`.tools/magisk-source/scripts/live_setup.sh`, `assets/magisk-v30.7.apk`
`docs/investigations/error12_stage3_mumu_native.md`

## NEW AUTOMATION MODULES

| File | Role |
|------|------|
| `scripts/mumu/common/Resolve-Adb.ps1` | Resolves ADB: project .tools, PATH, WinGet |
| `scripts/mumu/common/Resolve-MuMuDevice.ps1` | Resolves canonical MuMu serial |
| `scripts/mumu/common/Wait-MuMuBoot.ps1` | Waits for ADB + Android boot |
| `scripts/mumu/common/Write-MuMuLog.ps1` | Logs to logs/mumu-bootstrap/ |
| `scripts/mumu/root/apply-root.ps1/cmd` | Applies root via root-mumu.ps1, verifies su |
| `scripts/mumu/location/fix-error12.ps1/cmd` | Proven Error 12 cleanup |
| `scripts/mumu/location/verify-location.ps1/cmd` | Filtered location verification |
| `scripts/mumu/start-mumu-stack.ps1/cmd` | Master orchestrator (Normal/AttachOnly) |
| `run-mumu.cmd` | Top-level entry point |

## ORCHESTRATOR FLOW

[1/7] RESOLVE ADB → [2/7] START/DETECT MUMU → [3/7] WAIT FOR ANDROID → [4/7] APPLY ROOT → [5/7] WAIT FOR ROOTED DEVICE → [6/7] FIX ERROR12 STATE → [7/7] VERIFY

## ERROR CODES

0=success, 10=adb missing, 20=MuMu missing, 30=boot timeout, 40=root workflow failure, 50=root verification failure, 60=location cleanup failure, 70=location verification failure

## ROOT PRECHECK

NONE — root is applied unconditionally after boot. We know root is unavailable after a fresh boot.

## MUTATION ORDER

ROOT THEN ERROR12 CLEANUP — mandatory. Root may restart Android or temporarily disconnect ADB.

## FAILED COMMANDS / DO NOT USE

`./live_setup.sh` (no bash), `adb shell id` (not app root), add-test-provider (creates mock state), mock_location_app=com.theappninjas.fakegpsjoystick (causes isMock=true), hardcoded coordinates.

## NEXT SESSION

Verify start-mumu-stack.ps1 cold start, validate -AttachOnly mode on running MuMu, confirm lock prevents duplicate bootstrap.
