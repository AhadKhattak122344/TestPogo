# Current Context

Last updated: 2026-09-15

Latest user direction: stop repeating Google/Pixel API permutations; find and install another runtime, then install Magisk and run MuMu. All default fleet cases are disabled. MuMuPlayer 6.7.1.0 Android15 instance0 is now running at ADB 127.0.0.1:16384. Magisk v30.7 app is installed; full Magisk root installation has not been completed.

Follow-up: user cannot complete either Install action in Magisk. MuMu officially
lists Magisk as unsupported on its Android15 runtime (F07). Local root permission
is false and system disk readonly true. Do not retry the APK or patch a guessed
image. Root access versus specifically Magisk/modules was asked; configuration
and boot images remain unchanged pending the required direction.
Read docs/PROJECT_MAP.md for the organized layout and preserved Android/game
reference. Generated .tmp, root egg-info and misplaced experiments/config files
are retained under artifacts/_archive/cleanup-20260914, with 969 file hashes in
artifacts/repo-cleanup-20260914/move-manifest.json. No logs/components were deleted.
Fleet path/Java-launcher/profile defects are fixed. Run-FleetTests.ps1 implements
a sequential create/boot/display/install/observe/stop pass with per-case evidence.
The completed F02 sweep passed process/PNG checks for API35 and API36 on game
0.427.0. API35 showed birth-date setup; API36 initially showed splash. API37's
accepted swangle/DMA/Vulkan controls still fail display with the same assertion;
the case remains in config with enabled=false. F03 ran API36 alone for 120 seconds
and exited1: 10 valid PNGs from 11 attempts preceded ADB offline; sample08 showed
Google's blank Email/phone screen. Authentication/map remain unverified and crash
absence cannot be claimed. F04 API35 headless support was added but cancelled and
not run. No account credentials or birth date were supplied. The official MuMuPlayer
installer is downloaded with provenance evidence under
`artifacts/runtime-switch-20260915/`. MuMu installation and Android boot are now
verified. The latest PNG shows Magisk's boot-image picker; no image was selected
or patched by the agent. Game installation/login on MuMu remain unverified.

The active project is the `android-cloud-lab` CLI, not a FastAPI service. The
repo already contains a cautious Proxmox planner/deployer, diagnostics, observer,
root controls, location helpers, and Pokemon GO experiment harness.

Current verified baseline:

- Native API36 AVD `poke_api36_test` boots and launches Pokemon GO.
- Pokemon GO login remains unresolved on the emulator with the designated account.
- API36.1 display stability failed.
- API37 auto/host boot failed. Software GPU and software with GLDirectMem disabled
  both reached the boot marker but failed display capture with SurfaceFlinger
  SIGABRT (L23/L24). Guest stopped; no API37 login attempted.
- Proxmox is plan/preflight/deploy code with mocked tests and no live host proof.

Before suggesting a path, run:

```powershell
uv run python tools/validate_against_history.py "short suggestion text"
```

Then read the matched source entry before recommending or executing anything.
