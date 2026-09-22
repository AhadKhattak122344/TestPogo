# Pokemod Component Matrix

## Component Availability Analysis

| Component | Status | Source Location | Buildable | Notes |
|-----------|--------|-----------------|-----------|-------|
| **Host Controller (Python)** | ✅ IMPLEMENTED | `/workspace/android_lab/` | YES | ADB, root detection, device management |
| **Android Controller APK** | ❌ MISSING | N/A | NO | Proprietary - must download pre-built |
| **Native Injection Module** | ❌ MISSING | N/A | NO | Proprietary Zygisk/LSPosed module |
| **Zygisk Runtime** | ⚠️ UPSTREAM | External projects | PARTIAL | Use NeoZygisk/KernelSU plugins |
| **Magisk Module (eMagisk)** | ✅ AVAILABLE | `/workspace/upstream/eMagisk/` | YES | System utilities module |
| **Atlas Backend (RDM)** | ✅ AVAILABLE | `/workspace/upstream/Atlas-All-In-One/` | YES | Docker Compose stack |
| **Aegis Backend** | ✅ AVAILABLE | `/workspace/upstream/Aegis-All-In-One/` | YES | Alternative Docker stack |
| **Rotom MITM** | ✅ AVAILABLE | `/workspace/upstream/Rotom/` | YES | Node.js MITM connector |
| **Overlay Service** | ❌ MISSING | N/A | NO | Part of proprietary controller |
| **Joystick Service** | ❌ MISSING | N/A | NO | Part of proprietary controller |
| **Frida Scripts** | ❌ MISSING | N/A | NO | Must be created/reverse engineered |
| **RPC Protocol** | ⚠️ PARTIAL | Defined in android_lab | PARTIAL | Host side ready, Android side missing |

## Required Actions

### 1. Download Pre-built Components

Must obtain from official Pokemod sources:
- Atlas Controller APK
- Pokemod Zygisk module
- LSPosed module for Pokemod
- Any required Frida scripts

### 2. Build Available Components

```bash
# eMagisk module
cd upstream/eMagisk
./build.sh

# Rotom MITM
cd upstream/Rotom
npm ci && npm run build

# Atlas/Aegis stacks
docker-compose up -d
```

### 3. Implement Missing Host Tooling

- [x] ADB abstraction layer
- [x] Root detection logic
- [ ] APK deployment automation
- [ ] Module installation scripts
- [ ] Service management commands
- [ ] Configuration file generation

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HOST SYSTEM                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │ android_lab │  │ Deploy Scripts│  │ Config Generator │    │
│  │  (Python)   │  │ (PowerShell) │  │    (YAML/JSON)  │    │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘    │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │                                   │
│                          ▼                                   │
│                  ┌───────────────┐                          │
│                  │     ADB       │                          │
│                  └───────┬───────┘                          │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   ANDROID DEVICE                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   Magisk    │  │  eMagisk     │  │  Pokemod Module │    │
│  │  (Root)     │  │  (Utilities) │  │   (Injection)   │    │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘    │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │                                   │
│                          ▼                                   │
│                 ┌────────────────┐                           │
│                 │ Atlas Controller│                           │
│                 │      (APK)      │                           │
│                 └────────┬────────┘                           │
│                          │                                    │
│                          ▼                                    │
│                 ┌────────────────┐                            │
│                 │  Pokémon GO    │                            │
│                 │    (Target)    │                            │
│                 └────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## Service Dependencies

```
Pokémon GO
    ├── Requires: Pokemod Injection Module (Zygisk/LSPosed)
    │       └── Requires: Zygisk Runtime
    │           └── Requires: Magisk/KernelSU Root
    │
    ├── Requires: Atlas Controller APK
    │       ├── Requires: Overlay Permission
    │       ├── Requires: Accessibility Service (optional)
    │       └── Connects to: RDM/Aegis Backend
    │
    └── Requires: Proper configuration
            ├── Device endpoint secret
            ├── RDM server URL
            └── Auth bearer token
```

## Testing Strategy

Since core components are proprietary:

1. **Test host tooling with mocks** - Verify ADB commands, config generation
2. **Test deployment scripts** - Ensure files push to correct locations
3. **Test service commands** - Validate am startservice syntax
4. **Runtime validation later** - Actual injection requires live device

## Known Interfaces

From Atlas APK analysis (expected):

- **Service**: `com.pokemod.atlas.services.MappingService`
- **Configuration**: Stored in app preferences or config file
- **Communication**: Likely local TCP or broadcast intents
- **Overlay**: Standard Android overlay service

## Next Implementation Priorities

1. Create deployment script structure for pre-built components
2. Implement service management commands (start/stop/status)
3. Build configuration file generator for Atlas
4. Add health check endpoints for monitoring
5. Create mock implementations for testing without device
