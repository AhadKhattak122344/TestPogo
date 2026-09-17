# Pokemod Injector Crash Analysis

Date: 2026-09-17
Status: Root cause identified — ARM64/Houdini compatibility issue

## Summary

The Pokemod injector (`pokemod-injector`) crashes deterministically with SIGABRT
~1 second after launch when running under Houdini x86_64→ARM64 translation on
the MuMu API 37 emulator. The Pokemod HALService catches this as
`Command failed: 134` → `ShellFailed(1)` and initiates full shutdown.

## Crash Chain

```
Pokemod HALService (pid 24061, uid 10065)
  └─ execve("/system/bin/houdini64", ["houdini64", "pokemod-injector", ...])
       └─ pokemod-injector (ARM64 ELF, 31.4MB, NDK r29, stripped)
            └─ ~1s execution under Houdini translation
                 └─ abort() called from injector code
                      └─ SIGABRT (signal 6, exit code 134)
                           └─ HALService: "Command failed: 134"
                                └─ "ShellFailed(1)"
                                     └─ Injector closed → Service shutdown
```

## Evidence

### 1. Deterministic crash pattern (5+ identical attempts)

All crashes share identical characteristics:
- Same Houdini debug backtrace offsets: `#13 0x1b9bf64`, `#14 0x1ba5b1c`, `#15 0x1c9afe0`
- Same native backtrace: `abort+196` in libc → `libhoudini.so` → `libhoudini.so`
- Same process uptime: ~1 second
- Same exit code: 134 (SIGABRT)
- Different PIDs and ports across attempts (confirms not a resource conflict)

### 2. Native crash dump (tombstone_04, 43883 bytes)

**Process**: `/system/bin/houdini64` (pid 13082, uid 0)
**Signal**: SIGABRT, code -1 (SI_QUEUE)
**ABI**: x86_64 (running under Houdini translation)

**Native backtrace** (3 frames):
```
#00 pc 0000000000057864  /apex/com.android.runtime/lib64/bionic/libc.so (abort+196)
#01 pc 0000000000524613  /system/lib64/libhoudini.so
#02 pc 0000000000318421  /system/lib64/libhoudini.so
```

**Houdini ARM backtrace** (16 frames, all in injector):
```
#00  pc 0x1bdaff0  /data/.../injector/pokemod-injector
#01  pc 0x1bdb378  /data/.../injector/pokemod-injector
#02  pc 0x1be6098  /data/.../injector/pokemod-injector
#03  pc 0x1be2240  /data/.../injector/pokemod-injector
#04  pc 0x1be1cd8  /data/.../injector/pokemod-injector
#05  pc 0x1be1dd4  /data/.../injector/pokemod-injector
#06  pc 0x1be2ca0  /data/.../injector/pokemod-injector
#07  pc 0x1cb11f0  /data/.../injector/pokemod-injector
#08  pc 0x1be2c6c  /data/.../injector/pokemod-injector
#09  pc 0x1bad06c  /data/.../injector/pokemod-injector
#10  pc 0x1c805b0  /data/.../injector/pokemod-injector
#11  pc 0x1c78140  /data/.../injector/pokemod-injector
#12  pc 0x1c77d20  /data/.../injector/pokemod-injector
#13  pc 0x1b9bf64  /data/.../injector/pokemod-injector
#14  pc 0x1ba5b1c  /data/.../injector/pokemod-injector
#15  pc 0x1c9afe0  /data/.../injector/pokemod-injector
```

### 3. Injector binary properties

- **Architecture**: ARM64 (AArch64), ELF64, little-endian
- **Size**: 31.4MB (32,965,160 bytes)
- **Build**: Android 21 (API 21), NDK r29 (14206865), stripped
- **Type**: DYN (Shared object), Entry point: 0x467000
- **Dependencies**: libm.so, libdl.so, libc.so
- **Key strings found**: `ptrace`, `process_vm_writev`, `mprotect`,
  `FloydLinuxHelperBackendInjectTask`, `Floyd.InjectSession.rejuvenate`,
  `Remote mprotect failed`, `process_vm_writev failed`, `init fail`,
  `Unsupported ELF EI_DATA`, `assertion failed: WITHIN_ARENA(ptr)`

### 4. Pokemod service response (logcat lines 50007-50019)

```
[PKMD ERROR]: Aborted
[PKMD INFO]: [MAIN INJECTION] [-] Command failed: 134
[PKMD ERROR]: main failed with code 1
[PKMD DEBUG]: Closing Injector. Reason: ShellFailed(1)
[HALService]: Injector closed. Reason: ShellFailed(1)
[HALService]: Performing complete shutdown. Reason: Injector Closed (ShellFailed(1))
[HALService]: Step 1: Closing injector...
[HALService]: Step 2: Killing game and injector...
```

### 5. Strace analysis (4254 lines captured)

Main thread (pid 13811) under strace:
- **No ptrace syscall** visible (0 matches) — despite `ptrace` in binary strings
- **No process_vm_writev** syscall visible
- **No libNianticLabsPlugin.so** file open — injector never accesses the target library
- **No PGO process interaction** — no openat/stat on PGO-related paths
- **Repeated mprotect** on same address (0x7587fe585000) — Frida agent memory management
- **Exit**: `exit_group(4)` — clean exit with code 4 (different from SIGABRT crash)

This indicates the injector never reaches its injection logic under strace.
Under normal execution (without strace), it crashes with SIGABRT before or during
the injection attempt.

### 6. Empty Pokemod tombstone

`/data/tombstones/app/com.pokemod.app.public/10065.log` is 0 bytes.
The Pokemod service does not generate a native crash dump because it exits
gracefully (not via signal) after the injector fails.

## Root Cause Assessment

**Primary hypothesis**: The Pokemod injector is a Frida-based Linux injection
engine (Floyd) that requires ptrace, process_vm_writev, and mprotect to attach
to and inject code into the target process (libNianticLabsPlugin.so in PGO).
When running under Houdini x86_64→ARM64 translation, these operations are
unsupported or fail, causing the injector to call abort().

**Supporting evidence**:
1. The injector contains ptrace/process_vm_writev/mprotect in its strings
2. No ptrace or process_vm_writev syscalls appear in strace (hidden by Houdini or never reached)
3. The injector never accesses libNianticLabsPlugin.so or the PGO process
4. The crash is deterministic (same code path, same failure)
5. The abort originates from within the injector code (Houdini backtrace #13-#15)
6. The crash goes through Houdini's translation layer (libhoudini.so in native backtrace)
7. The injector exits in ~1 second (enough time for initialization, not for full injection)

**Alternative hypotheses** (less likely):
- The injector detects it's running in a translated environment and deliberately aborts
- The injector's initialization fails due to missing dependencies or incorrect configuration
- The injector's agent (main_agent) is incompatible with the current PGO version

## Injection Configuration

From the injector command line:
```
houdini64 pokemod-injector pokemod-injector \
  -p 26917 \
  -s /data/user/0/com.pokemod.app.public/files/agents/main_agent \
  -R v8 \
  -P {"uuid":"...","refreshToken":"...","apiBaseUrl":"https://discovery.pokemod.dev/hal/",
      "recoveryMode":false,"injectionType":"attach",
      "targetLibrary":"libNianticLabsPlugin.so",
      "signals":{...}}
```

- **Injection type**: attach (attach to running process, not spawn)
- **Target library**: libNianticLabsPlugin.so (PGO's native ARM64 library)
- **Agent**: main_agent (2.1MB file)
- **Port**: 26917 (varies per attempt)

## Files

- `artifacts/frida-logs/logcat.txt` — Full logcat (55277 lines)
- `artifacts/injector_strace.txt` — Strace of injector run (4254 lines)
- `artifacts/frida-logs/frida-output.txt` — Frida session output
- `docs/ROOT_MAGISK_WORKING.md` — Root setup procedure
- `docs/INJECTOR_CRASH_ANALYSIS.md` — This document

## Next Steps

1. **Try native x86_64 injector** — If Pokemod provides an x86_64 variant, it would
   bypass Houdini entirely
2. **Check with Pokemod developers** — Confirm whether Houdini translation is supported
3. **Try Frida directly** — Attach frida-server to PGO without the Pokemod injector
4. **Check Houdini capabilities** — Verify if Houdini supports ptrace on translated processes
5. **Alternative injection** — Use Frida's own Linux tools instead of Pokemod's Floyd backend
6. **Try without Houdini** — If PGO can run natively (x86_64), the injector might work
   without translation (but PGO requires ARM64)
