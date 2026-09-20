# Pokemod / MuMu ABI Compatibility — Stage 2

## Environment

| Property | Value |
|---|---|
| MuMu Player | 6.7.1.0 |
| Android | 15 / API 35 |
| Host ABI | x86_64 |
| Pokémon GO | 0.429.1 (com.nianticlabs.pokemongo) |
| Pokemod | 13.3.3 (com.pokemod.app.public) |
| Root | Magisk 30.7 + Zygisk Next 1.5.0 |

## ABI Matrix

| Component | ABI |
|---|---|
| MuMu userspace | x86_64 |
| Pokémon GO primaryCpuAbi | arm64-v8a |
| Pokémon GO installed native libs | arm64-v8a (lib/arm64) |
| Pokemod outer injector | arm64-v8a (ELF64, e_machine=0xb7) |
| Pokemod package primaryCpuAbi | x86_64 |
| Pokemod installed native libs | x86_64 (lib/x86_64: libconceal.so, libfancier.so) |
| Pokemod main payload (~24 MB) | arm64-v8a |
| Pokemod x86_64 stub | ~6 KB loader only |

## Translation Layer

- ARM64 ELF binaries are routed via binfmt_misc to `/system/bin/houdini64`.
- `ro.dalvik.vm.native.bridge=libnb.so`
- `ro.dalvik.vm.isa.arm64=x86_64`
- `/system/lib64/libhoudini.so` present (9.7 MB)

## Crash

- `pokemod-injector` (ARM64) runs under houdini64.
- SIGABRT (signal 6), exit code 134.
- Top frames: abort() -> libhoudini.so -> libhoudini.so
- Pokemod detects failure, reports ShellFailed, closes Pokémon GO.

## Compatibility Research

- Pokemod official docs: rooted Android required; no emulator support stated.
- Third-party documentation explicitly: "Pokemod doesn't work in emulators, cloned or modified PoGO apps."
- No official Android 15 or MuMu compatibility confirmation found.
- No official x86_64 / Houdini support documented.
- Community evidence: Houdini native-bridge environments break ARM injection tooling (Frida, Zygisk modules, inline hooks) due to TLS isolation and translation-cache issues.

## Conclusion

Pokemod's ARM64 injection workflow is incompatible with the current MuMu x86_64 / Houdini environment. Pokemod provides no full-size x86_64 injection payload; the ~6 KB x86_64 ELF embedded in the injector is a loader/stub only. No supported fix exists within this environment.

## Supported Fix

Use a native ARM64 Android environment (physical device or ARM emulator) that Pokemod supports. Do not patch Pokemod, Pokémon GO, or Houdini.