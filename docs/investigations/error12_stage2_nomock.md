# Error 12 Investigation — Stage 2: Clean No-Mock Control

Date: 2026-09-18 15:30Z
Device: MuMu Player (emulator-5554), Android 15 / API 35, Samsung Galaxy A54
Root: Magisk v30.7, `su -c id` = uid=0(root) context=u:r:magisk:s0

## Clean State Verification (BEFORE Pokemon GO Launch)

**Settings:**
- `mock_location_app` = null (cleared)
- `mock_location` = 1 (master switch on, but no app selected)

**AppOps:**
- `com.theappninjas.fakegpsjoystick` MOCK_LOCATION = deny
- `com.locationchanger` MOCK_LOCATION = deny

**Location Providers (dumpsys location):**
- **GPS provider**: No `[mock]` label. identity=1000/android[GnssService] (real hardware). last location=null initially.
- **Network provider**: No `[mock]` label. identity=10025/com.google.android.gms[network_location_provider]. last location=null.
- **Fused provider**: identity=10025/com.google.android.gms[fused_location_provider]. No mock flag on fresh locations.
- **Passive provider**: Aggregates from real providers.

**GPS Hardware**: Nemu GPS (emulator virtual GPS), providing real fixes with satellites=7, C/N0 ~37-51 dB-Hz, accuracy ~0.02m.

## Test Execution

1. Force-stopped all apps: Pokemon GO, GPS JoyStick, Location Changer
2. Denied MOCK_LOCATION AppOp for both location apps
3. Cleared `mock_location_app` setting
4. Removed test provider overrides for `gps` and `network` via `cmd location providers remove-test-provider`
5. Verified clean provider state (no `[mock]`, correct identities)
6. Force-stopped Pokemon GO
7. Launched: `am start -n com.nianticlabs.pokemongo/com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity`
8. Waited 45 seconds
9. Captured screenshot: `docs/investigations/pgo_stage2_clean.png`
10. Verified post-test provider state — remains clean

## Observation Result

| Metric | Result |
|--------|--------|
| ERROR 12 | **YES** |
| MAP LOADS | NO |
| POKESTOPS/GYMS | NO |
| POKEMON SPAWNS | NO |

**Evidence:**
- Game process stays alive (PID 14034), crash buffer empty, no SIGILL
- Activity remains `UnityMainActivity` — no account chooser, no map transition
- Screenshot shows loading screen only
- Real GPS hardware (Nemu GPS) actively delivering fixes to Pokemon GO (visible in dumpsys event log: `gps provider received location[1]` → `gps provider delivered location[1] to 10057/com.nianticlabs.pokemongo/...`)
- No mock providers active at any point during test

## Conclusion

**PROVEN: GPS JoyStick mock provider alone does not fully explain Error 12.**

With ALL third-party mock/test location providers cleanly removed, and the emulator's real virtual GPS (Nemu GPS) providing legitimate location fixes to Pokemon GO, Error 12 **still occurs**.

The game receives real GPS data from the emulator's virtual GPS hardware (identity=android[GnssService], satellites=7, realistic C/N0 values), yet refuses to progress past UnityMainActivity.

## Next Investigation Targets

The next stage should investigate:
1. **MuMu native Virtual Location** — whether MuMu's own virtual location feature (separate from GPS JoyStick) is active or detectable
2. **Root/emulator compatibility** — Magisk root detection, emulator build props, hardware identifiers
3. **System location configuration** — `mock_location` master switch still = 1, possible platform-level mock detection
4. **Play Integrity / device attestation** — emulator vs. real device certification failure
5. **Niantic backend checks** — account/API-level blocking independent of client-side location

Do NOT install HideMockLocation, LSPosed modules, Smali Patcher, or patch Pokemon GO. This stage was ONLY the clean no-mock control.