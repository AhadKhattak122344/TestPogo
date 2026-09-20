# Pokemod — Native ARM64 Environment Selection (Stage 3)

## Status: RESEARCH COMPLETE — Environment Selected, Migration Planned

## PHASE 1 — Pokemod Requirements

### Research Sources

| Source | Type |
|---|---|
| pokemod.dev (official site) | OFFICIAL |
| pokemod.dev/about-us | OFFICIAL |
| github.com/The-Pokemod-Group | OFFICIAL |
| github.com/The-Pokemod-Group/eMagisk | OFFICIAL |
| github.com/The-Pokemod-Group/Atlas-All-In-One | OFFICIAL |
| Platinmods FAQ (Zygisk mods) | COMMUNITY |
| XDA Developers forums | COMMUNITY |
| Stage 2 compatibility findings (this repo) | INFERENCE |

### Findings

**SUPPORTED CPU ARCHITECTURE:**
- `arm64-v8a` (ARM64) — **OFFICIAL**
  - Pokemod outer injector is ARM64 ELF64 (e_machine=0xb7)
  - Pokemod main payload (~24 MB) is ARM64
  - Only a ~6 KB x86_64 loader/stub exists for x86_64; no full x86_64 payload
  - Source: pokemod.dev, Stage 2 ABI analysis

**SUPPORTED ANDROID VERSIONS:**
- Minimum: Android 8+ (Magisk supports Android 6.0–16; POGO requires Android 9+) — **INFERENCE**
- Recommended range: Android 11–14 — **INFERENCE**
  - Root tooling (Magisk, Zygisk, eMagisk) stable on Android 11–13
  - POGO runs on Android 9+ (Niantic requires Android 9 or above)
  - No official Pokemod Android version stated; no Android 15 support confirmed
  - Source: pokemod.dev, Niantic GO Help Center, Magisk changelog

**ROOT REQUIREMENTS:**
- Rooted Android device **required** — **OFFICIAL**
  - pokemod.dev: "A rooted device is required to run this application"
  - Root is non-negotiable for Pokemod functionality

**MAGISK REQUIREMENTS:**
- Magisk required — **OFFICIAL**
  - eMagisk module (The-Pokemod-Group/eMagisk) targets "devices running Pokemod Atlas"
  - Zygisk must be enabled inside Magisk for mod modules to function
  - Source: eMagisk README, Platinmods FAQ

**ZYGISK REQUIREMENTS:**
- Zygisk required — **OFFICIAL/COMMUNITY**
  - Platinmods FAQ: "Your device needs to have Zygisk enabled and running inside of Magisk"
  - Zygisk mods do not work on x86 emulators (Platinmods FAQ): "Zygisk mods are by today not supported by any known x86 emulators"
  - Source: Platinmods FAQ (COMMUNITY)

**PHYSICAL DEVICE REQUIREMENT:**
- Physical device required, no emulator support — **OFFICIAL + COMMUNITY**
  - Pokemod docs state no emulator support
  - Third-party documentation: "Pokemod doesn't work in emulators, cloned or modified POGO apps"
  - Source: Stage 2 doc, pokemod.dev, community forums

**EMULATOR SUPPORT:**
- Not supported — **OFFICIAL + COMMUNITY**
  - No official emulator compatibility documented
  - Houdini/translation layers break ARM injection tooling (Stage 2 findings)
  - Zygisk cannot function under x86 emulation (Platinmods FAQ)

---

## PHASE 2 — Environment Options Comparison

### A. Spare Physical ARM64 Android Phone

| Property | Value |
|---|---|
| NATIVE ARM64 | Yes |
| ROOTABLE | Yes |
| ANDROID VERSION | 11–14 depending on device |
| ADB | Yes |
| POKEMON GO | Yes |
| POKEMOD SUPPORT | Yes |
| COST RANGE | $0 (existing) or $50–150 used |
| SETUP DIFFICULTY | Low |
| MAJOR DRAWBACK | Requires acquiring hardware if no spare exists |

### B. Cheap Used ARM64 Android Phone

| Property | Value |
|---|---|
| NATIVE ARM64 | Yes |
| ROOTABLE | Yes |
| ANDROID VERSION | 11–14 depending on device |
| ADB | Yes |
| POKEMON GO | Yes |
| POKEMOD SUPPORT | Yes |
| COST RANGE | $80–200 |
| SETUP DIFFICULTY | Low |
| MAJOR DRAWBACK | Hardware variability; verify ARM64 and bootloader unlock before purchase |

### C. ARM64 Android Tablet

| Property | Value |
|---|---|
| NATIVE ARM64 | Yes (most) |
| ROOTABLE | Yes |
| ANDROID VERSION | 11–13 depending on device |
| ADB | Yes |
| POKEMON GO | Partial (many tablets lack GPS; POGO requires GPS) |
| POKEMOD SUPPORT | Yes (if GPS present) |
| COST RANGE | $80–180 |
| SETUP DIFFICULTY | Medium (GPS absence on many tablets) |
| MAJOR DRAWBACK | Many WiFi-only tablets lack GPS sensor, which POGO requires |

### D. Native ARM64 Android VM (ARM Host)

| Property | Value |
|---|---|
| NATIVE ARM64 | Yes (on ARM host only: Apple Silicon, Raspberry Pi) |
| ROOTABLE | Possible but complex |
| ANDROID VERSION | Depends on ROM |
| ADB | Yes (via network) |
| POKEMON GO | Uncertain (GPS emulation difficult on VM) |
| POKEMOD SUPPORT | Not documented; high risk |
| COST RANGE | $0–50 (if ARM host exists) |
| SETUP DIFFICULTY | High |
| MAJOR DRAWBACK | No GPS hardware passthrough on most VMs; unverified Pokemod compatibility |

### E. ARM-based Windows/macOS Android Environment

| Property | Value |
|---|---|
| NATIVE ARM64 | Yes (on Apple Silicon Mac via UTM/AVD, or Windows on ARM) |
| ROOTABLE | Complex (requires custom ARM AVD image + Magisk) |
| ANDROID VERSION | Varies |
| ADB | Yes |
| POKEMON GO | Uncertain (GPU, GPS, Play Integrity issues) |
| POKEMOD SUPPORT | Not documented; very high risk |
| COST RANGE | $0 (if ARM hardware exists) |
| SETUP DIFFICULTY | Very High |
| MAJOR DRAWBACK | No production-grade ARM Android VM solution; Play Integrity fails on most; GPS absent |

### Comparison Summary

| Option | ARM64 | Root | POGO | Pokemod | Cost | Difficulty |
|---|---|---|---|---|---|---|
| A. Spare phone | Yes | Yes | Yes | Yes | $0–150 | Low |
| B. Cheap used phone | Yes | Yes | Yes | Yes | $80–200 | Low |
| C. ARM64 tablet | Yes | Yes | Partial | Partial | $80–180 | Medium |
| D. ARM64 VM | Yes | Hard | Uncertain | High risk | $0–50 | High |
| E. ARM desktop env | Yes | Hard | Uncertain | Very high risk | $0 | Very High |

**Conclusion:** Options A and B are the only realistic choices. Physical ARM64 phone with native hardware GPS, root, and ADB is the correct path.

---

## PHASE 3 — Best Android Version

### Version Comparison

| Android Version | Root Tooling | Pokemod Compatibility | POGO Compatibility | Stability | Risk |
|---|---|---|---|---|---|
| Android 11 | Magisk v26+ stable | Good — well-tested with Zygisk | Yes (Android 9+ req) | Stable | Low |
| Android 12 | Magisk v26+ stable | Good — widely used for Pokemod | Yes | Stable | Low |
| **Android 13** | **Magisk v27+ stable** | **Good — modern + well-supported** | **Yes** | **Stable** | **Low** |
| Android 14 | Magisk v27+ supports | Moderate — newer, fewer tweaks tested | Yes | Stable | Low-Medium |
| Android 15 | Limited testing | **Unknown — not confirmed** | Yes | Uncertain | **High** |

### Analysis

- **Android 15**: No official Pokemod compatibility confirmation. Root tooling maturing but fewer modules tested. **Rejected.**
- **Android 14**: Functional but newer; fewer Pokemod-specific guides available. Viable backup.
- **Android 13**: Sweet spot. Magisk well-established, Zygisk stable, extensive Pokemod community guides exist, POGO runs natively, widely available devices. **RECOMMENDED.**
- **Android 12**: Slightly older but very well-supported. Good fallback.
- **Android 11**: Still functional but aging; fewer OTA updates available on budget devices.

### Decision

**BEST ANDROID VERSION: Android 13** (primary target)
**BACKUP: Android 12** (if Android 13 device unavailable)

Rationale: Android 13 is modern enough for current POGO versions, stable for Magisk/Zygisk root tooling, has the broadest community documentation for Pokemod setups, and is available on multiple affordable devices.

---

## PHASE 4 — Device Shortlist

### Device 1 (RECOMMENDED): Google Pixel 6a

| Property | Value |
|---|---|
| MODEL | Google Pixel 6a (GX7AS/GB62Z) |
| SOC | Google Tensor (GS101) — ARM64 |
| ARM64 | Yes (arm64-v8a native) |
| BOOTLOADER UNLOCK | Yes (after June 2022 OTA update; `fastboot flashing unlock`) |
| ANDROID VERSION OPTIONS | Android 12 → 13, 14, 15, 16 (OTA); LineageOS 20/21 (Android 13/14) |
| ROOT PRACTICALITY | Excellent — Pixel devices have the best root documentation; Magisk via init_boot/boot.img patch; XDA, GitHub, DroidWin guides abundant |
| USED PRICE RANGE | $100–170 |
| WHY IT FITS | Cheapest path to Android 13 on native ARM64 with excellent root docs, easy ADB, built-in GPS, Google-certified POGO compatibility, Pixel 6a bootloader unlock is well-documented (needs June 2022+ OTA first) |

### Device 2 (BUDGET): OnePlus 8T

| Property | Value |
|---|---|
| MODEL | OnePlus 8T (KS2020/dimorphous) |
| SOC | Snapdragon 865 (SM8250) — ARM64 |
| ARM64 | Yes (arm64-v8a native) |
| BOOTLOADER UNLOCK | Yes — immediate, no waiting period; `fastboot oem unlock` or `fastboot flashing unlock` |
| ANDROID VERSION OPTIONS | Android 11 (stock) → Android 12/13 via LineageOS 20/21 |
| ROOT PRACTICALITY | Excellent — OnePlus has the easiest bootloader unlock; extensive XDA TWRP + Magisk guides; one of the most rooted OnePlus models |
| USED PRICE RANGE | $90–140 |
| WHY IT FITS | Cheapest option, easiest bootloader unlock process, excellent root documentation, ARM64, can run Android 12/13 via LineageOS, built-in GPS |

### Device 3 (PREMIUM BUDGET): Google Pixel 7a

| Property | Value |
|---|---|
| MODEL | Google Pixel 7a (LY1N/lynx) |
| SOC | Google Tensor G2 (GS201) — ARM64 |
| ARM64 | Yes (arm64-v8a native) |
| BOOTLOADER UNLOCK | Yes (`fastboot flashing unlock`) |
| ANDROID VERSION OPTIONS | Android 13 (stock) → 14, 15, 16 (OTA); LineageOS 21/22 |
| ROOT PRACTICALITY | Excellent — same Pixel root documentation as 6a; better SOC; Android 13 native |
| USED PRICE RANGE | $150–250 |
| WHY IT FITS | Android 13 out of the box, modern SoC, excellent root docs, built-in GPS, best performance-to-cost ratio among Pixels |

### Device 4 (ALTERNATIVE): OnePlus 9

| Property | Value |
|---|---|
| MODEL | OnePlus 9 (KE2020/laurel) |
| SOC | Snapdragon 888 (SM8350) — ARM64 |
| ARM64 | Yes (arm64-v8a native) |
| BOOTLOADER UNLOCK | Yes — immediate, no waiting period |
| ANDROID VERSION OPTIONS | Android 11 (stock) → Android 12/13 via LineageOS 19/20 |
| ROOT PRACTICALITY | Excellent — same easy OnePlus unlock; good XDA docs |
| USED PRICE RANGE | $100–180 |
| WHY IT FITS | Newer SoC than 8T, easy unlock, can run Android 12/13 via custom ROMs, built-in GPS |

### Device 5 (ULTRA-BUDGET): OnePlus Nord 2

| Property | Value |
|---|---|
| MODEL | OnePlus Nord 2 (MT6893/racoon) |
| SOC | MediaTek Dimensity 1200-AI — ARM64 |
| ARM64 | Yes (arm64-v8a native) |
| BOOTLOADER UNLOCK | Yes (most variants) |
| ANDROID VERSION OPTIONS | Android 11 (stock) → Android 12 via OxygenOS; LineageOS 18/19 |
| ROOT PRACTICALITY | Good — MediaTek requires different Magisk approach but well-documented |
| USED PRICE RANGE | $70–120 |
| WHY IT FITS | Cheapest option overall, ARM64, unlockable, adequate for POGO and Pokemod on Android 12 |

### Device Selection Rationale

| Rank | Device | Price | Android 13 | Root Docs | GPS | Unlock |
|---|---|---|---|---|---|---|
| 1 | Pixel 6a | $100–170 | OTA / Custom | Excellent | Yes | Easy |
| 2 | OnePlus 8T | $90–140 | Custom (LineageOS) | Excellent | Yes | Easiest |
| 3 | Pixel 7a | $150–250 | Native | Excellent | Yes | Easy |
| 4 | OnePlus 9 | $100–180 | Custom (LineageOS) | Excellent | Yes | Easiest |
| 5 | Nord 2 | $70–120 | Custom (LineageOS) | Good | Yes | Easy |

---

## PHASE 5 — Migration Plan (MuMu → Native ARM64 Device)

### Pre-Migration Checklist

- [ ] Purchase/acquire selected ARM64 device
- [ ] Verify device is ARM64 (`adb shell getprop ro.product.cpu.abi` → should show `arm64-v8a`)
- [ ] Backup Pokemod account credentials (email, password, device auth token)
- [ ] Backup Pokémon GO login credentials (Google/ Pokemon Trainer Club)
- [ ] Write down ADB workflow details from MuMu setup (commands, scripts, paths)
- [ ] Note current Magisk version and Zygisk status from MuMu (for reference)

### Migration Steps

1. **Factory reset new device** (if used) — ensure clean Android installation
2. **Enable Developer Options**: Settings → About Phone → Tap Build Number 7 times
3. **Enable USB Debugging**: Settings → Developer Options → USB Debugging ON
4. **Enable OEM Unlocking**: Settings → Developer Options → OEM Unlocking ON (required for bootloader unlock)
5. **Connect to PC via USB**: `adb devices` — verify ADB detects device
6. **Unlock bootloader**: `adb reboot bootloader` → `fastboot flashing unlock` → confirm on device (wipes data)
7. **Re-enable USB Debugging** after reboot
8. **Flash Magisk**:
   - Download stock boot.img / init_boot.img matching device and current Android version
   - Patch with Magisk APK → `magisk_patched.img`
   - `adb reboot bootloader` → `fastboot flash boot magisk_patched.img` (or init_boot)
   - `fastboot reboot`
9. **Enable Zygisk**: Magisk app → Settings → Zygisk → Enable → Reboot
10. **Install Pokemod APK** (from pokemod.dev or official source)
11. **Install Pokémon GO** from Google Play Store
12. **Configure GPS Joystick** (if using mock location) — grant all permissions
13. **Verify root**: `adb shell su -c id` → should return `uid=0(root)`
14. **Launch Pokemod** → grant root permissions → verify service running
15. **Launch Pokémon GO** → verify normal operation with Pokemod overlay

### Do NOT Copy from MuMu

- [ ] Do NOT copy MuMu-specific patches or configurations
- [ ] Do NOT copy Houdini patches or translation libraries
- [ ] Do NOT copy emulator-only binaries or drivers
- [ ] Do NOT blindly copy /data from MuMu to new device
- [ ] Do NOT transfer emulator fingerprint or device properties

### Preserve

- [x] Pokémon GO account/login credentials
- [x] Pokemod account (email, auth token from atlas.pokemod.dev)
- [x] ADB workflow (same commands, different device serial)
- [x] Root verification steps (adb shell su)
- [x] Normal Android location services (GPS chip on device)

---

## PHASE 6 — Acceptance Test

Define the following verification tests after migration. These are pass/fail criteria only; troubleshooting is a separate phase.

1. **adb detects device**: `adb devices` shows the new device with serial number and `device` state
2. **arm64-v8a confirmed**: `adb shell getprop ro.product.cpu.abi` returns `arm64-v8a`
3. **root works**: `adb shell su -c id` returns `uid=0(root)` or Magisk app shows active
4. **Pokémon GO launches normally**: Game opens and loads to map without crash
5. **map/location works normally**: Map view renders with player position; GPS is accurate
6. **Pokémon spawn normally**: Wild Pokémon appear on map as expected
7. **Pokemod launches**: Pokemod app opens without error
8. **Pokemod service stays running**: Pokemod service indicator remains active for 5+ minutes
9. **Pokémon GO stays open after Pokemod starts**: No crash or forced close when Pokemod attaches
10. **overlay appears**: Pokemod overlay (e.g., Perfect Throw, Virtual GO Plus) renders on screen
