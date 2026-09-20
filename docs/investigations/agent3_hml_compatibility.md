# Agent 3: HideMockLocation Technical Compatibility Investigation

## Purpose

Determine whether the current HideMockLocation (HML) implementation is technically
compatible with the MuMu Player / Android 15 / API 35 / x86_64 / Magisk / LSPosed
stack. Test against ONLY a benign mock-location detector application.

**This is NOT scoped to Pokémon GO at any point.**

## Environment

| Component | Value |
|---|---|
| Runtime | MuMu Player |
| Android | 15 (API 35) |
| CPU ABI | x86_64 |
| Device | SM_A546E (a54x) |
| ADB endpoint | 127.0.0.1:16384 |
| Magisk | v30.7 (APK installed) |
| LSPosed | Not yet installed / unknown |
| Zygisk | ZygiskNext v1.5.0 (module present, daemon inactive) |
| HML Candidate | auag0/HideMockLocation v2.3.1 |
| Test App | auag0/MockLocationDetector v2.0.0 |

## Phase 1: Research Current HML

### Repository

**auag0/HideMockLocation** — https://github.com/auag0/HideMockLocation

### Latest Relevant Stable Version

**v2.3.1** (released 2026-05-12) — latest stable release.

Release history (v2.x series):
| Version | Release Date | Key Changes |
|---|---|---|
| v2.0.0 | 2026-04-15 | Fully migrated to libxposed API 101; fixed Settings class hook bug |
| v2.1.0 | 2026-04-16 | (unreleased details seen in release list) |
| v2.2.0 | 2026-04-16 | Added SettingsProvider hooks |
| v2.2.1 | 2026-04-16 | Icon update |
| v2.3.0 | 2026-04-17 | Fixed SettingsProvider issues; added AppOpsService hooks |
| v2.3.1 | 2026-05-12 | Disabled AppOps hooks (was causing issues; use HideMyAppList instead) |

### Compatibility Matrix

| Requirement | HML Support | Compatible? |
|---|---|---|
| Android 15 (API 35) | Supports Android 6–16 | **YES** |
| x86_64 ABI | Pure Java/Kotlin, no native code | **YES** |
| Xposed API 101 | v2.x requires API 101+ | **YES** (if LSPosed supports API 101) |
| Xposed API 100 | v1.2.2 or below | N/A (fallback) |
| LSPosed | Yes, designed for LSPosed | **YES** |

### APK Properties (verified via aapt)

HideMockLocation v2.3.1:
- Package: `io.github.auag0.hidemocklocation`
- versionCode: 11, versionName: 2.3.1
- minSdk: 26, targetSdk: 36
- No native code (pure Java/Kotlin Xposed module)
- Downloaded: artifacts/agent3-hml-prep/HideMockLocation-v2.3.1.apk (21,958 bytes)

MockLocationDetector v2.0.0:
- Package: `io.github.auag0.mocklocationdetector`
- versionCode: 2, versionName: 2.0.0
- minSdk: 23, targetSdk: 36
- native-code: arm64-v8a, armeabi-v7a, x86, x86_64
- Downloaded: artifacts/agent3-hml-prep/MockLocationDetector-v2.0.0.apk (1,238,564 bytes)

### Hooked Methods (from README)

- `android.location.Location`: `isFromMockProvider()`, `isMock()`, `setIsFromMockProvider()`, `setMock()`, `getExtras()`, `setExtras()`, `set()`
- `android.provider.Settings`: `Secure.getStringForUser()`
- `android.app.AppOpsManager`: `checkOp()`, `checkOpNoThrow()`, `unsafeCheckOp()`, `unsafeCheckOpNoThrow()`
- `com.android.providers.settings.SettingsProvider`: `call()`
- `com.android.server.appop.AppOpsService` / `com.android.server.AppOpsService`: `checkOperationImpl()`, `checkOperation()`

### Version Selection Logic

- If LSPosed API >= 101: use **v2.3.1**
- If LSPosed API <= 100: use **v1.2.2** (fallback)
- v2.3.1 disabled AppOps hooks in v2.3.1; recommends HideMyAppList for that coverage.
  This is acceptable for the test app scope.

## Phase 2: Match to Framework

### framework.txt Status (read from `$coord\status\framework.txt`)

**Latest reading (2026-09-18T14:15Z):**
```
ROOT READY = NO
MAGISK READY = NO
MAGISK VERSION = UNKNOWN
ZYGISK AVAILABLE = UNKNOWN
ZYGISK ENABLED = UNKNOWN
LSPOSED INSTALLED = UNKNOWN
LSPOSED ACTIVE = UNKNOWN
LSPOSED VERSION = UNKNOWN
LSPOSED API = UNKNOWN
REBOOT SURVIVES = UNKNOWN
EXACT BLOCKER = MuMu is Android 15/API 35/x86_64 at 127.0.0.1:16384; canonical workflow hard-codes emulator-5554 and cannot address the running instance. su is missing.
```

### Direct Device Verification (via ADB at 127.0.0.1:16384)

Cross-checked against framework.txt to understand the actual device state:

| Check | Result |
|---|---|
| ADB connectivity | Device accessible at 127.0.0.1:16384 (product:a54x, model:SM_A546E) |
| whoami | `root` |
| id | `uid=0(root) gid=0(root) context=u:r:su:s0` |
| Magisk package | `com.topjohnwu.magisk` installed |
| su binary | NOT accessible (`su: inaccessible or not found`) |
| Magisk daemon | Not running (no magisk process) |
| ZygiskNext module | Present at `/data/adb/modules/zygisksu` v1.5.0 but daemon inactive |
| zygisk.enabled prop | Not set |
| /system/lib64/zygisk/ | Does not exist |
| LSPosed package | NOT installed |
| /system/xposed/ | Does not exist |
| Android SDK | 35 |
| Android Release | 15 |
| CPU ABI | x86_64 |
| Users | 1 (UserInfo{0:Owner:4c13} running) |

### Version Selection

**HML Version Selected: v2.3.1** (when LSPosed API >= 101)
- Latest stable release (2026-05-12)
- Fully migrated to libxposed API 101
- Supports Android 6-16 (including Android 15/API 35)
- No native code — works on x86_64 without issue
- APK downloaded to: `artifacts/agent3-hml-prep/HideMockLocation-v2.3.1.apk`

**Fallback: v1.2.2** — if LSPosed API is found to be 100 or lower

### Blocking Status

Framework is NOT ready. Per task instructions, do NOT install/enable HML until:
- ROOT READY = YES
- LSPOSED ACTIVE = YES

Both are currently unmet (ROOT=NO, LSPOSED=UNKNOWN/NO).

## Phase 3: Multiuser

### Status: COMPLETE (read-only investigation)

Source: `$coord\status\multiuser.txt`

| Field | Value |
|---|---|
| ANDROID USERS | 1 (UserInfo{0:Owner:4c13} running) |
| POGO USER | user 0 |
| SECONDARY PROFILE | none |
| XSPACE EQUIVALENT | none |
| SCREENSHOT APPLIES | NO |
| RECOMMENDED SCOPE | single user 0; do not attempt XSpace/secondary-user steps |
| BLOCKER | none (read-only investigation complete; LSPosed not installed, only Magisk) |

**Implications:**
- Only a single Android user (user 0 / Owner) exists on this MuMu instance.
- No secondary profile or Xiaomi XSpace equivalent to worry about.
- HML/MockLocationDetector scope is single-user only. No multiuser installation steps needed.
- Multiuser is NOT a blocker for HML compatibility testing.

## Phase 4: Install / Verify HML

**Status: PENDING** — blocked by framework readiness.

## Phase 5: Benign Test Application

**Status: PENDING** — blocked by framework readiness.

### Planned Test Procedure (once framework is ready)

1. Install GPS Joystick mock location provider (com.theappninjas.fakegpsjoystick) if not already installed.
2. Install MockLocationDetector (io.github.auag0.mocklocationdetector).
3. **BEFORE**: Set GPS Joystick as mock location provider, run MockLocationDetector, capture all 4 detection results.
4. Install and enable HML in LSPosed, scope to:
   - System Framework (system)
   - Settings Storage (com.android.providers.settings)
   - MockLocationDetector (io.github.auag0.mocklocationdetector)
   **Do NOT add com.nianticlabs.pokemongo to HML scope.**
5. Reboot if required.
6. **AFTER**: Run MockLocationDetector again, capture all 4 detection results.
7. Record exactly which checks change between BEFORE and AFTER.

### MockLocationDetector Detection Methods

1. **AppOpsManager** — checks if any app has ACCESS_MOCK_LOCATION permission
2. **Settings.Secure** — reads `mock_location` setting (non-zero = mock enabled)
3. **Location object** — inspects `isFromMockProvider()`, `isMock()`, extras bundle `mockLocation`
4. **Hook detection** — verifies Location fields have not been tampered with

## Device Lock

- Lock path: `$env:LOCALAPPDATA\PokemonGoLSPosedDebug\device.lock`
- Lock NOT yet acquired (waiting for framework readiness)
- Will acquire before any device mutations, release after.

## Decision Log

| Date/Time | Decision | Rationale |
|---|---|---|
| 2026-09-18T14:02Z | Started Phase 1 research | Per task instructions: "You may perform web/repo research immediately." |
| 2026-09-18T14:05Z | Downloaded HML v2.3.1 and MockLocationDetector v2.0.0 APKs | Preparation only; NOT installed on device. |
| 2026-09-18T14:10Z | Checked device state directly via ADB | framework.txt shows UNKNOWN but device is ADB-accessible. Root partially available (adb root), LSPosed not installed, Magisk su daemon not running. |
| 2026-09-18T14:10Z | Waiting for framework.txt ROOT READY=YES and LSPOSED ACTIVE=YES | Per task: "DO NOT install or enable HML until confirmed." |
