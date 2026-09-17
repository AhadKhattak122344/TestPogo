# Repository working instructions

Read docs/STATE.md, docs/DEBUGGING.md and docs/CODEX.md before editing.
Use docs/MODEL_STRATEGY.md on every task: Terra/medium routine execution,
Luna/low for worthwhile bounded documentation work, Astra/medium only for hard
evidence-backed decisions. At most one independent worker, no recursion; only
the lead controls devices or their disks. Follow the actual tool contract.

Inspect Git status and checkpoint before moving files. Preserve unrelated edits,
working functionality and downloaded Android/VM assets. The real CLI is
android_lab/cli.py, installed as lab via root pyproject.toml. Use uv sync --extra
test, uv run lab --help, and the full tests/ suite. Keep output in artifacts/;
use artifacts/tmp for Windows Temp problems. Run tools/windows/Test-Profiles.ps1
after script changes and tools/verify_repository.py plus git diff --check.

Before any experiment read experiments/EXPERIMENT_LOG.md. After each attempt
append date, environment, hypothesis, one changed variable, exact command/action,
exit code, observed result, evidence paths and next decision. Distinguish verified,
reported, failed, inconclusive and not-run outcomes. Put raw/private data only in
artifacts/. Update docs/STATE.md when findings change. Never invent missing logs.

## MuMu Startup and Root

MuMu startup and root are treated as one operation.

If the user says anything equivalent to:

- run MuMu
- open MuMu
- start MuMu
- launch emulator
- start emulator
- open Pokémon emulator
- start the Pokémon environment
- get MuMu running

DO NOT only launch MuMu.

Use:

.\start-mumu-root.cmd

or its underlying implementation.

Success means BOTH:

MuMu is running

AND

adb shell "su -c id"

returns:

uid=0(root)


If MuMu was launched manually outside the repo, the installed
PokemonGoBot-MuMuRootWatcher scheduled task should automatically run
the existing root workflow.

DO NOT rediscover Magisk setup unless root-mumu.ps1 itself reports a
specific failure.

Do not directly tell the user to run:

.\root-mumu.ps1

because their normal PowerShell execution policy blocks PS1 scripts.

For manual use prefer:

.\start-mumu-root.cmd

or:

.\root-mumu.cmd

Both CMD files invoke PowerShell with ExecutionPolicy Bypass.

## Running MuMu Player with Magisk, Zygisk, GPS Joystick and Pokemon Go

### Prerequisites
- MuMu Player 6.7.1.0 installed at `C:\Program Files\Netease\MuMuPlayer\`
- Android SDK at `Pokemon_Go_Bot\.tools\android-sdk\`
- ADB at `Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe`
- Magisk APK at `Pokemon_Go_Bot\.tools\Magisk-v30.7.apk`
- Zygisk at `Pokemon_Go_Bot\assets\zygisk-next-v1.5.0.zip`
- GPS Joystick from Play Store: `com.theappninjas.fakegpsjoystick`
- Pokemon Go APKs at `Pokemon_Go_Bot\artifacts\pgo-apk\`

### 1. Boot MuMu Player VM
```bash
# Launch via MuMu CLI (must use this, not VBoxManage directly)
"C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe" control launch --vmindex all

# VM will boot. Wait for ADB to detect it:
"C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe" devices
# Expected: emulator-5554 device
```

### 2. Enable Root and Configure Magisk
```powershell
$adb = "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe"
$serial = "emulator-5554"

# Enable root via adb root
& $adb -s $serial root

# Push Magisk APK and Zygisk to device
& $adb -s $serial push "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\Magisk-v30.7.apk" /data/local/tmp/magisk.apk

# Install Magisk APK
& $adb -s $serial shell pm install -r -g /data/local/tmp/magisk.apk

# Extract Zygisk from zip and push .so files
# Extract lib/x86_64/libzygisk.so, libpayload.so, libzn_loader.so from zygisk-next-v1.5.0.zip
& $adb -s $serial push libzygisk.so /data/local/tmp/libzygisk.so
# ... push all 3 zygisk .so files

# Enable mock location (needed for GPS Joystick)
& $adb -s $serial shell settings put secure mock_location 1
```

### 3. Complete Magisk Setup (GUI)
1. Open Magisk app on VM - click "Install" on Magisk card
2. When prompted, select "Set Location" or skip setup wizard
3. Magisk daemon should show `30.7:MAGISK:R`
4. Verify root: `adb shell su -c 'id'` → uid=0(root), context=u:r:magisk:s0
5. Zygisk: `adb shell getprop zygisk.enabled` → true

### 4. Install and Configure GPS Joystick
1. Open Play Store on VM, search "GPS JoyStick", install `com.theappninjas.fakegpsjoystick`
2. Grant permissions: ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION
3. Set as mock location app: `settings put secure mock_location_app com.theappninjas.fakegpsjoystick`
4. Open GPS Joystick app
5. In Setup Wizard, click "Skip this step" (mock location already configured)
6. In main screen: "Set Location" is already selected
7. Enter coordinates in "Latitude, Longitude" field (e.g., `407128740060` for NYC 40.7128,-74.0060)
8. Click "START"
9. GPS Joystick overlay appears - use joystick or set location

### 5. Install Pokemon Go
```powershell
# Install via install-multiple (base + split APK)
& $adb -s $serial install-multiple -r -g "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\artifacts\pgo-apk\base.apk" "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\artifacts\pgo-apk\split_config.arm64_v8a.apk"

# If install-multiple fails, install base APK alone first:
& $adb -s $serial install "C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\artifacts\pgo-apk\base.apk"
```

### 6. Launch Pokemon Go
```powershell
# Launch PGO (activity: UnityMainActivity)
& $adb -s $serial shell am start -W -n com.nianticlabs.pokemongo/com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity

# Verify running
& $adb -s $serial shell pidof com.nianticlabs.pokemongo
& $adb -s $serial shell dumpsys window | Select-String "mCurrentFocus"
```

### 7. Verify Everything is Working
```powershell
# Check Magisk
& $adb -s $serial shell "magisk -v"  # → 30.7:MAGISK:R
& $adb -s $serial shell "su -c 'id'" # → uid=0(root) context=u:r:magisk:s0

# Check Zygisk
& $adb -s $serial shell "getprop zygisk.enabled" # → true

# Check mock location
& $adb -s $serial shell "settings get secure mock_location"        # → 1
& $adb -s $serial shell "settings get secure mock_location_app"   # → com.theappninjas.fakegpsjoystick
& $adb -s $serial shell "dumpsys location" | Select-String "last location" # → mock coordinates

# Check PGO
& $adb -s $serial shell "pidof com.nianticlabs.pokemongo"
& $adb -s $serial shell "dumpsys window" | Select-String "mCurrentFocus"
```

### Troubleshooting
- **MuMu VM won't start**: Kill all MuMu processes, delete `.MUMUNX/VirtualBox.xml`, re-register VM with VBoxManage, fix disk UUID mismatches in .nemu file
- **Magisk su not found after reboot**: Re-run `adb root`, or re-run live_setup.sh from magisk-source/scripts/
- **ADB shows offline**: Wait 1-2 minutes, restart ADB server (`adb kill-server && adb start-server`)
- **GPS Joystick START doesn't change location**: Clear text field first, re-enter coordinates, click START
- **PGO says Failed to Sign In**: This is a Niantic server-side issue, not a local configuration problem
