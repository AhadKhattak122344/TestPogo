# Pokemod Automation Framework

## Implementation Status

### COMPLETED ✓

1. **Frida Manager** (`android_lab/frida_manager.py`)
   - Auto-downloads Frida server for device architecture
   - Pushes and starts Frida server on device
   - Status monitoring (PID, port, architecture)
   - Script execution (launch with app or attach to running)

2. **Automation Orchestrator** (`android_lab/automation.py`)
   - Binary discovery and validation
   - Atlas APK deployment
   - Service management via `am` commands
   - Pokémon GO launch with Frida injection
   - Comprehensive result reporting

3. **CLI Runner** (`scripts/frida/run_automation.py`)
   - Full workflow execution
   - Check-only mode
   - Custom script support
   - JSON report generation

4. **Default Hook Script** (`scripts/frida/default_hook.js`)
   - Activity lifecycle hooks
   - Location service monitoring
   - Unity player detection
   - SSL pinning detection
   - Native method registration logging

### TESTED ✓

- All Python modules compile successfully
- All 37 unit tests pass
- CLI help command works
- Import validation passes

### REQUIRES MANUAL TESTING

The following require a running Android emulator/device with MuMu:

1. **Frida Server Deployment**
   - Requires rooted device/emulator
   - Needs network connectivity for download

2. **Atlas APK Installation**
   - Requires `bin/Atlas.apk` (proprietary, not included)
   - Device must have package installer working

3. **Service Start**
   - Requires Atlas APK to be installed first
   - Service class names may need verification

4. **Pokémon GO Injection**
   - Requires `com.nianticlabs.pokemongo` installed
   - Requires valid Frida script for specific game version
   - Game anti-cheat may block injection

## Quick Start

```bash
# 1. Place binaries in bin/
#    - Atlas.apk (from official Pokemod distribution)
#    - Pokemod-Zygisk.zip (from official distribution)

# 2. Check what's available
python scripts/frida/run_automation.py --check-only --bin-dir ./bin

# 3. Run full workflow (requires device connected)
python scripts/frida/run_automation.py --workflow --bin-dir ./bin --output report.json
```

## Architecture

```
Host (Python)                    Device (Android)
────────────                     ────────────────
┌──────────────────┐             
│ PokemodAutomation│             
│  ├─ check_binaries()           ┌─────────────────┐
│  ├─ deploy_atlas()    ───────► │ Atlas.apk       │
│  ├─ start_service()   ───────► │ MappingService  │
│  └─ launch_pogo()             │                 │
└────────┬─────────┘            │  Pokémon GO     │
         │                      └────────┬────────┘
         │ ADB                           │
         ▼                               │
┌──────────────────┐                     │
│  FridaManager    │                     │
│  ├─ ensure_server() ─────────────────►│ frida-server  
│  ├─ run_script()  ───────────────────►│ injected hooks
│  └─ get_status()  ◄───────────────────│ process info
└──────────────────┘                     
```

## Missing Components (Proprietary)

These components are NOT included in this repository and must be obtained from official Pokemod distribution:

1. **Atlas.apk** - The main controller application
2. **Pokemod-Zygisk.zip** - Zygisk injection module
3. **Game-specific Frida scripts** - Version-dependent hooks for IL2CPP functions

## Next Steps for Manual Testing

1. Obtain `Atlas.apk` and place in `bin/`
2. Start MuMu emulator with root enabled
3. Ensure ADB can connect: `adb devices`
4. Run: `python scripts/frida/run_automation.py --check-only`
5. If binaries found, run: `python scripts/frida/run_automation.py --workflow`
6. Review `report.json` for detailed results
