# Current Repository Architecture

## Overview

This repository provides **host-side tooling** for managing PogoMod deployments. It does NOT contain the proprietary injection modules or Atlas APK source code.

## Active Components

### 1. Python Package (`android_lab/`)

Core library providing:
- **ADB Communication**: Device discovery, shell commands, file transfer
- **Root Detection**: Magisk/root status verification  
- **Configuration Management**: YAML-based settings
- **CLI Interface**: Command-line entry points
- **Health Monitoring**: Device state tracking
- **Diagnostics**: System health checks

### 2. Upstream References (`external/`)

Cloned repositories for reference and integration:
- **atlas/**: RealDeviceMap Docker stack
- **emagisk/**: Magisk module template with ATV services
- **aegis/**: Enhanced monitoring stack
- **rotom/**: MITM connector (Node.js)

### 3. Test Suite (`tests/`)

Automated tests for:
- ADB parsing and device selection
- Root result interpretation
- Configuration loading
- Health state evaluation
- Command generation

## What This Repository Is NOT

- ❌ Source code for Atlas Android application
- ❌ Zygisk injection module implementation
- ❌ LSPosed hook definitions
- ❌ Frida instrumentation scripts
- ❌ Game reverse engineering tools

## Integration Model

```
┌─────────────────────┐
│  Host Tooling       │ ← This repository
│  (android_lab)      │
└──────────┬──────────┘
           │ ADB
           ▼
┌─────────────────────┐
│  Android Device     │
│  ┌───────────────┐  │
│  │ Atlas APK (🔒)│  │ ← Proprietary
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ Zygisk (🔒)   │  │ ← Proprietary
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ Pokémon GO    │  │
│  └───────────────┘  │
└─────────────────────┘
```

## File Structure

```
/workspace/
├── android_lab/           # Python package
│   ├── __init__.py
│   ├── adb.py            # ADB communication layer
│   ├── cli.py            # CLI entry points
│   ├── config.py         # Configuration loader
│   ├── default.yaml      # Default settings
│   ├── diagnostics.py    # Health checks
│   ├── emulator.py       # Emulator management
│   ├── health.py         # State machine
│   ├── location.py       # Location services
│   ├── root.py           # Root detection
│   └── ...               # Other modules
│
├── tests/
│   └── unit/             # Unit tests
│
├── external/             # Upstream references
│   ├── atlas/
│   ├── emagisk/
│   ├── aegis/
│   └── rotom/
│
├── docs/                 # Documentation
│   ├── CURRENT_ARCHITECTURE.md
│   ├── POGOMOD_COMPONENT_MATRIX.md
│   ├── UPSTREAM_ARCHITECTURE.md
│   └── DEPLOYMENT_ARCHITECTURE.md
│
├── scripts/mumu/         # MuMu helpers
├── tools/                # Build/deploy scripts
├── config/               # Configuration templates
│
├── pyproject.toml        # Python project config
├── uv.lock              # Dependency lockfile
├── README.md            # Project overview
└── START-HERE.md        # Getting started guide
```

## Entry Points

### CLI Commands

```bash
# Via uv
uv run android-lab --help

# Direct Python
python -m android_lab.cli --help
```

### Python API

```python
from android_lab import adb, root, config

# List devices
devices = adb.list_devices()

# Check root status
status = root.check_root("emulator-5554")

# Load configuration
cfg = config.load()
```

## Build & Test

```bash
# Sync dependencies
uv sync

# Run tests
uv run pytest

# Compile check
python -m compileall android_lab

# Verify project
tools/windows/verify-project.ps1  # Windows
```

## Configuration

Edit `config/default.yaml` or create environment-specific overrides:

```yaml
adb:
  path: /usr/bin/adb
  timeout: 30
  
device:
  serial: emulator-5554
  
mumu:
  path: C:/Program Files/Nemu/MuMuEmulator/v12/shell/NemuConsole.exe
```

## Next Steps

1. **Review** `POGOMOD_COMPONENT_MATRIX.md` for component status
2. **Study** `UPSTREAM_ARCHITECTURE.md` for cloned repos
3. **Read** `DEPLOYMENT_ARCHITECTURE.md` for deployment flow
4. **Obtain** proprietary components from Pokemod distribution
5. **Configure** backend infrastructure via Docker Compose
6. **Deploy** to test device for runtime validation
