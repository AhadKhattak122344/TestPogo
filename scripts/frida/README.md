# Pokemod Automation Scripts

This directory contains automation scripts for Pokemod workflow.

## Usage

### Run Full Workflow
```bash
python scripts/frida/run_automation.py --workflow --bin-dir /path/to/bin --output report.json
```

### Check Binaries Only
```bash
python scripts/frida/run_automation.py --check-only --bin-dir /path/to/bin
```

### Setup Frida Server Only
```bash
python scripts/frida/run_automation.py --bin-dir /path/to/bin
```

### With Custom Frida Script
```bash
python scripts/frida/run_automation.py --workflow --script /path/to/custom_hook.js
```

## Options

- `--serial`: ADB device serial (auto-detects if not specified)
- `--bin-dir`: Directory containing binaries (Atlas.apk, Pokemod-Zygisk.zip, etc.)
- `--scripts-dir`: Directory containing Frida scripts
- `--script`: Specific Frida script to run
- `--output`: Save JSON report to this path
- `--workflow`: Run full automation workflow
- `--check-only`: Only check for binaries and status

## Required Binaries

Place these files in the `bin/` directory:

- `Atlas.apk` - Pokemod Atlas controller APK
- `Pokemod-Zygisk.zip` - Zygisk module for injection
- `frida-server-*` - Will be auto-downloaded if missing

## Frida Scripts

Default hook script: `scripts/frida/default_hook.js`

This script hooks:
- Activity lifecycle
- Location services
- Unity player initialization
- Network clients (SSL pinning detection)
- Native method registration
