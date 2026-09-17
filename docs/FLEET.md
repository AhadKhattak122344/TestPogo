# Windows fleet tests

September15 status: all default fleet entries are disabled after the user stopped
repeated Google emulator permutations. API35 reached birth-date setup. API36's
longer observation reached Google sign-in, then ADB went offline; authentication
remains unverified. API37 still fails display capture. Configurations, AVD data
and logs are preserved. The next test should use a different Android platform.

Run from the repository root in PowerShell. The fleet scripts live in
`tools/windows/`; the shared helper is dot-sourced by the other scripts.
The device matrix is `config/fleet-matrix.json`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/windows/Run-FleetTests.ps1
```

The command above currently exits before any device operation because no default
case is enabled. The commands below document the retained interfaces; a separate
matrix with enabled entries is required for a future justified experiment.

The runner tests each enabled AVD sequentially, using the existing APK set in
`artifacts/pgo-apk`. It continues to the next case after a failure, stops only
name-matched AVDs it launched, verifies serial disappearance, and returns exit1
if any case fails. Each case has its own boot/game report, command, output and
exit-code files under `artifacts/fleet-sweep-<timestamp>/`. A successful command
without a matching game report cannot pass. Login is a separate acceptance step.

Use `-Only fleet_api35_pixel8` or `-Only fleet_api36_pixel9` for a single case,
`-ObserveSeconds 120` for a longer observation, `-Headless` to pass `-no-window`
to the emulator, and `-DryRun` to preview selection without device operations.
Existing images are reused; `-InstallImages` permits missing image downloads.
The runner's `-Matrix` accepts a separate test matrix without changing the default.
Headless forwarding passed host checks; the planned live API35 headless test was
cancelled without running when the user redirected testing to another platform.

For individual stages or an interactive emulator that stays open:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/windows/New-FleetAvds.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/windows/Start-Fleet.ps1 -Only fleet_api36_pixel9
powershell -NoProfile -ExecutionPolicy Bypass -File tools/windows/Install-FleetGame.ps1 -ApkDir artifacts/pgo-apk
powershell -NoProfile -ExecutionPolicy Bypass -File tools/windows/Stop-Fleet.ps1
```

`artifacts/pgo-apk` is this checkout's existing APK set. On another checkout,
supply a folder containing the official base APK and matching splits, or use
`-PullFromSerial emulator-5556` with the original API36 AVD running. Pulling copies
installed APK files; it does not transfer Google accounts or app data.

The default SDK/JDK and Android user directory are project-local under `.tools`.
Use `-SdkRoot`, `-JavaHome`, and `-AvdHome` to override them. API35 needs an official
system-image download if absent; API36/API37 were already installed here.
`-SkipInstall` skips downloads. Existing AVDs are preserved unless `-Force` is
explicitly supplied; the original named baseline AVDs are protected.

The matrix retains disabled API35/5562, API36/5564, API37/5566 and API33/5568
reference cases. All currently created fleet AVDs use
the SDK's available Pixel7 hardware profile; inventory names containing pixel8/9
were retained for continuity. `-Only <name>` selects one enabled
entry. `MaxParallel` controls the number started in each batch; successful AVDs
remain running, so it is not a total memory/concurrency limit.

Startup records boot completion, AVD identity, properties, crash logs, Google
package evidence, and a PNG. A boot marker alone does not pass display readiness.
Failed AVDs are stopped by default; `-KeepOnFailure` retains them for diagnosis.
Game testing consumes only name-matched devices with `display_ok` in the startup
summary, installs/launches once, and records process/window/screenshot/crash
evidence. `process_running` is not confirmed foreground UI or successful login.
Authentication stays unverified until separately observed.

Logs and per-device results are in timestamped `artifacts/fleet-*` directories.
Latest standalone summaries: `artifacts/fleet-latest.json` and
`artifacts/fleet-game-latest.json`; automatic runs also write
`artifacts/fleet-sweep-latest.json`. A failed startup/game result gives exit 1;
inspect the summaries because other devices may still have passed.

Run host checks with `Test-Fleet.ps1`, `Test-FleetRunner.ps1`, `Test-Profiles.ps1`, the full Python test
suite, and `tools/verify_repository.py`. Host tests do not prove guest compatibility.
Fresh runtime findings belong in `experiments/EXPERIMENT_LOG.md` and `docs/STATE.md`.

The original misplaced files and the pasted source were preserved under
`artifacts/fleet-input-20260914-180404/` before restoring the canonical paths.
