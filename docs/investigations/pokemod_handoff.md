# Pokemod / MuMu — Investigation Handoff

## Status: STAGE 3 COMPLETE — ARM64 Device Selected, Migration Planned

## Summary

MuMu x86_64 environment is incompatible with Pokemod due to ARM64 injector/SIGABRT under Houdini translation.

**Solution selected**: Native ARM64 physical Android device (Google Pixel 6a as primary target).

## Key Findings

- Pokemod requires rooted physical ARM64 device (OFFICIAL)
- No emulator support — x86_64/Houdini path is unsupported
- Zygisk requires native ARM64; cannot work under emulation
- Android 13 identified as best version (root tooling + POGO + Pokemod compatibility)
- Pixel 6a selected: ~$100-170 used, Android 13, excellent root documentation, built-in GPS

## Device Shortlist

| Priority | Device | Price | Android |
|---|---|---|---|
| 1 | Google Pixel 6a | $100–170 | 12→13 |
| 2 | OnePlus 8T | $90–140 | 11→12/13 |
| 3 | Google Pixel 7a | $150–250 | 13 native |

## Migration Status

- [x] Environment research complete
- [x] Device shortlist defined
- [x] Migration checklist defined
- [x] Acceptance test criteria defined
- [ ] Hardware acquired — PENDING
- [ ] Migration executed — PENDING
- [ ] Acceptance test run — PENDING

## Next Step

Acquire selected ARM64 device → Execute migration checklist → Run acceptance test
