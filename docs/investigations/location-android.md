# Android location/mock-provider lifecycle investigation

Reported: 2026-09-18
Worktree: `C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.kilo\worktrees\even-dogwood`
Branch: `location-android-4`

## Scope and environment

This investigation covered only Android location-provider and mock-provider lifecycle behavior for Pokémon GO Error 12. It did not test root, Magisk, Pokemod, Frida, Play Integrity, identity masking, concealment, or anti-cheat bypasses.

- ADB: `C:\Users\ahadk\Downloads\Pokemod_Qwen\Pokemon_Go_Bot\.tools\android-sdk\platform-tools\adb.exe`
- Device: MuMu `emulator-5554`
- Android: 15/API 35, `x86_64,arm64-v8a,x86`
- Location setting: enabled
- Packages observed: `com.locationchanger` and prior `com.theappninjas.fakegpsjoystick`
- Target symptom: Pokémon GO Error 12, which was not retested as a game-login or anti-cheat result in this pass

The controlled reproduction below used Android shell UID 2000 to create test providers. Those entries exercise the same LocationManager provider registry lifecycle as an app-owned test provider, but they are not proof that Location Changer itself created them. A prior handoff separately reported `identity=10068/com.locationchanger`; that remains a prior observation, not a result reproduced in this pass.

## Current state

A clean baseline showed no `[mock]` provider tags:

- GPS: `identity=1000/android[GnssService]`
- Network: `identity=10025/com.google.android.gms[network_location_provider]`
- Fused: `identity=10025/com.google.android.gms[fused_location_provider]`
- Passive provider: `identity=1000/android[LocationService]`

After the cleanup and reboot checks, the same normal identities were restored. No GPS or network `[mock]` entry remained. Location Changer was re-enabled and launched with its mock-location app-op allowed; the provider dump still showed normal GPS/network/fused identities rather than a test-provider identity.

`settings get secure mock_location_app` was blank in the clean state. The Pokémon GO Error 12 result was not repeated after the reset, so this report does not claim that location cleanup resolves the game error.

## Tests performed

### 1. Reproduce a mock-provider entry

**BEFORE**

- GPS, network, and fused had normal identities.
- Shell UID 2000 had `MOCK_LOCATION: deny`.
- No test-provider entries were present.

**ACTION**

```text
adb shell appops set 2000 android:mock_location allow
adb shell cmd location providers add-test-provider gps --requiresSatellite --supportsAltitude --supportsSpeed --supportsBearing --powerRequirement 2
adb shell cmd location providers add-test-provider network --requiresNetwork --supportsAltitude --supportsSpeed --supportsBearing --powerRequirement 1
```

The command is nested under `providers`; `cmd location add-test-provider` returns `Unknown command: add-test-provider`. Numeric power requirements were required: `2` and `1` worked, while `HIGH` and `MEDIUM` produced `NumberFormatException`.

**AFTER**

- `gps provider [mock]`
- `network provider [mock]`
- Both reported `identity=2000/android[LocationService]`
- Event log contained `gps provider added mock provider override` and `network provider added mock provider override`
- Fused remained `10025/com.google.android.gms[fused_location_provider]` and was not tagged `[mock]`

**CONCLUSION**

The shell can create persistent LocationManager test-provider overrides after receiving the mock-location app-op. The `[mock]` state belongs to the provider registry and is independent of the package that may have originally registered it.

### 2. Disable Location Changer without removing providers

**BEFORE**

- Shell-owned GPS and network test providers were present and tagged `[mock]`.
- Location Changer was running.
- `settings get secure mock_location_app` was blank.

**ACTION**

```text
adb shell pm disable-user --user 0 com.locationchanger
adb shell pidof com.locationchanger
```

**AFTER**

- `pm disable-user` reported `Package com.locationchanger new state: disabled-user`.
- `pidof com.locationchanger` returned no PID.
- GPS and network remained `[mock]` with `identity=2000/android[LocationService]`.
- Fused remained normal and non-mock.

**CONCLUSION**

Disabling the package and terminating its process do not remove test-provider entries. Provider cleanup must be explicit; package lifecycle alone is insufficient.

### 3. Remove the test providers explicitly

**BEFORE**

- GPS and network were shell-owned `[mock]` providers.

**ACTION**

```text
adb shell cmd location providers remove-test-provider gps
adb shell cmd location providers remove-test-provider network
```

**AFTER**

- GPS returned to `identity=1000/android[GnssService]`.
- Network returned to `identity=10025/com.google.android.gms[network_location_provider]`.
- Fused remained `identity=10025/com.google.android.gms[fused_location_provider]`.
- No `[mock]` tags or test-provider last-location entries remained.

**CONCLUSION**

`remove-test-provider` is the minimum immediate cleanup for a known provider name. It removes the registry entry without requiring an app restart or guest reboot.

### 4. Reboot with a lingering test provider

**BEFORE**

- Shell-owned GPS and network providers were present and tagged `[mock]`.
- Event log contained the mock-provider override entries.

**ACTION**

```text
adb reboot
```

The device was allowed to complete boot; `getprop sys.boot_completed` returned `1`.

**AFTER**

- Immediately after boot, LocationManager initially exposed only the passive provider while Google location services initialized.
- After Google location services were available, GPS, network, and fused returned to their normal identities listed in `CURRENT STATE`.
- No `[mock]` tags or shell test-provider identities remained.

**CONCLUSION**

A full MuMu reboot clears lingering test-provider overrides. It is a broad reset, not the minimum cleanup when the provider names are known.

### 5. Observe fused-provider behavior after the mock registration ends

**BEFORE**

- A Location Changer registration had ended or the shell-owned test providers had been removed.
- Fused still retained its last reported location.

**ACTION**

Inspected `dumpsys location` and the provider identities after the registration ended and after explicit provider removal.

**AFTER**

- Fused remained owned by `10025/com.google.android.gms[fused_location_provider]`.
- Its last-location value could remain cached after the source registration ended.
- It did not change to the old mock-provider identity or continue showing a `[mock]` tag.

**CONCLUSION**

Fused does not remain backed by the old mock provider after the mock registration stops. A retained last location is provider-local cache/state and should not be confused with continued mock-provider ownership.

### 6. Relaunch Location Changer after cleanup

**BEFORE**

- Providers were in the normal clean state.
- Location Changer had been disabled by the lifecycle test.

**ACTION**

- Re-enabled and launched `com.locationchanger`.
- Granted its `android:mock_location` app-op and observed its GPS request.

**AFTER**

- GPS, network, and fused retained normal identities.
- No new `[mock]` entry appeared in this controlled run.
- The app requested GPS high-accuracy updates, while fused remained a separate Google provider.

**CONCLUSION**

On this MuMu/API 35 build, the controlled Location Changer launch did not expose a test-provider entry. This does not invalidate the earlier handoff observation of `identity=10068/com.locationchanger`; it shows that provider ownership must be verified per build and registration path.

## Proven facts

1. Android test providers are represented in the LocationManager provider registry and can outlive the creating process.
2. The shell command `cmd location providers remove-test-provider <name>` removes a known test provider immediately.
3. The application API for the same cleanup is `LocationManager.removeTestProvider(String provider)`.
4. Disabling or force-stopping a mock-location package does not, by itself, remove a registered test provider.
5. Selecting mock app `None` is a setting change, not a provider-removal operation. A prior handoff observed that force-stop plus `None` did not clear the app-owned lingering provider state; that specific sequence was not repeated in this pass.
6. A full reboot clears lingering overrides on this MuMu/API 35 guest.
7. Fused is a separate Google provider. It can retain a last location after another registration ends, but it does not remain owned by the old mock provider.
8. The controlled shell reproduction and the earlier `com.locationchanger` identity observation are different evidence sources and must not be conflated.

## What clears the lingering test provider

- Call `LocationManager.removeTestProvider(providerName)` for every provider name that the app added, in the app's stop/cleanup path or a `finally` block.
- From an ADB shell, run `cmd location providers remove-test-provider <providerName>` for each known name.
- Reboot the guest when the provider names or owner are unknown, or when a stale registry state must be reset broadly.

Android documentation and source evidence:

- API reference: https://developer.android.com/reference/android/location/LocationManager.html
- AOSP `LocationManager` implementation: https://android.googlesource.com/platform/frameworks/base/+/d46d308/location/java/android/location/LocationManager.java
- AOSP `LocationManagerService`: https://android.googlesource.com/platform/frameworks/base/+/master/services/core/java/com/android/server/location/LocationManagerService.java

CTS removes leftover test providers after aborted runs, which supports treating explicit removal as the normal cleanup operation.

## What does not clear it

- Disabling `com.locationchanger` with `pm disable-user`.
- Killing or force-stopping the mock-location package.
- Selecting mock app `None` without removing the provider.
- Stopping the app's location updates while leaving its registered test provider in the registry.
- Waiting for fused to update; fused is a separate provider and may retain a cached last location.

## Minimum clean reset procedure

For an app that owns the provider names:

1. Stop its location updates and listeners.
2. Call `LocationManager.removeTestProvider(name)` for every provider it added.
3. Verify with `adb shell cmd location providers` that no `[mock]` entry remains.
4. If ownership or names are unknown, remove each discovered test-provider name; otherwise perform a full guest reboot.

For this shell reproduction, the complete immediate reset was:

```text
adb shell cmd location providers remove-test-provider gps
adb shell cmd location providers remove-test-provider network
```

Clearing `settings secure mock_location_app` or changing the app-op can reset selection and permissions, but neither operation is a substitute for removing the provider registry entry.

## Remaining unknowns

- The earlier app-owned `identity=10068/com.locationchanger` state was not reproduced in this continuation.
- Location Changer's actual stop implementation was not available in the repository, so it is not verified whether it calls `removeTestProvider` for every provider it adds.
- The exact provider names used by every mock-location build are unknown; cleanup must enumerate or otherwise discover them.
- Pokémon GO Error 12 was not retested after cleanup, so causation remains unverified.
- Root, Magisk, Play Integrity, and concealment behavior remain intentionally out of scope.
