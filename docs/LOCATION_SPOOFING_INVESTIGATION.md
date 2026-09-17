# Pokemod Location Spoofing Investigation

Date: 2026-09-17
Status: Root cause identified, workaround needed

## Problem Statement

Pokemod injector crashes under Houdini x86_64→ARM64 translation, preventing location spoofing.
GPS Joystick sets mock coordinates but they're stale (1+ hours old), causing PGO to show
"Failed to detect location. (12)".

## Current State

- **PGO**: Running (pid 20819), ARM64 through Houdini, showing "Failed to detect location. (12)"
- **GPS Joystick**: Running (pid 9196), coordinates set to 41.874, -87.619 but timestamp is 1h+ old
- **Pokemod service**: Running (pid 10621), injector crashes immediately
- **Frida server**: Running (pid 15652, port 27042, v17.18.0)
- **Root**: Working (magisk:s0)
- **Mock location**: Enabled, GPS Joystick is the mock provider

## Key Findings

### 1. Pokemod Injector Crash (ARM64/Houdini Incompatibility)

- The injector is a 31.4MB ARM64 ELF binary (NDK r29, stripped)
- It crashes deterministically with SIGABRT ~1 second after launch under Houdini
- Crash chain: `abort() in libc → libhoudini.so → libhoudini.so`
- Houdini ARM backtrace shows 16 frames all in the injector (offsets 0x1b9bf64, 0x1ba5b1c, 0x1c9afe0)
- The injector contains ptrace, process_vm_writev, mprotect strings (Frida Floyd Linux backend)
- Strace confirms NO ptrace or process_vm_writev syscalls (0 of 4254 lines)
- The injector never accesses libNianticLabsPlugin.so or the PGO process
- Pokemod service catches this as "Command failed: 134" → "ShellFailed(1)" → shutdown
- See `docs/INJECTOR_CRASH_ANALYSIS.md` for full analysis

### 2. Frida Limitations

- Frida v17.18.0 can attach to processes and execute basic JavaScript
- Java.perform fails with "ReferenceError: 'Java' is not defined" in ALL apps (system-wide)
- Process.enumerateModules returns 0 modules in all tested processes
- This prevents hooking Java methods or enumerating native modules
- Frida spawn works (can spawn PGO and attach) but same limitations apply

### 3. GPS Joystick Location Issues

- Coordinates are set to 41.874, -87.619 (Chicago area) via broadcast intent (result=0)
- Location timestamp is 1+ hours old (not updated when coordinates change)
- Coordinates are stored in encrypted shared preferences (ASV7R3... prefix)
- `input tap` and `input text` commands don't properly interact with the coordinate field
- The GPS Joystick overlay service is running but not actively updating location
- PGO receives location updates but rejects them (error 12)

### 4. PGO Behavior

- PGO is a Unity app running as ARM64 through Houdini
- PGO registers for HIGH_ACCURACY location from GPS Joystick
- PGO has received 300+ locations but shows "Failed to detect location"
- PGO's native libraries (libunity.so, libil2cpp.so, libNianticLabsPlugin.so) are loaded
- Frida cannot enumerate these modules due to Java bridge limitation

## Root Cause Summary

There are TWO independent blockers preventing location spoofing:

1. **Pokemod Injector Crash**: The Pokemod injector (a Frida-based ARM64 binary) cannot run
under Houdini's x86_64→ARM64 translation. The injector needs ptrace/process_vm_writev to
attach to PGO and inject the main_agent, but these operations fail or are unsupported under
Houdini. Without the injector, Pokemod cannot intercept PGO's location verification.

2. **GPS Joystick Stale Provider**: GPS Joystick does NOT publish fresh location updates.
After a clean force-stop/restart, the location timestamp remains at et=+1h18m36s (unchanged
across 4+ minutes of testing). PGO receives hundreds of location updates but they all have
the same stale timestamp. PGO shows "Failed to detect location. (12)" because it rejects
stale locations.

Additionally, Frida's Java bridge doesn't work on this device/emulator, preventing alternative
injection approaches through Frida.

## Recommendations

### Immediate (Location Spoofing)

1. **Try a different GPS Joystick app** - Some apps actively push location updates
2. **Try setting coordinates through the app UI** - The coordinate field might need direct interaction
3. **Check if PGO accepts the mock location** - The error code 12 might be a different issue

## Latest Test Results (2026-09-17)

**PGTools package:** `net.pgtools.auto`
**Selected as mock app:** YES
**PGTools location service running:** YES (PID 29719)
**First et:** +1h18m36s902ms
**Second et (5s later):** +1h18m36s902ms (IDENTICAL)
**Location updating:** NO
**Altitude:** 4.18E7 meters (absurd - broken)
**Pokémon GO Error 12:** YES (expected, location stale)
**Next blocker:** PGTOOLS_STALE_PROVIDER

**Summary:** PGTools is installed and set as mock location app with location permissions granted (via appops), but it does NOT publish fresh location updates. The timestamp remains frozen at et=+1h18m36s902ms (1h18m stale). PGTools is a WebView-based app that appears to require UI interaction to start its location service, but no automated method was found to trigger it.

**Recommendation:** Both GPS Joystick and PGTools fail to provide fresh location updates on this MuMu emulator. Recommend:
1. Try a different mock location app (Fake GPS Location by Lexa, GPS Emulator)
2. Use an x86_64 emulator or physical ARM64 device
3. Investigate PGTools WebView JavaScript injection to trigger location service

## Files

- `docs/INJECTOR_CRASH_ANALYSIS.md` - Detailed injector crash analysis
- `artifacts/frida-logs/logcat.txt` - Full logcat (55277 lines)
- `artifacts/injector_strace.txt` - Strace of injector run (4254 lines)
- `artifacts/frida-inject.py` - Frida injection script (attempts)
- `artifacts/frida-*.py` - Various Frida test scripts
