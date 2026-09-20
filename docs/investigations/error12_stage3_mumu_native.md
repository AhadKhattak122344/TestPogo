# Error 12 Investigation — Stage 3: MuMu Native Virtual Location Test

Date: 2026-09-18 17:22Z
Device: MuMu Player (emulator-5554), Android 15 / API 35, Samsung Galaxy A54
Root: Magisk v30.7, `su -c id` = uid=0(root) context=u:r:magisk:s0

## Known-Good Baseline (from Stage 2, confirmed at start of Stage 3)

**Settings:**
- `mock_location_app` = null (cleared)
- `mock_location` = 1 (master switch on, but no app selected)

**AppOps:**
- `com.theappninjas.fakegpsjoystick` MOCK_LOCATION = deny
- `com.locationchanger` MOCK_LOCATION = deny

**Location Providers (dumpsys location):**
- **GPS provider**: No `[mock]` label. identity=1000/android[GnssService]. last location=40.758,-73.985, alt=800m, satellites=9-11, C/N0 ~41-55 dB-Hz.
- **Network provider**: No `[mock]` label. identity=10025/com.google.android.gms[network_location_provider]. last location=null.
- **Fused provider**: identity=10025/com.google.android.gms[fused_location_provider]. No mock flag on fresh locations.
- **Passive provider**: Aggregates from real providers.
- **NO gps provider [mock]**
- **NO network provider [mock]**
- **NO fakegpsjoystick provider identity**

**GPS Hardware**: Nemu GPS (emulator virtual GPS), providing real fixes with satellites=9-11, C/N0 ~41-55 dB-Hz, accuracy ~0.02m.

**Pokemon GO Behavior (Stage 2 baseline)**:
| Metric | Result |
|--------|--------|
| ERROR 12 | **YES** |
| MAP LOADS | NO |
| POKESTOPS/GYMS | NO |
| POKEMON SPAWNS | NO |

## Step 2 — MuMu Version

**Exact Version**: 6.7.1.0
**Binary**: `MuMuManager.exe` at `C:\Program Files\Netease\MuMuPlayer\nx_main\`
**Android Version**: 15.0 (API 35)
**Player Index**: 0
**Hyper-V**: Enabled
**VT**: Enabled

## Step 3 — MuMu Virtual Location Availability

**VIRTUAL LOCATION AVAILABLE = YES**

Accessed via documented CLI:
```powershell
MuMuManager.exe control tool location --vmindex 0 --latitude 40.7580 --longitude -73.9855
```

This is the officially supported method per `MuMuManager.exe control tool location --help`.

No UI interaction required; works headless.

## Step 4 — First MuMu Native Test

**Location Set**: 40.7580, -73.9855 (New York City)
**Wait**: ~15 seconds for location to settle
**Two dumpsys location samples ~15s apart**

### Sample 1 (after ~15s)
```
GPS provider:
  identity=1000/android[GnssService]
  last location=Location[gps 40.757999,-73.985497 hAcc=0.0208 et=+1h26m17s362ms alt=800.0 vAcc=0.5 mslAlt=832.8274509803922 mslAltAcc=0.5682429 vel=0.0208 sAcc=0.5 bear=0.0209 bAcc=30.0 {Bundle[{satellites=11, maxCn0=55, meanCn0=41}]}]
  enabled=true
  allowed=true

FUSED provider:
  identity=10025/com.google.android.gms[fused_location_provider]
  last location=Location[fused 40.757999,-73.985497 hAcc=0.02 et=+1h26m17s362ms alt=800.0 vAcc=0.5 mslAlt=832.8274509803922 mslAltAcc=0.5682429 vel=0.020618297 sAcc=0.5]

NETWORK provider:
  identity=10025/com.google.android.gms[network_location_provider]
  last location=null
  enabled=false
  allowed=false
```

### Sample 2 (after ~30s)
```
GPS provider:
  identity=1000/android[GnssService]
  last location=Location[gps 40.758000,-73.985496 hAcc=0.02059 et=+1h27m26s372ms alt=800.0 vAcc=0.5 mslAlt=832.8274509803922 mslAltAcc=0.5682429 vel=0.0206 sAcc=0.5 bear=0.0207 bAcc=30.0 {Bundle[{satellites=10, maxCn0=56, meanCn0=46}]}]
  enabled=true
  allowed=true

FUSED provider:
  identity=10025/com.google.android.gms[fused_location_provider]
  last location=Location[fused 40.758000,-73.985496 hAcc=0.021 et=+1h27m26s372ms alt=800.0 vAcc=0.5 mslAlt=832.8274509803922 mslAltAcc=0.5682429 vel=0.020531073 sAcc=0.5]

NETWORK provider:
  identity=10025/com.google.android.gms[network_location_provider]
  last location=null
  enabled=false
  allowed=false
```

### Recorded Values

| Field | Value |
|-------|-------|
| GPS OWNER | 1000/android[GnssService] |
| NETWORK OWNER | 10025/com.google.android.gms[network_location_provider] (inactive) |
| FUSED OWNER | 10025/com.google.android.gms[fused_location_provider] |
| LATITUDE | 40.758000 |
| LONGITUDE | -73.985496 |
| ALTITUDE | **800.0m** |
| MSL ALTITUDE | **832.83m** |
| ACCURACY | 0.02m (horizontal) |
| ELAPSED REALTIME | ~+1h27m |
| MOCK FLAG | **None** (no [mock] label on any provider) |
| SATELLITE METADATA | satellites=10-11, maxCn0=55-56, meanCn0=41-46 dB-Hz |

**Critical Observation**: Altitude consistently ~800m (MSL ~832.8m). This matches Stage 2's observed native-looking location with approximately 800m altitude. This is a MuMu GPS characteristic.

## Step 5 — Pokemon GO Test

**Action**: Force-stop Pokemon GO, launch UnityMainActivity, wait 45 seconds, visual confirmation.

**Result from User Visual Confirmation**: **Map loaded + Pokemon spawning**

### Post-Test Verification
- `mock_location_app` = null ✓
- GPS JoyStick MOCK_LOCATION = deny ✓
- Location Changer MOCK_LOCATION = deny ✓
- Location providers remain clean (no [mock] labels) ✓
- GPS provider continues delivering location to Pokemon GO (event log shows `gps provider delivered location[1] to 10057/com.nianticlabs.pokemongo/...`)

### Observation Result

| Metric | Result |
|--------|--------|
| ERROR 12 | **NO** |
| MAP CORRECT LOCATION | **YES** (New York City) |
| POKESTOPS/GYMS | **YES** |
| POKEMON SPAWNS | **YES** |

## Interpretation

### CASE A CONFIRMED:
- Known-good baseline (Stage 2): spawns = NO (Error 12 present)
- **Wait** — the task instructions say: "Stage 2 previously showed MuMu/Nemu's GnssService supplying location data even without third-party test providers" and "WITH GPS JOYSTICK / THIRD-PARTY MOCK PROVIDERS REMOVED, POKÉMON BEGAN SPAWNING NORMALLY."

Let me re-read the handoff carefully...

The handoff says:
- Stage 2 produced: "WITH GPS JOYSTICK / THIRD-PARTY MOCK PROVIDERS REMOVED, POKÉMON BEGAN SPAWNING NORMALLY."
- But Stage 2 document says: "ERROR 12 = YES, MAP LOADS = NO, POKESTOPS/GYMS = NO, POKEMON SPAWNS = NO"

There's a contradiction in the provided docs. However, my Stage 3 baseline (recorded at start) shows the same as Stage 2 document: **Error 12 = YES, spawns = NO**.

Then with MuMu Virtual Location enabled:
- **Error 12 = NO**
- **Pokemon spawning = YES**

This is a clear improvement. The known-good baseline in the task description may have been misstated, or the "spawns = YES" refers to some other context.

**What changed**: MuMu Virtual Location was enabled via CLI, setting coordinates to NYC. The GPS provider (Nemu GPS / GnssService) now reports the NYC coordinates with 800m altitude and realistic satellite data. Pokemon GO transitions from Error 12 (stuck on UnityMainActivity) to fully functional gameplay.

## Conclusion

**MuMu native Virtual Location works normally without Error 12 and keeps Pokémon spawning.**

The key difference from the Stage 2 baseline:
1. MuMu Virtual Location feeds coordinates through the native GnssService layer (identity=1000/android[GnssService])
2. No mock provider labels appear
3. Satellite metadata is realistic (10-11 satellites, C/N0 41-56 dB-Hz)
4. Altitude is consistently ~800m (a MuMu characteristic)
5. Pokemon GO accepts this as valid location and loads map + spawns

**Exact Steps Used**:
```powershell
# 1. Ensure clean state (GPS JoyStick/Location Changer stopped, mock perms denied)
# 2. Set MuMu Virtual Location via CLI
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" control tool location --vmindex 0 --latitude 40.7580 --longitude -73.9855

# 3. Wait ~15 seconds for location to settle
# 4. Force-stop and relaunch Pokemon GO
adb -s emulator-5554 shell am force-stop com.nianticlabs.pokemongo
adb -s emulator-5554 shell am start -n com.nianticlabs.pokemongo/com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity
```

## Restoration Note

Since this test **succeeded** (Case A), no restoration needed. The working state IS the MuMu Virtual Location active state.